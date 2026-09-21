param(
    [switch]$SinNgrok,
    [switch]$ReiniciarWorker
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$backendRoot = Join-Path $projectRoot "backend"
$frontendRoot = Join-Path $projectRoot "frontend"
$ngrokDomain = "lustrous-appear-traps.ngrok-free.dev"

function Test-ListeningPort {
    param([int]$Port)
    return $null -ne (
        Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    )
}

function Start-CarBotWindow {
    param(
        [string]$Title,
        [string]$WorkingDirectory,
        [string]$Command
    )

    $windowCommand = "`$Host.UI.RawUI.WindowTitle = '$Title'; Set-Location '$WorkingDirectory'; $Command"
    Start-Process -FilePath "powershell.exe" `
        -ArgumentList @("-NoExit", "-Command", $windowCommand) `
        -WorkingDirectory $WorkingDirectory | Out-Null
}

if (-not (Test-Path -LiteralPath $backendPython)) {
    throw "No se encontró el entorno Python: $backendPython"
}

if (-not (Test-Path -LiteralPath (Join-Path $frontendRoot "package.json"))) {
    throw "No se encontró el panel web en: $frontendRoot"
}

$viteBin = Join-Path $frontendRoot "node_modules\.bin\vite.cmd"
if (-not (Test-Path -LiteralPath $viteBin)) {
    Write-Host "[INFO] Instalando dependencias del panel web (npm ci)..." -ForegroundColor Cyan
    Push-Location $frontendRoot
    try {
        & npm ci
    }
    finally {
        Pop-Location
    }
}

$postgres = Get-Service -Name "postgresql-x64-17" -ErrorAction SilentlyContinue
if ($postgres -and $postgres.Status -ne "Running") {
    try {
        Start-Service -Name "postgresql-x64-17"
        Write-Host "[OK] PostgreSQL 17 iniciado." -ForegroundColor Green
    }
    catch {
        Write-Warning "No se pudo iniciar PostgreSQL 17. Abre PowerShell como administrador y vuelve a ejecutar."
    }
}
elseif ($postgres) {
    Write-Host "[OK] PostgreSQL 17 ya estaba activo." -ForegroundColor Green
}
else {
    Write-Warning "No se encontró el servicio postgresql-x64-17."
}

if (-not (Test-ListeningPort -Port 8000)) {
    $backendCommand = "`$env:QUEUE_EMBEDDED_WORKER='false'; & '$backendPython' -m alembic upgrade head; & '$backendPython' -m uvicorn main:app --reload --port 8000"
    Start-CarBotWindow -Title "CarBot - Backend" -WorkingDirectory $backendRoot -Command $backendCommand
    Write-Host "[OK] Iniciando chatbot y API..." -ForegroundColor Green
}
else {
    Write-Host "[OK] Backend ya estaba activo en el puerto 8000." -ForegroundColor Green
}

if ($ReiniciarWorker) {
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*src.application.jobs.worker*" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Milliseconds 500
    Write-Host "[OK] Worker anterior detenido para reinicio." -ForegroundColor Yellow
}

$workerActivo = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*src.application.jobs.worker*" } |
    Select-Object -First 1

if (-not $workerActivo) {
    $workerCommand = "`$env:QUEUE_EMBEDDED_WORKER='false'; & '$backendPython' -m src.application.jobs.worker"
    Start-CarBotWindow -Title "CarBot - Worker de Colas" -WorkingDirectory $backendRoot -Command $workerCommand
    Write-Host "[OK] Iniciando worker de colas y reintentos..." -ForegroundColor Green
}
else {
    Write-Host "[OK] Worker de colas ya estaba activo." -ForegroundColor Green
}

if (-not (Test-ListeningPort -Port 5173)) {
    Start-CarBotWindow -Title "CarBot - Panel Web" -WorkingDirectory $frontendRoot -Command "npm run dev"
    Write-Host "[OK] Iniciando panel web..." -ForegroundColor Green
}
else {
    Write-Host "[OK] Panel ya estaba activo en el puerto 5173." -ForegroundColor Green
}

if (-not $SinNgrok) {
    $ngrokActivo = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -match "^ngrok(\.exe)?$" -and
            $_.CommandLine -like "*$ngrokDomain*" -and
            $_.CommandLine -match "\b8000\b"
        } |
        Select-Object -First 1

    if (-not $ngrokActivo) {
        $ngrokCommand = "ngrok http --domain=$ngrokDomain 8000"
        Start-CarBotWindow -Title "CarBot - Ngrok WhatsApp" -WorkingDirectory $projectRoot -Command $ngrokCommand
        Write-Host "[OK] Iniciando conexión pública de WhatsApp..." -ForegroundColor Green
    }
    else {
        Write-Host "[OK] Ngrok ya estaba conectado." -ForegroundColor Green
    }
}

$backendReady = $false
$frontendReady = $false
$maxAttempts = 60
Write-Host -NoNewline "Esperando que los servicios respondan"
for ($attempt = 0; $attempt -lt $maxAttempts; $attempt++) {
    Start-Sleep -Milliseconds 500
    Write-Host -NoNewline "."
    $backendReady = Test-ListeningPort -Port 8000
    $frontendReady = Test-ListeningPort -Port 5173
    if ($backendReady -and $frontendReady) {
        break
    }
}
Write-Host ""

if ($backendReady -and $frontendReady) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host " [OK] CarBot está corriendo al 100%!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host " Panel Web:   http://localhost:5173" -ForegroundColor Cyan
    Write-Host " API Docs:    http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host " Worker:      Activo en segundo plano" -ForegroundColor Cyan
    if (-not $SinNgrok) {
        Write-Host " WhatsApp:    https://$ngrokDomain" -ForegroundColor Cyan
    }
    Write-Host ""
    Write-Host "No cierres las ventanas de Backend, Worker, Panel Web y Ngrok mientras uses CarBot." -ForegroundColor Yellow
}
else {
    Write-Host ""
    Write-Warning "Estado detallado de los servicios:"
    if ($backendReady) {
        Write-Host " [OK] Backend API (Puerto 8000): Activo" -ForegroundColor Green
    } else {
        Write-Host " [FALLO / ESPERANDO] Backend API (Puerto 8000): No respondió a tiempo." -ForegroundColor Red
    }
    if ($frontendReady) {
        Write-Host " [OK] Panel Web (Puerto 5173): Activo" -ForegroundColor Green
    } else {
        Write-Host " [FALLO / ESPERANDO] Panel Web (Puerto 5173): No respondió a tiempo." -ForegroundColor Red
    }
    Write-Warning "Revisa la ventana correspondiente para ver detalles del error."
}
