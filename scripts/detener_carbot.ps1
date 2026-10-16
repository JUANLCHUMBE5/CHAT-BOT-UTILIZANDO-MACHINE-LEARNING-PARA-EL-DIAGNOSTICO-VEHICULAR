Write-Host "Deteniendo servicios de CarBot..." -ForegroundColor Yellow

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$escapedRepoRoot = [Regex]::Escape($repoRoot)

function Test-EsProcesoCarBot($proc) {
    if ($null -eq $proc) { return $false }
    $cmd = [string]$proc.CommandLine
    $exe = [string]$proc.ExecutablePath
    return ($cmd -match $escapedRepoRoot) -or ($exe -match $escapedRepoRoot)
}

# Detener Uvicorn / FastAPI Backend perteneciente a CarBot
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
        (Test-EsProcesoCarBot $_) -and
        ($_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*main:app*")
    } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

# Liberar puertos 8000 y 5173 solo si el proceso propietario pertenece a CarBot
Get-NetTCPConnection -LocalPort 8000, 5173 -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object {
        $owner = Get-CimInstance Win32_Process -Filter "ProcessId = $($_.OwningProcess)" -ErrorAction SilentlyContinue
        if (Test-EsProcesoCarBot $owner) {
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }

# Detener Worker de Colas de CarBot
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
        (Test-EsProcesoCarBot $_) -and
        ($_.CommandLine -like "*src.application.jobs.worker*")
    } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

# Detener Vite / Panel Web de CarBot
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
        (Test-EsProcesoCarBot $_) -and
        ($_.CommandLine -like "*vite*" -or $_.CommandLine -like "*carbot-frontend*")
    } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

# Detener Ngrok iniciado hacia el puerto 8000 de CarBot
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -match "^ngrok(\.exe)?$" -and
        ($_.CommandLine -like "*8000*" -or (Test-EsProcesoCarBot $_))
    } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

# Cerrar ventanas de consola de CarBot
Get-Process powershell -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowTitle -like "CarBot - *" } |
    ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }

Write-Host "[OK] Todos los servicios y ventanas de CarBot han sido detenidos correctamente." -ForegroundColor Green
