$projectRoot = Split-Path -Parent $PSScriptRoot
$backendPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$backendRoot = Join-Path $projectRoot "backend"

# 1. Terminar worker anterior
Get-CimInstance Win32_Process | ForEach-Object {
    if ($_.CommandLine -match "src.application.jobs.worker") {
        Write-Host "Terminando worker PID: $($_.ProcessId)"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Seconds 1

# 2. Iniciar nuevo worker
$windowCommand = "`$Host.UI.RawUI.WindowTitle = 'CarBot - Worker de Colas'; `$env:QUEUE_EMBEDDED_WORKER='false'; & '$backendPython' -m src.application.jobs.worker"
Start-Process -FilePath "powershell.exe" `
    -ArgumentList @("-NoExit", "-Command", $windowCommand) `
    -WorkingDirectory $backendRoot | Out-Null

Write-Host "[OK] Worker reiniciado con éxito."
