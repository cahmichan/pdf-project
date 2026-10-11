$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
& $pythonPath -m pytest tests -q
if ($LASTEXITCODE -ne 0) { throw 'Document tests failed.' }
& $pythonPath scripts/create_fixtures.py
if ($LASTEXITCODE -ne 0) { throw 'Fixture preparation failed.' }
& $pythonPath scripts/prepare_assets.py
if ($LASTEXITCODE -ne 0) { throw 'Asset preparation failed.' }
& $pythonPath scripts/collect_licenses.py
if ($LASTEXITCODE -ne 0) { throw 'License collection failed.' }
$ocrDataArgument = (Join-Path $projectRoot 'tools\tessdata') + ';tessdata'
& $pythonPath -m PyInstaller --noconfirm --clean --onefile --console --add-data $ocrDataArgument --name pdf-worker --distpath src-tauri/binaries --workpath artifacts/pyinstaller --specpath artifacts worker/main.py
if ($LASTEXITCODE -ne 0) { throw 'Worker packaging failed.' }
$workerTarget = Join-Path $projectRoot 'src-tauri\binaries\pdf-worker-x86_64-pc-windows-msvc.exe'
Copy-Item -LiteralPath (Join-Path $projectRoot 'src-tauri\binaries\pdf-worker.exe') -Destination $workerTarget -Force
& $pythonPath scripts/smoke_worker.py
if ($LASTEXITCODE -ne 0) { throw 'Packaged worker verification failed.' }
& npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
& npm.cmd run tauri -- build
if ($LASTEXITCODE -ne 0) { throw 'Desktop packaging failed.' }
$releaseVersion = (Get-Content -LiteralPath (Join-Path $projectRoot 'src-tauri\tauri.conf.json') -Raw | ConvertFrom-Json).version
$releaseRoot = Join-Path $projectRoot "artifacts\releases\$releaseVersion"
New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null
$installerName = "Folio_${releaseVersion}_x64-setup.exe"
Copy-Item -LiteralPath (Join-Path $projectRoot "src-tauri\target\release\bundle\nsis\$installerName") -Destination $releaseRoot -Force
& $pythonPath scripts/release_receipt.py $releaseRoot
if ($LASTEXITCODE -ne 0) { throw 'Release receipt failed.' }
Write-Output "Installer saved to $releaseRoot"
