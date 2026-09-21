<#
.SYNOPSIS
Retira solo temporales conocidos y los conserva fuera del repositorio.
.DESCRIPTION
Sin -Aplicar muestra los candidatos. No elimina codigo, dependencias, datos ni modelos.
El manifiesto del respaldo permite localizar cada archivo original.
#>
param([switch]$Aplicar)

$ErrorActionPreference = 'Stop'
$raizCarBot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$prefijoCarBot = $raizCarBot.TrimEnd('\') + '\'
$nombresCache = @('__pycache__', '.pytest_cache', '.ruff_cache')
$candidatos = @()
foreach ($nombre in @('.codex_tmp', 'tmp', '.ruff_cache', '.pytest_cache', '__pycache__')) {
    $ruta = Join-Path $raizCarBot $nombre
    if (Test-Path -LiteralPath $ruta -PathType Container) {
        $candidatos += Get-Item -LiteralPath $ruta -Force
    }
}
foreach ($nombre in @('backend', 'machine_learning', 'scripts')) {
    $candidatos += Get-ChildItem -LiteralPath (Join-Path $raizCarBot $nombre) -Directory -Recurse -Force |
        Where-Object { $_.Name -in $nombresCache }
}
$candidatos = @($candidatos | Sort-Object FullName -Unique)
if (-not $candidatos.Count) { Write-Output 'No hay temporales conocidos que retirar.'; return }

# Verificar todos los objetivos antes de mover el primero. Nunca seguir enlaces.
foreach ($carpeta in $candidatos) {
    $resuelta = (Resolve-Path -LiteralPath $carpeta.FullName).Path
    if (-not $resuelta.StartsWith($prefijoCarBot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Objetivo fuera del repositorio: $resuelta"
    }
    $actual = $carpeta
    while ($actual.FullName -ne $raizCarBot) {
        if ($actual.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "No se permite mover un enlace: $($actual.FullName)"
        }
        $actual = $actual.Parent
    }
    $enlaces = @(Get-ChildItem -LiteralPath $resuelta -Recurse -Force |
        Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
    if ($enlaces.Count) { throw "Hay enlaces dentro de $resuelta" }
    $relativa = $resuelta.Substring($prefijoCarBot.Length).Replace('\', '/')
    $versionados = @(git -C $raizCarBot ls-files -- "$relativa/")
    if ($LASTEXITCODE -ne 0 -or $versionados.Count) {
        throw "No se retira una carpeta con archivos versionados: $relativa"
    }
}
$candidatos | ForEach-Object { Write-Output $_.FullName }
if (-not $Aplicar) { Write-Output 'Vista previa. Use -Aplicar para retirar con respaldo.'; return }

$documentosUsuario = [Environment]::GetFolderPath('MyDocuments')
$raizRespaldos = [IO.Path]::GetFullPath((Join-Path $documentosUsuario 'CarBot-respaldos-limpieza'))
if ($raizRespaldos.StartsWith($prefijoCarBot, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'El respaldo debe estar fuera del repositorio.'
}
$respaldo = Join-Path $raizRespaldos ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $respaldo | Out-Null
$manifiesto = @()
foreach ($carpeta in $candidatos) {
    $relativa = $carpeta.FullName.Substring($prefijoCarBot.Length)
    $destino = [IO.Path]::GetFullPath((Join-Path $respaldo $relativa))
    if (-not $destino.StartsWith($respaldo + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Destino fuera del respaldo.'
    }
    $archivos = @(Get-ChildItem -LiteralPath $carpeta.FullName -Recurse -File -Force)
    foreach ($archivo in $archivos) {
        $manifiesto += [pscustomobject]@{
            original = $archivo.FullName
            respaldo = Join-Path $respaldo $archivo.FullName.Substring($prefijoCarBot.Length)
            bytes = $archivo.Length
            sha256 = (Get-FileHash -LiteralPath $archivo.FullName -Algorithm SHA256).Hash
        }
    }
    # Guardar el inventario antes de mover: incluso una interrupcion conserva la trazabilidad.
    $manifiesto | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $respaldo 'manifiesto.json') -Encoding utf8
    New-Item -ItemType Directory -Path (Split-Path -Parent $destino) -Force | Out-Null
    Move-Item -LiteralPath $carpeta.FullName -Destination $destino
}
foreach ($registro in $manifiesto) {
    if ((Get-FileHash -LiteralPath $registro.respaldo -Algorithm SHA256).Hash -ne $registro.sha256) {
        throw "No coincide el respaldo: $($registro.respaldo)"
    }
}
Write-Output "Carpetas retiradas: $($candidatos.Count). Archivos respaldados y verificados: $($manifiesto.Count)."
Write-Output "Respaldo: $respaldo"
