param(
    [switch]$SinNgrok
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$frontendRoot = Join-Path $projectRoot "web_dashboard"
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

    $windowCommand = "`$Host.UI.RawUI.WindowTitle = '$Title'; $Command"
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
    $backendCommand = "& '$backendPython' -m uvicorn main:app --reload --port 8000"
    Start-CarBotWindow -Title "CarBot - Backend" -WorkingDirectory $projectRoot -Command $backendCommand
    Write-Host "[OK] Iniciando chatbot y API..." -ForegroundColor Green
}
else {
    Write-Host "[OK] Backend ya estaba activo en el puerto 8000." -ForegroundColor Green
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
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Milliseconds 500
    $backendReady = Test-ListeningPort -Port 8000
    $frontendReady = Test-ListeningPort -Port 5173
    if ($backendReady -and $frontendReady) {
        break
    }
}

Write-Host ""
if ($backendReady -and $frontendReady) {
    Write-Host "CarBot está listo." -ForegroundColor Green
    Write-Host "Panel: http://localhost:5173"
    Write-Host "API:   http://localhost:8000/docs"
    Write-Host "No cierres las ventanas de Backend, Panel Web y Ngrok mientras lo uses."
}
else {
    Write-Warning "Algún servicio no terminó de iniciar. Revisa las ventanas abiertas para ver el error."
}
