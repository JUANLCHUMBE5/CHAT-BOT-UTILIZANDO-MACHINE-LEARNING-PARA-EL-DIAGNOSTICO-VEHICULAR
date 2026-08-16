# Estado final documentado de CarBot

Fecha de corte: 15 de agosto de 2026

Este documento es la fuente principal para conocer el estado funcional actual
del proyecto. Los documentos con fecha anterior se consideran antecedentes y
no deben usarse para contradecir esta descripción.

## 1. Objetivo y alcance

CarBot es un asistente de diagnóstico vehicular preliminar para un taller de
Carabayllo. Recibe mensajes por WhatsApp, diferencia clientes de personal
técnico autorizado y combina clasificación ML, recuperación RAG y síntesis con
Gemini. El resultado es una hipótesis técnica que siempre requiere comprobación
física; no sustituye al mecánico ni al manual OEM del vehículo.

El panel web es administrativo. Los mecánicos trabajan únicamente mediante
WhatsApp y no necesitan usuario ni contraseña para entrar al panel.

## 2. Arquitectura vigente

```text
WhatsApp del cliente o mecánico
              |
              v
Meta Cloud API -> webhook FastAPI -> PostgreSQL
                                      |
                    +-----------------+------------------+
                    |                                    |
                 cliente                         técnico autorizado
                    |                                    |
             menú informativo              intención y contexto vehicular
             y solicitud #4                           |
                                              ML -> RAG -> Gemini
                                                    |
                                      respuesta WhatsApp + trazabilidad
                                                    |
                                      panel React solo administrador
```

El repositorio es un monorepo dividido en:

- `frontend`: panel React y TypeScript.
- `backend`: API FastAPI, lógica, persistencia e integraciones.
- `machine_learning`: datasets, scripts, modelos y corpus RAG.
- `infrastructure`: PostgreSQL, Docker e infraestructura auxiliar.
- `scripts`: inicio, comprobación y tareas operativas.
- `docs`: arquitectura, operación, tesis y evidencias.

## 3. Tecnologías y herramientas

| Capa | Tecnología | Uso |
|---|---|---|
| Frontend | React 19, TypeScript 6, Vite 8 | Panel administrativo |
| Interfaz | Lucide React, Recharts, CSS | Iconos, métricas y visualizaciones |
| Backend | Python, FastAPI, Uvicorn, Pydantic | API REST y webhook |
| Persistencia | PostgreSQL, SQLAlchemy async, asyncpg, Alembic | Datos operativos y migraciones |
| ML | scikit-learn, TF-IDF, Linear SVM calibrado | Clasificación de fallas |
| RAG | FAISS y corpus técnico local | Recuperación de evidencia |
| LLM | Google Gemini | Síntesis técnica controlada |
| Mensajería | WhatsApp Cloud API de Meta | Entrada y salida de mensajes |
| Exposición local | ngrok | URL HTTPS temporal para el webhook local |
| Seguridad | JWT HS256, PBKDF2-HMAC-SHA256, HMAC, Fernet | Sesiones, claves e identidades |
| Calidad | Pytest, Oxlint, TypeScript, `git diff --check` | Verificación automatizada |

Las versiones exactas están fijadas en `backend/requirements.txt` y
`frontend/package.json`.

## 4. Roles y permisos

| Rol | WhatsApp básico | Diagnóstico completo | Panel web | Administración |
|---|---:|---:|---:|---:|
| Cliente | Sí | No | No | No |
| Mecánico autorizado | Sí | Sí | No | No |
| Jefe de taller/supervisor heredado | Sí | Sí | No | No |
| Administrador | Sí | Sí | Sí | Sí |

Reglas implementadas:

- Un contacto nuevo se registra automáticamente como cliente.
- La opción `4` crea una solicitud de acceso como mecánico.
- Solo el administrador puede aprobar o rechazar la solicitud desde el panel.
- Al aprobar, el número queda autorizado para utilizar el flujo técnico.
- El mecánico se identifica por su número de WhatsApp; no recibe credenciales web.
- Solo un administrador puede crear o promover otra cuenta administrativa.
- No se permite desactivar, bloquear o degradar al último administrador activo.
- Revocar el acceso técnico devuelve al usuario al rol cliente y conserva el historial.
- El backend comprueba los permisos; ocultar botones en el frontend no es la única protección.

## 5. Flujo de WhatsApp

### Cliente no autorizado

Recibe un menú básico con servicios, citas, ubicación/horario y solicitud de
acceso. Este flujo no ejecuta ML, RAG ni Gemini y no crea diagnósticos.

### Solicitud de mecánico

1. El cliente responde `4`.
2. Se crea una solicitud pendiente asociada a su identidad protegida.
3. El administrador abre `Personas y accesos > Solicitudes de acceso`.
4. Aprueba o rechaza la solicitud.
5. Si se aprueba, el número queda habilitado para consultas técnicas completas.
6. La notificación se envía por WhatsApp mediante el outbox persistente.

### Mecánico autorizado

Los mensajes pasan por clasificación de intención:

- `diagnostico`: describe síntomas o códigos DTC y puede registrarse.
- `consulta_tecnica`: pregunta informativa; se responde, pero no se guarda como avería.
- `fuera_de_alcance`: no se fuerza una predicción automotriz.

El audio está desactivado por defecto. Cuando se habilita, debe descargarse y
transcribirse realmente; si no hay persistencia y control de cuota, se rechaza
de forma segura en lugar de simular una transcripción.

## 6. Contexto del vehículo y conversación

El bot extrae únicamente datos expresamente escritos por el mecánico:

- marca;
- modelo;
- año;
- motor o cilindrada;
- combustible;
- equipo GNV/GLP cuando se menciona;
- kilometraje.

Si falta información necesaria, solicita datos adicionales y conserva el
síntoma inicial en el contexto JSON de la conversación. La siguiente respuesta
completa el perfil y permite continuar sin comenzar desde cero. El extractor no
inventa versiones ni motorizaciones y advierte sobre kilometrajes ambiguos como
“100 km” cuando probablemente se quiso indicar “100 mil km”.

Conocer marca, modelo y año mejora el contexto, pero no garantiza una respuesta
específica para esa unidad. Para procedimientos, capacidades, fluidos o fallas
de fábrica se requiere una fuente OEM identificada o una fuente oficial de
recalls separada del clasificador.

## 7. Pipeline de diagnóstico

1. Se sanitiza y normaliza el mensaje y la jerga peruana.
2. Se clasifica la intención.
3. Si corresponde, se solicita o completa el perfil del vehículo.
4. TF-IDF transforma el texto y Linear SVM calibrado calcula probabilidades.
5. Se guardan las tres hipótesis ML con mayor probabilidad.
6. FAISS recupera evidencia del corpus RAG y calcula similitud.
7. Gemini sintetiza una orientación estructurada cuando hay cuota y conexión.
8. Si Gemini falla, el modo degradado responde con ML+RAG.
9. PostgreSQL conserva diagnóstico, hipótesis, etapas, tiempos, fuente y consumo.
10. El outbox envía la respuesta de manera reintentable por WhatsApp.

La caché LRU usa una clave derivada del síntoma y del vehículo, capacidad de
2,000 entradas y TTL de dos horas. La trazabilidad indica si una respuesta salió
de caché. Esta caché acelera consultas idénticas; no reemplaza PostgreSQL.

## 8. Panel administrativo

Rutas actuales:

- `/login`: autenticación administrativa.
- `/inicio`: métricas del taller.
- `/personas`: solicitudes, clientes y equipo del taller.
- `/diagnosticos`: historial, filtros, revisión y detalle técnico.

Las antiguas rutas `/clientes` y `/mecanicos` redirigen a `/personas`. Los datos
se cargan bajo demanda según la vista activa para evitar peticiones masivas.

### Inicio

- Métricas por periodo, inicialmente “Este mes”.
- Skeletons durante la carga.
- Tiempo promedio calculado con el mismo rango seleccionado.

### Personas y accesos

- Solicitudes pendientes.
- Directorio de clientes.
- Equipo técnico y administrativo.
- Alta, edición, activación, bloqueo, cambio de rol y revocación.
- Confirmaciones mediante modales y mensajes integrados, sin `alert()`.
- Contraseñas solo para administradores: mínimo 12 caracteres, mayúscula,
  minúscula y número.

### Diagnósticos

- Búsqueda, estado, modo, mecánico, periodo y ordenamiento.
- Paginación con 5, 10, 20 o 50 filas por página.
- Estados `generado`, `en_revision`, `confirmado` y `descartado`.
- Descartar exige una observación técnica.
- Detalle por diagnóstico con:
  - síntoma original y normalizado;
  - tres probabilidades ML representadas con barras;
  - versión del modelo;
  - evidencia, fuente y similitud RAG;
  - síntesis Gemini y modelo utilizado;
  - etapas, duración, tokens y uso de caché.

Actualmente se muestran visualizaciones de barras y etapas, no imágenes internas
de árboles del Random Forest. El modelo elegido es Linear SVM, por lo que no
existen árboles de decisión individuales que mostrar.

## 9. Autenticación y continuidad de sesión

- Inicio: `POST /api/v1/auth/login`.
- Access token JWT: dos horas.
- Refresh token: siete días.
- Renovación: `POST /api/v1/auth/refresh`.
- El frontend reintenta una vez la petición que recibió HTTP 401 después de
  rotar los tokens.
- Las renovaciones simultáneas comparten una sola petición en curso.
- Si el refresh token expiró, fue alterado o la cuenta perdió permisos, se
  elimina la sesión y se regresa al login.
- La sesión administrativa se guarda en `localStorage` bajo `carbot_session`.
- La última ruta válida se guarda como `carbot_last_route` y se restaura después
  de iniciar sesión.
- Las rutas del panel rechazan cualquier sesión que no sea administrativa.

Guardar tokens en `localStorage` exige mantener el frontend libre de XSS. En un
despliegue público de mayor riesgo se recomienda migrar el refresh token a una
cookie `HttpOnly`, `Secure` y `SameSite`.

## 10. Persistencia, privacidad y resiliencia

PostgreSQL almacena talleres, roles, usuarios, identidades, vehículos,
conversaciones, mensajes, diagnósticos, hipótesis, trabajos Gemini, outbox,
consumo y auditoría.

- Teléfonos y placas se buscan mediante HMAC-SHA256.
- En la interfaz solo se muestran los últimos cuatro dígitos.
- Los destinatarios que deben recuperarse para enviar mensajes se cifran con Fernet.
- La firma del webhook Meta se valida con `META_APP_SECRET`.
- `meta_message_id` evita procesar dos veces el mismo mensaje.
- El mensaje entrante se persiste antes de confirmar su procesamiento.
- El outbox conserva envíos y reintentos ante fallos externos.
- Las cuotas Gemini se coordinan en PostgreSQL entre workers.
- Los datos operativos no deben usarse automáticamente para reentrenar: primero
  necesitan confirmación mecánica, anonimización y separación de evaluación.

Migraciones recientes:

| Revisión | Cambio |
|---|---|
| `20260815_01` | Elimina credenciales web de roles no administrativos |
| `20260815_02` | Añade trazabilidad JSON por diagnóstico |
| `20260815_03` | Distingue diagnóstico de consulta técnica en la cola |
| `20260815_04` | Persiste contexto conversacional del vehículo |

## 11. Modelo ML y datos

Estado vigente del modelo:

- Versión: `2.2.0-external-audited`.
- Algoritmo: Linear SVM calibrado con TF-IDF de unigramas y bigramas.
- Dataset base: 2,861 registros, 48 clases y 14 sistemas.
- Fuente académica: Zenodo, DOI `10.5281/zenodo.15626055`, CC BY 4.0.
- Casos fuente revisados: 99.
- Casos externos admitidos: 33.
- Total de entrenamiento final: 2,894.
- Holdout: 570 casos tomados únicamente del dataset base.
- Exactitud: 97.54 %.
- F1 macro: 95.95 %.
- F1 ponderado: 97.03 %.
- ECE: 24.81 %; menor es mejor.

Los casos externos entraron solo porque mejoraron F1 macro sin degradar
materialmente exactitud, calibración o clases individuales. NHTSA no se usa como
etiqueta de reparación: un reclamo no confirma la causa técnica. Puede integrarse
en el futuro como evidencia separada de recalls o como contexto RAG.

El modelo continúa bloqueado para uso autónomo porque hay soporte insuficiente,
una clase con F1 de 0.20 y calibración por encima del objetivo. Los valores
exactos están en `machine_learning/models/metricas_modelo.json`.

Deuda de calidad conocida: `reporte_calidad_dataset.json` documenta la limpieza
que produjo 2,751 filas. El CSV base vigente contiene 110 ejemplos añadidos
posteriormente que tienen `sintoma` y `falla`, pero todavía carecen de
`codigo_falla`, `sistema` y `severidad`. El clasificador puede utilizarlos porque
entrena con texto y falla; sin embargo, esos metadatos deben completarse mediante
la taxonomía antes de declarar totalmente cerrado el linaje del dataset base.

## 12. Meta, ngrok, GitHub Pages y dominios

- Meta envía webhooks al backend, por ejemplo
  `https://<dominio-ngrok>/api/v1/webhook`.
- `META_VERIFY_TOKEN` debe ser idéntico en Meta y `.env`; no es el access token.
- `META_PHONE_NUMBER_ID` identifica el número emisor registrado.
- `META_ACCESS_TOKEN` autoriza llamadas Graph API y debe provenir del usuario de
  sistema con `whatsapp_business_management` y `whatsapp_business_messaging`.
- Para producción, la app Meta debe estar publicada y suscrita al webhook.
- GitHub Pages sirve la política de privacidad y las instrucciones de
  eliminación de datos. No ejecuta FastAPI, PostgreSQL ni el chatbot.
- ngrok expone el backend local; si se cierra ngrok o cambia la URL, Meta deja de
  entregar mensajes hasta actualizar el webhook.

Nunca documentar ni subir tokens, contraseñas, `APP_SECRET` o claves privadas.
Los tres archivos de configuración cumplen funciones distintas:

- `.editorconfig`: reglas de formato del código.
- `.env.example`: plantilla pública sin secretos.
- `.env`: configuración privada local, excluida de Git.

## 13. Inicio y operación

Desde la raíz del proyecto en Windows:

```powershell
.\iniciar_carbot.cmd
```

El lanzador:

1. comprueba `.venv` y el frontend;
2. intenta iniciar PostgreSQL 17;
3. ejecuta `alembic upgrade head`;
4. inicia FastAPI en el puerto 8000;
5. inicia Vite en el puerto 5173;
6. inicia ngrok hacia el puerto 8000;
7. informa cuándo el backend y el frontend están escuchando.

Direcciones locales:

- Panel: `http://localhost:5173`
- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health/ready`

Para iniciar sin ngrok:

```powershell
.\scripts\iniciar_carbot.ps1 -SinNgrok
```

## 14. Verificación vigente

Última ejecución completa registrada el 15 de agosto de 2026:

- Backend: 162 pruebas aprobadas y 46 omitidas por dependencias opcionales.
- Dataset externo: 3 pruebas de integridad aprobadas.
- Compilación Python: aprobada.
- `git diff --check`: aprobado; solo avisos informativos de finales de línea.
- Entrenamiento reproducible: aprobado.

Los `skip` no son fallos; corresponden principalmente a integraciones que
requieren servicios externos o una base específica. Las advertencias de librerías
deprecadas deben mantenerse bajo seguimiento.

## 15. Limitaciones y trabajo pendiente

- El modelo no está aprobado para diagnóstico autónomo.
- Hay 110 filas base con etiqueta de falla válida pero metadatos taxonómicos
  incompletos; deben normalizarse y generar un nuevo reporte de calidad.
- Faltan casos reales confirmados y reservados para validación externa.
- El corpus RAG necesita más manuales OEM con marca, modelo, año, edición y página.
- La información de recalls debe proceder de fuentes oficiales y mostrarse como
  evidencia, no como predicción aprendida.
- La dirección y horario del taller deben configurarse con datos reales.
- El plan gratuito de Gemini y ngrok tiene límites y no ofrece disponibilidad empresarial.
- El dominio ngrok usado por el lanzador está fijado actualmente en el script;
  si cambia, debe actualizarse allí y en Meta.
- La aplicación puede recordar la pantalla, pero no formularios incompletos.
- Las consultas técnicas informativas no aparecen en el historial de averías por diseño.

## 16. Regla de mantenimiento documental

Todo cambio futuro debe actualizar, como mínimo:

1. este documento si cambia el comportamiento funcional;
2. `.env.example` si cambia configuración;
3. `docs/base_datos_postgresql.md` si cambia el esquema;
4. `machine_learning/data/FUENTES_ENTRENAMIENTO.md` y métricas si cambia ML;
5. pruebas y comandos verificados;
6. una migración Alembic cuando cambie PostgreSQL.

No se debe afirmar que una funcionalidad está terminada solo porque aparece en
una pantalla o documento: el código, la migración y las pruebas deben coincidir.
