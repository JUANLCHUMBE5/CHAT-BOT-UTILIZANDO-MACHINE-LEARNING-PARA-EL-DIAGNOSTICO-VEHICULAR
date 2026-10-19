# Validación RAG-03I

Desde la raíz de un checkout RAG-03I, PowerShell. `python` debe apuntar al entorno de pruebas con las dependencias del backend; las versiones utilizadas están en la evidencia `entorno.txt`. El runner bloquea red externa, `.env`, credenciales heredadas y escritura en `machine_learning`. Usa exclusivamente puertos loopback 55439/56389.

```powershell
$out = 'scratch/rag03i-evidencias'
$run = 'scripts/experiments/rag03i/ejecutar.py'
docker compose -f scripts/experiments/rag03i/compose.test.yml up -d --wait
python -B $run --out "$out/migraciones" --db migrate
docker compose -f scripts/experiments/rag03i/compose.test.yml exec -T postgres createdb -U carbot_app carbot_rag03i_e2e_test
python -B $run --out "$out/e2e-migraciones" --db --e2e-db migrate
$env:COVERAGE_CORE = 'sysmon'
python -u -B $run --out "$out/suite-final" --db --coverage pytest tests -o faulthandler_timeout=120
python -u -B $run --out "$out/benchmark-definitivo" benchmark
python -u -B $run --out "$out/regresiones-definitivas" pytest tests/rag03i tests/rag03g/test_seguridad_y_documentos.py
python -u -B $run --out "$out/seguridad-definitiva" pytest tests/rag03g/test_seguridad_y_documentos.py tests/test_seguridad_commonrail_dpf.py tests/test_seguridad_mecanica_emergencia.py tests/test_bateria_independiente_seguridad.py
python -u -B $run --out "$out/agentes-final" pytest tests/rag03g/test_paquete.py tests/rag03g/test_cache_y_memoria.py tests/test_rag03a_relevancia_adversarial.py tests/test_rag03_remediacion_agente1.py ../test_rag03f_agente2_compatibilidad.py
python -u -B $run --out "$out/rag-final" rag
python -u -B $run --out "$out/e2e-final" --db --e2e-db e2e
python -u -B scripts/experiments/rag03i/sonda_worker.py "$out/worker-definitivo"
python -B scripts/experiments/rag03i/verificar_integridad.py --out "$out/integridad-final.json"
python -B scripts/experiments/rag03i/resumir.py $out
docker compose -f scripts/experiments/rag03i/compose.test.yml down
```

Cada ejecución conserva su código de salida y JUnit. Un código diferente de cero exige leer el fallo; no se transforma en PASS. La batería nueva es pública y de desarrollo, no un holdout independiente. Las dos pruebas DPF históricas y las aserciones OEM universales deben revisarse por separado; no se han reescrito para esta entrega. Los servicios no deben compartir la base de pruebas durante dos ejecuciones simultáneas de pytest.

El pipeline E2E conserva la cola durable PostgreSQL y Redis de contexto/estado. Solo se sustituye el transporte WhatsApp; no se envían mensajes reales. No iniciar `iniciar_carbot.cmd` ni túneles para estas pruebas.
