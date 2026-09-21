# CHECKLIST OPERATIVO PARA EL DÍA DE CAMPO
## Piloto Presencial y Recolección Oficial — CarBot Tesis

**Fecha de Preparación:** 19 de Septiembre de 2026  
**Objetivo:** Garantizar la integridad operativa, metodológica y técnica durante la jornada de evaluación experimental con los mecánicos en el taller automotriz.

---

### I. ANTES DE INICIAR LA JORNADA (Verificación Pre-Vuelo)

- [ ] **1. Base de Datos Operativa:**
  - PostgreSQL corriendo en puerto `5432` (`carbot_db`).
  - Conexión verificada: `psql -U postgres -d carbot_db -c "SELECT 1;"`.
- [ ] **2. Backend API Activo:**
  - FastAPI levantado en `http://localhost:8000`.
  - Swagger/OpenAPI respondiendo en `http://localhost:8000/docs`.
  - Endpoint de salud respondiendo `HTTP 200`: `GET /api/v1/health`.
- [ ] **3. Frontend Activo:**
  - Vite dev server / preview corriendo en `http://localhost:5173`.
  - Panel visual accesible desde la tableta / laptop del taller.
- [ ] **4. Canal WhatsApp & Webhook Operativo:**
  - Túnel ngrok / Cloudflare activo hacia `http://localhost:8000/api/v1/webhook/whatsapp`.
  - Número de WhatsApp del bot verificado y conectado a Meta Cloud API.
- [ ] **5. CarBot Responde en Vivo:**
  - Enviar mensaje de prueba desde WhatsApp: *"El motor tiembla en ralentí y pierde fuerza"*.
  - Comprobar recepción de diagnóstico estructurado con Top 3 fallas y pruebas físicas.
- [ ] **6. Contadores Oficiales en Cero:**
  - Verificar en panel web y BD que la muestra oficial esté limpia:
    - **PRE:** `0 / 30`
    - **POST:** `0 / 30`
    - **TOTAL:** `0 / 60`
- [ ] **7. Entorno de Trabajo Definido:**
  - Si se realizan pruebas de calentamiento/familiarización con los mecánicos: Usar selector **PILOTO**.
  - Si se inicia la evaluación formal de los 60 casos: Usar selector **OFICIAL**.
- [ ] **8. Sincronización Horaria del Servidor:**
  - Verificar que la hora del sistema sea la hora local oficial de Lima (UTC-5) para que `inicio_sistema_at` y `fin_sistema_at` tengan sello temporal fidedigno.
- [ ] **9. Respaldo de Seguridad Previo:**
  - Tomar backup inicial de PostgreSQL antes de ingresar al taller:  
    `pg_dump -U postgres -d carbot_db -F c -b -v -f backup_carbot_pre_campo.dump`.

---

### II. DURANTE LA JORNADA (Protocolo de Registro)

- [ ] **1. Verificar Fase Correcta:**
  - Para vehículos evaluados por el mecánico bajo método tradicional: Seleccionar **Pre-test**.
  - Para vehículos evaluados con asistencia de CarBot: Seleccionar **Post-test**.
- [ ] **2. Verificar Entorno Seleccionado:**
  - Para los casos reales de la muestra: Asegurarse de que el selector esté en **OFICIAL**.
  - Comprobar que aparezca el badge visual correspondiente (**OFICIAL** en dorado/azul, **PILOTO** en gris).
- [ ] **3. Registro Pre-test (Tradicional):**
  - Ingresar placa (enmascarada), marca/modelo, síntoma reportado.
  - Registrar el diagnóstico emitido por el mecánico (sin intervención de CarBot).
  - Medir y registrar el tiempo de diagnóstico manual en minutos (`tiempo_diagnostico_minutos`).
  - Registrar la falla real comprobada en el vehículo y el método de confirmación física.
- [ ] **4. Registro Post-test (Con CarBot):**
  - Vincular la consulta seleccionando el `diagnostico_id` generado por WhatsApp.
  - Comprobar que los campos de síntoma, predicción de CarBot y confianza se precarguen automáticamente.
  - Verificar que la predicción original de CarBot permanezca **bloqueada e inmutable**.
  - Registrar la falla física real encontrada y el método de confirmación metrológica.
- [ ] **5. Confirmación de Ficha:**
  - Al presionar "Guardar Ficha Oficial", revisar el modal de confirmación con la advertencia de registro irreversible.
  - Confirmar explícitamente en el modal.
- [ ] **6. Comprobación de Persistencia:**
  - Comprobar que la ficha aparezca inmediatamente en el historial en estado `verificado`.
  - Comprobar que el contador aumente a `1/30`, `2/30`, etc.
- [ ] **7. Regla de Oro Operativa:**
  - **PROHIBIDO** editar la base de datos directamente con queries manuales durante la recolección.
  - Todo registro debe entrar por la interfaz de usuario validada.

---

### III. AL FINAL DEL DÍA (Cierre y Custodia de Datos)

- [ ] **1. Comprobar Conteos Finales de la Muestra:**
  - Verificar el avance del trabajo de campo:
    - Pre-test completados: `N / 30`.
    - Post-test completados: `M / 30`.
    - Total de casos oficiales acumulados: `(N + M) / 60`.
- [ ] **2. Exportar Respaldo Oficial Inmediato:**
  - Descargar exportación oficial en formato CSV (LONG) desde el panel de validación.
  - Comprobar que el archivo descargado contenga las columnas metodológicas: `Fase`, `Tipo_Registro`, `Sintoma_Presentado`, `Falla_Real_Taller`, `ChatBot_Prediccion`, `Tiempo_Diagnostico_Minutos`, `Prediccion_Correcta`, `Campos_Completos`.
- [ ] **3. Verificar Registros Incompletos o Borradores:**
  - Revisar si quedó alguna ficha en estado `borrador` por falta de método de confirmación o evidencia.
  - Completar con los mecánicos la evidencia física antes de retirarse del taller.
- [ ] **4. Custodia y Conservación de Evidencias:**
  - Archivar copias de fotos de elevador, reportes de scanner, capturas de osciloscopio o notas de taller asociadas al código `evidencia_ref`.
- [ ] **5. Backup Completo de Cierre:**
  - Generar dump final con timestamp:  
    `pg_dump -U postgres -d carbot_db -F c -b -v -f backup_carbot_cierre_campo_$(date +%Y%m%d).dump`.
  - Almacenar una copia en almacenamiento seguro fuera de línea (USB / nube cifrada).
