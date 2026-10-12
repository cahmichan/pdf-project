#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use std::{io::{BufRead, BufReader, Write}, process::{Child, ChildStdin, Command, Stdio}, sync::{Arc, Mutex, mpsc}, time::Duration};
use serde_json::Value;
use tauri::{Emitter, Manager};

fn allow_session_assets(app: &tauri::AppHandle, value: &Value) -> Result<(),String> {
    let sessions = app.path().app_data_dir().map_err(|e|e.to_string())?.join("sessions");
    fn visit(app: &tauri::AppHandle, root: &std::path::Path, value: &Value) -> Result<(),String> {
        match value {
            Value::Object(object) => {
                if let Some(path) = object.get("path").and_then(Value::as_str) {
                    let path = std::path::Path::new(path);
                    let image_or_pdf = matches!(path.extension().and_then(|s|s.to_str()),Some("pdf"|"png"|"jpg"|"jpeg"));
                    if path.is_absolute() && path.starts_with(root) && !path.components().any(|p|matches!(p,std::path::Component::ParentDir)) && image_or_pdf && path.is_file() {
                        // Windows package virtualization can redirect a newly created child
                        // outside the canonical directory originally granted at startup.
                        app.asset_protocol_scope().allow_file(path).map_err(|e|e.to_string())?;
                    }
                }
                for item in object.values() { if item.is_object() || item.is_array() { visit(app,root,item)?; } }
            }
            Value::Array(array) => { for item in array { visit(app,root,item)?; } }
            _ => {}
        }
        Ok(())
    }
    visit(app,&sessions,value)
}

struct Worker { child: Arc<Mutex<Child>>, input: ChildStdin, output: mpsc::Receiver<Result<String,String>> }
fn stop_worker(child: &mut Child) -> Result<(),String> {
    if child.try_wait().map_err(|e| e.to_string())?.is_some() { return Ok(()); }
    // PyInstaller onefile uses a bootloader and a child process. Stop our own tree.
    #[cfg(windows)] {
        use std::os::windows::process::CommandExt;
        let system = std::env::var_os("SystemRoot").ok_or("Windows system directory unavailable")?;
        let result = Command::new(std::path::Path::new(&system).join("System32/taskkill.exe"))
            .args(["/PID", &child.id().to_string(), "/T", "/F"])
            .creation_flags(0x08000000).stdout(Stdio::null()).stderr(Stdio::null()).status();
        if !matches!(result, Ok(status) if status.success()) { let _ = child.kill(); }
    }
    #[cfg(not(windows))] { let _ = child.kill(); }
    let _ = child.wait();
    Ok(())
}
impl Drop for Worker { fn drop(&mut self) { if let Ok(mut child) = self.child.lock() { let _ = stop_worker(&mut child); } } }
#[derive(Clone)]
struct Backend { worker: Arc<Mutex<Option<Worker>>>, control: Arc<Mutex<Option<Arc<Mutex<Child>>>>> }

fn start_worker(app: &tauri::AppHandle) -> Result<Worker,String> {
    let data = app.path().app_data_dir().map_err(|e| e.to_string())?;
    std::fs::create_dir_all(&data).map_err(|e| e.to_string())?;
    let mut command;
    if cfg!(debug_assertions) {
        let project = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).parent().unwrap();
        command = Command::new(project.join(".venv/Scripts/python.exe"));
        command.arg("-u").arg(project.join("worker/main.py"));
    } else {
        let executable = std::env::current_exe().map_err(|e| e.to_string())?;
        command = Command::new(executable.parent().unwrap().join("pdf-worker.exe"));
    }
    command.arg("--data-dir").arg(data).stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::null());
    #[cfg(windows)] { use std::os::windows::process::CommandExt; command.creation_flags(0x08000000); }
    let mut child = command.spawn().map_err(|e| format!("Cannot start the PDF worker: {e}"))?;
    let input = child.stdin.take().ok_or("Worker input unavailable")?;
    let mut reader = BufReader::new(child.stdout.take().ok_or("Worker output unavailable")?);
    let (sender, output) = mpsc::channel();
    std::thread::spawn(move || loop {
        let mut line = String::new();
        let result = match reader.read_line(&mut line) {
            Ok(0) => Err("PDF worker stopped. Sessions remain recoverable.".into()),
            Ok(_) => Ok(line),
            Err(error) => Err(error.to_string()),
        };
        let finished = result.is_err();
        if sender.send(result).is_err() || finished { break; }
    });
    Ok(Worker {child: Arc::new(Mutex::new(child)), input, output})
}

#[tauri::command]
async fn pdf_cancel(state: tauri::State<'_,Backend>) -> Result<(),String> {
    let child = state.control.lock().map_err(|_| "Worker control unavailable")?.clone();
    if let Some(child) = child { let mut process = child.lock().map_err(|_| "Worker process unavailable")?; stop_worker(&mut process)?; }
    Ok(())
}

#[tauri::command]
async fn pdf_command(app: tauri::AppHandle, state: tauri::State<'_,Backend>, request: Value) -> Result<Value,String> {
    if request["command"] == "native_paths" && std::env::var_os("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS").is_some() {
        let data = app.path().app_data_dir().map_err(|e| e.to_string())?;
        let path = request["args"]["path"].as_str().unwrap_or("");
        let scope = app.asset_protocol_scope();
        return Ok(serde_json::json!({"data":data,"canonical_data":std::fs::canonicalize(&data).ok(),"path":path,"canonical_path":std::fs::canonicalize(path).ok(),"patterns":scope.allowed_patterns().iter().map(|p|p.as_str().to_string()).collect::<Vec<_>>(),"path_allowed":scope.is_allowed(path),"file_open":std::fs::File::open(path).map(|_|"ok".to_string()).unwrap_or_else(|e|e.to_string())}));
    }
    if request["command"] == "startup" {
        let path = std::env::args().skip(1).find(|argument| argument.to_lowercase().ends_with(".pdf"));
        return Ok(serde_json::to_value(path).map_err(|e| e.to_string())?);
    }
    let backend = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        let mut guard = backend.worker.lock().map_err(|_| "Worker state unavailable")?;
        if guard.is_none() {
            let worker = start_worker(&app)?;
            *backend.control.lock().map_err(|_| "Worker control unavailable")? = Some(worker.child.clone());
            *guard = Some(worker);
        }
        let worker = guard.as_mut().unwrap();
        let line = serde_json::to_string(&request).map_err(|e| e.to_string())?;
        if let Err(e) = writeln!(worker.input, "{line}").and_then(|_| worker.input.flush()) { *guard = None; return Err(format!("Worker disconnected: {e}")); }
        loop {
            let response = match worker.output.recv_timeout(Duration::from_secs(300)) {
                Ok(Ok(line)) => line,
                Ok(Err(error)) => { *guard = None; return Err(error); },
                Err(_) => { *guard = None; return Err("Operation stopped after five minutes without a worker response. Reopen the recovery session before retrying.".into()); },
            };
            let value: Value = match serde_json::from_str(&response) {
                Ok(value) => value,
                Err(error) => { *guard = None; return Err(format!("Invalid worker response: {error}. Retry to reconnect.")); },
            };
            if value["event"] == "progress" { let _ = app.emit("pdf-progress", &value); continue; }
            if value["ok"] == true { let result=value["result"].clone();allow_session_assets(&app,&result)?;return Ok(result); }
            return Err(value["error"]["message"].as_str().unwrap_or("PDF operation failed").to_string());
        }
    }).await.map_err(|e| e.to_string())?
}

fn main() {
    tauri::Builder::default().plugin(tauri_plugin_dialog::init()).plugin(tauri_plugin_opener::init())
        .manage(Backend { worker: Arc::new(Mutex::new(None)), control: Arc::new(Mutex::new(None)) })
        .setup(|app| { let data = app.path().app_data_dir()?; std::fs::create_dir_all(&data)?; app.asset_protocol_scope().allow_directory(data, true)?; Ok(()) })
        .invoke_handler(tauri::generate_handler![pdf_command, pdf_cancel])
        .run(tauri::generate_context!()).expect("Folio could not start");
}
