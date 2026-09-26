<# Crea una copia local separada. No borra, no hace commit y no publica. #>
param([string]$Destino = "")
$ErrorActionPreference = 'Stop'
$origen = Split-Path -Parent $PSScriptRoot
if (-not $Destino) { $Destino = Join-Path $origen 'repositorios_separados' }
$Destino = [IO.Path]::GetFullPath($Destino)
if (Test-Path -LiteralPath $Destino) { throw "El destino ya existe; no se sobrescribe: $Destino" }
$repos = @('carbot-backend', 'carbot-frontend', 'carbot-machine-learning')
foreach ($repo in $repos) { New-Item -ItemType Directory -Path (Join-Path $Destino $repo) | Out-Null }

function Copiar-Archivo([string]$Relativo, [string]$Repo, [string]$RutaDestino) {
    $fuente = Join-Path $origen $Relativo
    if (-not (Test-Path -LiteralPath $fuente -PathType Leaf)) { return }
    $objetivo = Join-Path (Join-Path $Destino $Repo) $RutaDestino
    New-Item -ItemType Directory -Path (Split-Path -Parent $objetivo) -Force | Out-Null
    Copy-Item -LiteralPath $fuente -Destination $objetivo
}

$archivos = & git -C $origen ls-files --cached --others --exclude-standard
if ($LASTEXITCODE -ne 0) { throw 'No se pudo enumerar el origen Git.' }
foreach ($archivo in ($archivos | Sort-Object -Unique)) {
    if ($archivo -match '(^|/)(node_modules|__pycache__|dist|\.venv|\.git)/|\.log$|\.pyc$|tracker_diagnosticos|evidencias_evaluacion') { continue }
    if ($archivo -match '(^|/)\.env($|\.)' -and $archivo -notmatch '\.env\.example$') { continue }
    if ($archivo.StartsWith('frontend/')) {
        Copiar-Archivo $archivo 'carbot-frontend' $archivo.Substring(9)
    } elseif ($archivo.StartsWith('machine_learning/')) {
        Copiar-Archivo $archivo 'carbot-machine-learning' $archivo
    } elseif ($archivo -match '^(backend/|infrastructure/|docs/)') {
        Copiar-Archivo $archivo 'carbot-backend' $archivo
    } elseif ($archivo.StartsWith('scripts/') -and $archivo -notmatch 'publicar_a_repositorios|preparar_tres_repos') {
        # Automatizaciones históricas: se conservan en ML, sin ejecutarlas.
        Copiar-Archivo $archivo 'carbot-machine-learning' $archivo
    }
}
foreach ($repo in $repos) {
    foreach ($comun in @('.editorconfig', '.gitattributes', '.gitignore', 'SECURITY.md', 'CONTRIBUTING.md')) {
        Copiar-Archivo $comun $repo $comun
    }
}
Copiar-Archivo '.env.example' 'carbot-backend' '.env.example'
Copiar-Archivo 'README.md' 'carbot-backend' 'README.md'
Copiar-Archivo 'machine_learning/README.md' 'carbot-machine-learning' 'README.md'

# Artefactos necesarios para inferencia: copia local explícita, permanecen ignorados por Git.
$artefactos = @(
    'machine_learning/models/c1_fase10_final',
    'machine_learning/manuals'
)
foreach ($dir in $artefactos) {
    Get-ChildItem -LiteralPath (Join-Path $origen $dir) -File -Recurse |
        Where-Object { $_.Extension -in '.pkl', '.index' -and $_.FullName -notmatch 'sandbox|experimentos|__pycache__' } |
        ForEach-Object {
            $rel = $_.FullName.Substring($origen.Length + 1)
            Copiar-Archivo $rel 'carbot-machine-learning' $rel
        }
}
foreach ($repo in $repos) {
    & git -C (Join-Path $Destino $repo) init -b main --quiet
    if ($LASTEXITCODE -ne 0) { throw "No se pudo inicializar $repo" }
}
Write-Output "Tres repositorios locales creados en $Destino. Sin remotos, commits ni push."
Write-Output 'Aplicar las adaptaciones de rutas y despliegue antes de usarlos; ver GUIA_LOCAL.md.'
