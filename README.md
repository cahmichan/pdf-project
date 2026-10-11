# Folio - Personal PDF

Free local Windows PDF reader/editor under development. Follow [the plan](PERSONAL_PDF_APP_PLAN.md), [progress](docs/PROGRESS.md), and [feature status](docs/FEATURES.md).

## Run from source

Requirements: Windows x64, Node.js, Rust with Visual Studio C++ build tools, Python 3.12+, and Microsoft Edge WebView2 runtime.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r worker/requirements.lock.txt
npm.cmd ci
.\.venv\Scripts\python.exe scripts/prepare_assets.py
```

Package the worker once before the first desktop development launch:

```powershell
$ocrDataArgument = (Join-Path (Get-Location) 'tools\tessdata') + ';tessdata'
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --onefile --console --add-data $ocrDataArgument --name pdf-worker --distpath src-tauri/binaries --workpath artifacts/pyinstaller --specpath artifacts worker/main.py
Copy-Item src-tauri/binaries/pdf-worker.exe src-tauri/binaries/pdf-worker-x86_64-pc-windows-msvc.exe
npm.cmd run desktop
```

## Verify

```powershell
npm.cmd run test:worker
.\.venv\Scripts\python.exe scripts/create_fixtures.py
```

Browser UI tests use a development-only loopback bridge. Run `npx.cmd playwright test`; the test runner starts the loopback bridge and Vite automatically. They currently use installed Microsoft Edge. This bridge is not part of the desktop release.

## Build an installer

```powershell
npm.cmd run package
```

The current per-user NSIS installer targets an existing WebView2 runtime. It does not require developer Node/Python/Rust installations at runtime. Native acceptance and optional dependency setup are tracked separately. See the release receipt before relying on a build.

## File safety

The app edits private working copies and saves separate outputs by default. Sessions are recoverable in `%APPDATA%\personal.folio.pdf\sessions` (the exact Tauri app-data path may vary). Closing a tab retains recovery files. Source documents, especially signed/encrypted files, are never intentionally replaced by the UI.

Some features have explicit limitations. Read FEATURES.md before treating an export as a faithful conversion or using redaction on an untested document class.

## Licensing

This private application uses the AGPL edition of PyMuPDF/MuPDF. Retain dependency notices and comply with applicable licenses. There are no paid engines or APIs. Local use is the current scope; distribution or network access would require a separate license review.
