param([switch]$SkipBuild)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot
Set-Location $root
$env:CARBOT_LAB_PORT=''
foreach($port in 8765..8795){
  $listener=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,$port)
  try {$listener.Start(); $env:CARBOT_LAB_PORT="$port"; break} catch {} finally {$listener.Stop()}
}
if(!$env:CARBOT_LAB_PORT){throw 'No hay puerto local disponible; no detener servicios ajenos'}
$id=Get-Date -Format 'yyyyMMddTHHmmss'
$project="carbot_harness_$id".ToLowerInvariant()
$out=Join-Path $root "outputs/harness/$id"
New-Item -ItemType Directory -Force $out | Out-Null
$env:CARBOT_HARNESS_ARTIFACTS=$out.Replace('\','/')
$env:CARBOT_HARNESS_SUBNET=& (Join-Path $root '.venv/Scripts/python.exe') scripts/harness/select_subnet.py
if($LASTEXITCODE -ne 0){throw 'No se pudo asignar subred sin borrar redes existentes'}
$env:CARBOT_HARNESS_ACCESS_SUBNET=& (Join-Path $root '.venv/Scripts/python.exe') scripts/harness/select_subnet.py $env:CARBOT_HARNESS_SUBNET
$env:CARBOT_HARNESS_RAG=& (Join-Path $root '.venv/Scripts/python.exe') scripts/harness/prepare_rag.py (Join-Path $out 'rag-canonical')
if($LASTEXITCODE -ne 0){throw 'Paquete RAG Git incompatible; no reconstruir índice'}
$env:CARBOT_HARNESS_SOURCE=& (Join-Path $root '.venv/Scripts/python.exe') scripts/harness/snapshot.py (Join-Path $out 'source')
if($LASTEXITCODE -ne 0){throw 'Snapshot no estable; se conservaron los originales'}
New-Item -ItemType Junction -Path (Join-Path $env:CARBOT_HARNESS_SOURCE 'frontend/node_modules') -Target (Join-Path $root 'frontend/node_modules') | Out-Null
$dc=@('compose','-p',$project,'-f','infrastructure/harness/compose.yml')
$results=[ordered]@{project=$project;synthetic=$true;official=$false;artifacts=$out;lab_url="http://127.0.0.1:$env:CARBOT_LAB_PORT";steps=@{}}
function Step($name,[scriptblock]$action){
  & $action *> (Join-Path $out "$name.command.log")
  $code=$LASTEXITCODE
  $results.steps[$name]=$code
  $results | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $out 'summary.json')
  Write-Host "${name}: exit=$code | $(Join-Path $out "$name.command.log")"
  if($code -ne 0){Get-Content (Join-Path $out "$name.command.log") -Tail 8 | Out-Host}
  return $code
}
docker version --format '{{.Server.Version}}'
if($LASTEXITCODE -ne 0){throw 'Docker Linux no disponible: E2E pendiente, sin equivalencia con mocks.'}
if(!$env:CARBOT_HARNESS_RUNTIME_IMAGE){$env:CARBOT_HARNESS_RUNTIME_IMAGE='carbot-harness:local'}
if(!$env:CARBOT_HARNESS_TEST_IMAGE){$env:CARBOT_HARNESS_TEST_IMAGE='carbot-harness-tests:local'}
if(!$SkipBuild){
  docker build -f backend/Dockerfile -t $env:CARBOT_HARNESS_RUNTIME_IMAGE .
  if($LASTEXITCODE -ne 0){throw 'Falló construcción runtime'}
  docker build -f backend/Dockerfile.harness --build-arg "RUNTIME_IMAGE=$env:CARBOT_HARNESS_RUNTIME_IMAGE" -t $env:CARBOT_HARNESS_TEST_IMAGE .
  if($LASTEXITCODE -ne 0){throw 'Falló construcción de pruebas'}
}
docker @dc config --quiet
if($LASTEXITCODE -ne 0){throw 'Compose inválido'}
docker @dc up -d --wait --wait-timeout 180 postgres redis api worker lab web
if($LASTEXITCODE -ne 0){throw 'Stack no saludable; conservar contenedores y revisar logs'}
docker @dc exec -T postgres createdb -U carbot_e2e carbot_lab_test
if($LASTEXITCODE -ne 0){throw 'No se pudo crear base de pytest aislada'}
Step 'readiness' {docker @dc exec -T lab python -m scripts.lab.check_ready} | Out-Host
Step 'pytest' {docker @dc run --rm tests} | Out-Host
Step 'ruff' {docker @dc run --rm --entrypoint ruff tests check --no-cache src tests main.py scripts/lab scripts/e2e scripts/verify_release_image.py ../machine_learning/training ../machine_learning/tests/test_runtime_bundle.py} | Out-Host
Step 'security' {docker @dc run --rm --entrypoint ruff tests check --no-cache src main.py --select S --ignore S104,S105,S110,S603} | Out-Host
Step 'machine-learning' {docker @dc run --rm --entrypoint python tests -m pytest -q -p no:cacheprovider ../machine_learning/tests/test_runtime_bundle.py --junitxml=/artifacts/ml.xml} | Out-Host
Step 'frontend' {Push-Location (Join-Path $env:CARBOT_HARNESS_SOURCE 'frontend'); try {npm.cmd run verify} finally {Pop-Location}} | Out-Host
Step 'e2e80' {docker @dc run --rm runner --phase initial} | Out-Host
foreach($service in @('api','worker','redis','postgres')){
  docker @dc restart $service
  if($LASTEXITCODE -ne 0){throw "No se pudo reiniciar $service"}
  docker @dc up -d --wait --wait-timeout 180 api worker postgres redis
  Step "restart-$service" {docker @dc run --rm runner --phase continuity --restart-service $service} | Out-Host
}
Step 'lab-scenarios' {docker @dc exec -T lab python -c "import httpx; r=httpx.post('http://localhost:8765/lab/run',json={},timeout=360); r.raise_for_status(); assert r.json()['passed'], r.text; print('10 turnos Toyota Yaris/Nissan Sentra aprobados')"} | Out-Host
$results | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $out 'summary.json')
Write-Host "Laboratorio: http://127.0.0.1:$env:CARBOT_LAB_PORT | Evidencia: $out"
if(@($results.steps.Values | Where-Object {$_ -ne 0}).Count){throw 'Harness con fallos: consultar summary.json y trazas. No se eliminaron recursos.'}













