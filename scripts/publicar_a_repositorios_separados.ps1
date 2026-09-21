<#
.SYNOPSIS
    Sincroniza y publica los modulos del Monorepo en los 3 repositorios separados de GitHub.

.DESCRIPTION
    Toma los cambios de las carpetas backend, frontend y machine_learning del proyecto
    principal y los empuja a sus respectivos repositorios remotos en GitHub de forma
    limpia y aislada, sin ensuciar el espacio de trabajo local.

.PARAMETER Mensaje
    Mensaje descriptivo para los commits en los repositorios separados.

.PARAMETER SoloBackend
    Sincroniza unicamente el repositorio carbot-backend.

.PARAMETER SoloFrontend
    Sincroniza unicamente el repositorio carbot-frontend.

.PARAMETER SoloML
    Sincroniza unicamente el repositorio carbot-machine-learning.

.EXAMPLE
    .\scripts\publicar_a_repositorios_separados.ps1 -Mensaje "feat: actualizacion de diagnosticos"
#>

param(
    [string]$Mensaje = "sync: sincronizacion desde monorepo principal $(Get-Date -Format 'yyyy-MM-dd HH:mm')",
    [switch]$SoloBackend,
    [switch]$SoloFrontend,
    [switch]$SoloML,
    [switch]$HaciaMain
)

$ErrorActionPreference = "Continue"

$projectRoot = Split-Path -Parent $PSScriptRoot
$sincronizarTodos = (-not $SoloBackend) -and (-not $SoloFrontend) -and (-not $SoloML)

$repos = @(
    @{
        Nombre = "carbot-backend"
        Url = "https://github.com/JUANLCHUMBE5/carbot-backend.git"
        Activo = ($sincronizarTodos -or $SoloBackend)
        Origen = (Join-Path $projectRoot "backend")
        Tipo = "backend"
        RamaDev = "dev-backend"
    },
    @{
        Nombre = "carbot-frontend"
        Url = "https://github.com/JUANLCHUMBE5/carbot-frontend.git"
        Activo = ($sincronizarTodos -or $SoloFrontend)
        Origen = (Join-Path $projectRoot "frontend")
        Tipo = "frontend"
        RamaDev = "dev-frontend"
    },
    @{
        Nombre = "carbot-machine-learning"
        Url = "https://github.com/JUANLCHUMBE5/carbot-machine-learning.git"
        Activo = ($sincronizarTodos -or $SoloML)
        Origen = $projectRoot
        Tipo = "ml"
        RamaDev = "dev-machine-learning"
    }
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Sincronizador de Repositorios Separados CarBot" -ForegroundColor Cyan
Write-Host " Mensaje de commit: '$Mensaje'" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$tempBase = Join-Path $env:TEMP ("carbot_sync_" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempBase -Force | Out-Null

try {
    foreach ($r in $repos) {
        if (-not $r.Activo) { continue }

        $nombre = $r.Nombre
        $url = $r.Url
        $cloneDir = Join-Path $tempBase $nombre

        $targetBranch = if ($HaciaMain) { "main" } else { $r.RamaDev }

        Write-Host "`n--> Procesando [$nombre] (Rama: $targetBranch)..." -ForegroundColor Green
        Write-Host "    Clonando rama '$targetBranch' desde GitHub..." -ForegroundColor Gray
        & git clone --branch $targetBranch --depth 1 --quiet $url $cloneDir
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "No se pudo clonar la rama $targetBranch de $url. Verifica tu conexion a internet o permisos de GitHub."
            continue
        }

        Write-Host "    Sincronizando archivos..." -ForegroundColor Gray

        if ($r.Tipo -eq "backend") {
            robocopy (Join-Path $projectRoot "backend") $cloneDir /E /PURGE `
                /XD ".git" "__pycache__" ".pytest_cache" ".ruff_cache" ".venv" "node_modules" `
                /XF "*.pyc" "*.log" ".DS_Store" /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
        }
        elseif ($r.Tipo -eq "frontend") {
            robocopy (Join-Path $projectRoot "frontend") $cloneDir /E /PURGE `
                /XD ".git" "node_modules" "dist" ".vite" `
                /XF "*.log" ".DS_Store" /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
        }
        elseif ($r.Tipo -eq "ml") {
            $dirsML = @("machine_learning", "docs")
            foreach ($d in $dirsML) {
                $src = Join-Path $projectRoot $d
                $dst = Join-Path $cloneDir $d
                if (Test-Path $src) {
                    robocopy $src $dst /E /PURGE `
                        /XD ".git" "__pycache__" ".pytest_cache" ".ruff_cache" ".venv" "sandbox_rag_experimental" "experimentos" "raw" "nhtsa_complaints" "nhtsa_recalls" `
                        /XF "*.pyc" "*.log" "*.pkl" "*.index" "*.zip" "*.tar.gz" "*.jsonl" `
                        /MAX:50000000 `
                        /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
                }
            }
            $mlReq = Join-Path $projectRoot "machine_learning\requirements.txt"
            if (Test-Path $mlReq) { Copy-Item $mlReq (Join-Path $cloneDir "requirements.txt") -Force }
            $mlDock = Join-Path $projectRoot "machine_learning\Dockerfile"
            if (Test-Path $mlDock) { Copy-Item $mlDock (Join-Path $cloneDir "Dockerfile") -Force }
        }

        # Verificar si hay cambios en git
        Push-Location $cloneDir
        try {
            $status = & git status --porcelain
            if ([string]::IsNullOrWhiteSpace($status)) {
                Write-Host "    [AL DIA] $nombre ya tiene todos los archivos actualizados en '$targetBranch'." -ForegroundColor Cyan
            }
            else {
                Write-Host "    Cambios detectados. Creando commit y enviando a GitHub ($targetBranch)..." -ForegroundColor Yellow
                & git add -A
                & git commit -m "$Mensaje" | Out-Null
                & git push origin $targetBranch
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "    [OK] $nombre actualizado con exito en GitHub en la rama '$targetBranch'!" -ForegroundColor Green
                } else {
                    Write-Warning "    Error al hacer git push a $nombre ($targetBranch)."
                }
            }
        }
        finally {
            Pop-Location
        }
    }
}
finally {
    if (Test-Path $tempBase) {
        Remove-Item -Path $tempBase -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " Proceso de sincronizacion finalizado." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
