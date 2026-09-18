$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$backendRoot = Join-Path $projectRoot "backend"

$workerCommand = "`$Host.UI.RawUI.WindowTitle = 'CarBot - Worker de Colas'; `$env:QUEUE_EMBEDDED_WORKER='false'; & '$backendPython' -m src.application.jobs.worker"
Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-Command", $workerCommand) -WorkingDirectory $backendRoot
Write-Host "[OK] Worker iniciado exitosamente." -ForegroundColor Green
