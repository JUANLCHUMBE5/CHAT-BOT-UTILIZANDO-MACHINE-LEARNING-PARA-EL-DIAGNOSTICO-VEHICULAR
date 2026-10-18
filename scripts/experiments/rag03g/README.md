# RAG-03G: reproducción aislada

Candidato de desarrollo; no autoriza producción, merge ni activación experimental.
Python utilizado: 3.14.5 en Windows. El lock adjunto registra el entorno realmente
instalado; no sustituye un lock multiplataforma. Instalar en un venv nuevo.

Desde la raíz de este checkout, usando su propio intérprete aislado:

```powershell
python -m venv .venv-rag03g
.venv-rag03g/Scripts/python.exe -m pip install -r scripts/experiments/rag03g/requirements-win-py314.lock.txt
docker compose -f backend/docker-compose.rag03g.yml up -d --wait
.venv-rag03g/Scripts/python.exe scripts/experiments/rag03g/verificar_integridad.py --out scratch/integridad.json
.venv-rag03g/Scripts/python.exe scripts/experiments/rag03g/ejecutar.py --out scratch/migraciones --db migrate
.venv-rag03g/Scripts/python.exe scripts/experiments/rag03g/ejecutar.py --out scratch/backend --db pytest tests
.venv-rag03g/Scripts/python.exe scripts/experiments/rag03g/ejecutar.py --out scratch/regresiones pytest tests/rag03g
.venv-rag03g/Scripts/python.exe scripts/experiments/rag03g/ejecutar.py --out scratch/agente2 pytest ../test_rag03f_agente2_compatibilidad.py
.venv-rag03g/Scripts/python.exe scripts/experiments/rag03g/ejecutar.py --out scratch/rag rag
.venv-rag03g/Scripts/python.exe scripts/experiments/rag03g/comparar_evaluadores.py --out scratch/criterios
```

`comparar_evaluadores.py` requiere el historial de los commits 1858be4e y 3fa09f4e.
Los tres evaluadores reciben escenarios y oráculos serializados con el mismo hash.
Cada uno vuelve a ejecutar el mismo runtime; los UUID y tiempos pueden variar.
No se cambian los casos históricos para hacerlos pasar.

E2E utiliza otra base vacía en el mismo PostgreSQL de pruebas:

```powershell
docker compose -f backend/docker-compose.rag03g.yml exec -T postgres createdb -U carbot_test carbot_rag03g_e2e_test
.venv-rag03g/Scripts/python.exe scripts/experiments/rag03g/ejecutar.py --out scratch/e2e-migraciones --db --e2e-db migrate
.venv-rag03g/Scripts/python.exe scripts/experiments/rag03g/ejecutar.py --out scratch/e2e --db --e2e-db e2e
docker compose -f backend/docker-compose.rag03g.yml down
```

No ejecutar E2E dos veces sobre la misma base: crear otra base vacía o recrear
exclusivamente estos contenedores efímeros. Se simula únicamente el transporte
WhatsApp; webhook firmado, cola durable PostgreSQL, worker, outbox, persistencia
y sesiones/heartbeat Redis son reales de pruebas. Redis no es el broker durable.
El runner ignora `.env`, vacía credenciales de proveedores y bloquea conexiones
externas. Solo habilita puertos loopback 55439 y 56389 con `--db`.

## Criterios y límites

- Una decisión `SEGURIDAD_CRITICA` no acredita seguridad sin prohibición visible.
- Una advertencia no exime instrucciones peligrosas posteriores ni límites OEM.
- Un requisito visible no se satisface con un dato oculto del estado; únicamente
  requisitos explícitos `estado:` inspeccionan estado.
- Una abstención no satisface automáticamente cualquier expectativa.
- Plan B exige alternativa observable o continuidad provisional sin confirmación.
- Dimensiones no comprobadas se registran como `null`, con denominadores separados.
- Los 120 escenarios, los benchmarks 100/30 y las regresiones nuevas son datos
  públicos de desarrollo. No acreditan generalización ni exactitud clínica.
- No se ha creado ni congelado el holdout de 180 casos. `ejecutar_holdout.py`
  acepta un paquete futuro custodiado por otro auditor, verifica sus hashes y
  captura salidas sin leer los oráculos ni puntuar. El custodio debe sellar
  previamente escenarios, resultados esperados, protocolo y manifiesto
  `carbot.holdout/1` (`count`, `custodian`, `frozen_at`, `scenarios` y `oracles`
  con `path` y `sha256`), y mantenerlos fuera del ajuste de esta implementación.

`sellar_paquete.py` solo genera el manifiesto de la entrega experimental preservada;
no reconstruye índices ni entrena. No usarlo para legitimar archivos adulterados:
la auditoría debe contrastar también los hashes de procedencia del informe.
El cargador valida inventario antes de deserializar y comprueba los 256 vectores.
La política sigue `corpus_validado=False`; el selector predeterminado es canónico.

Trabajo de campo pendiente de verificación. Los resultados pretest y postest se
calcularán exclusivamente con registros reales recopilados y verificados durante
la aplicación de los instrumentos. Esta ejecución no verificó el avance de los
60 registros ni permite aceptar hipótesis de tesis. La prueba inferencial queda
pendiente de definición con el asesor estadístico según la naturaleza de la muestra.
