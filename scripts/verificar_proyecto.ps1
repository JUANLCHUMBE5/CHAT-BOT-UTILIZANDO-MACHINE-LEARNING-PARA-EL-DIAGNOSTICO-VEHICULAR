$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$ruffLocal = Join-Path $projectRoot ".venv\Scripts\ruff.exe"
$backend = Join-Path $projectRoot "backend"
$frontend = Join-Path $projectRoot "frontend"

if (-not (Test-Path -LiteralPath $python)) {
    throw "No existe .venv. Cree el entorno virtual e instale backend/requirements-dev.txt."
}
$ruffCommand = if (Test-Path -LiteralPath $ruffLocal) {
    $ruffLocal
} else {
    (Get-Command ruff -ErrorAction SilentlyContinue).Source
}
if (-not $ruffCommand) {
    throw "Ruff no está instalado. Ejecute: pip install -r backend/requirements-dev.txt"
}

Push-Location $backend
try {
    & $ruffCommand check src tests main.py locustfile.py scripts ..\machine_learning\training ..\infrastructure\database\postgresql
    & $python -m pytest -q
}
finally {
    Pop-Location
}

Push-Location $frontend
try {
    npm run lint
    npm run build
}
finally {
    Pop-Location
}

Write-Host "Verificación completa: backend y frontend correctos." -ForegroundColor Green
