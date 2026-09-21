$backendPython = "C:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING\.venv\Scripts\python.exe"
$backendRoot = "C:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING\backend"

$windowCommand = "`$Host.UI.RawUI.WindowTitle = 'CarBot - Worker de Colas'; `$env:QUEUE_EMBEDDED_WORKER='false'; & '$backendPython' -m src.application.jobs.worker"
Start-Process -FilePath "powershell.exe" `
    -ArgumentList @("-NoExit", "-Command", $windowCommand) `
    -WorkingDirectory $backendRoot | Out-Null

Write-Host "[OK] Worker iniciado."
