# Registro consolidado de cambios de CarBot

Fecha: 15 de agosto de 2026

Este registro reúne los cambios realizados durante la revisión integral. No
contiene credenciales ni valores privados.

## Profesionalización del repositorio

- Organización como monorepo con `frontend`, `backend`, `machine_learning`,
  `infrastructure`, `docs` y `scripts`.
- Configuración centralizada y plantilla `.env.example`.
- Convenciones mediante `.editorconfig`, `.gitattributes`, `CONTRIBUTING.md` y
  `SECURITY.md`.
- Docker, health checks, CI, Alembic y comandos de verificación.
- Eliminación de archivos de vistas obsoletos:
  `MecanicosView.tsx` y `ClientesSolicitudesView.tsx`.

## Panel administrativo

- Consolidación de clientes, solicitudes y personal en `Personas y accesos`.
- Vista dividida en `SolicitudesTab`, `ClientesTab` y `EquipoTallerTab`.
- Carga bajo demanda por módulo para reducir peticiones.
- Eliminación del ciclo de recargas de personas.
- Eliminación de la petición duplicada del catálogo de mecánicos.
- Paginación, filtros por fecha, ordenamiento, carga y estados vacíos en
  diagnósticos.
- Paginación real en backend mediante `limite` y `offset`.
- Obligación de ingresar notas cuando se descarta un diagnóstico.
- Dashboard alineado inicialmente al mes en curso y con skeletons.
- Promedio de tiempo corregido para respetar el periodo seleccionado.
- Indicador del Sidebar conectado a `/health/ready` con estados activo,
  parcial y sin conexión.
- Confirmaciones para activar, bloquear, revocar o cambiar roles.
- Sustitución de `alert()` por mensajes integrados.
- Protección de cuenta propia y del último administrador activo.

## Política definitiva de acceso

- El panel web quedó restringido a `administrador`/`admin` en frontend y backend.
- Mecánicos, jefes/supervisores y clientes no pueden iniciar sesión en el panel.
- Las rutas inválidas o heredadas se normalizan mediante `routing.ts`.
- Los mecánicos operan mediante su número autorizado de WhatsApp.
- Los clientes utilizan únicamente el menú informativo.
- La opción `4` crea una solicitud; aprobarla promueve al contacto a mecánico.
- Revocar acceso devuelve al rol cliente sin eliminar conversaciones ni historial.
- La migración `20260815_01` eliminó hashes de contraseña no administrativos.

## Autenticación y navegación

- Access token JWT con vigencia de dos horas.
- Refresh token rotatorio con vigencia de siete días.
- Endpoint `POST /api/v1/auth/refresh`.
- Reintento automático después de HTTP 401.
- Una sola renovación compartida cuando varias peticiones fallan simultáneamente.
- Cierre seguro si la cuenta fue bloqueada, desactivada o perdió el rol.
- Conservación de sesión en `carbot_session`.
- Conservación de última vista en `carbot_last_route`.
- Contraseña administrativa unificada: 12 caracteres, mayúscula, minúscula y número.

## WhatsApp y Meta

- Registro y verificación de un número de producción de WhatsApp Business.
- Webhook HTTPS dirigido al backend mediante ngrok.
- Uso de `META_ACCESS_TOKEN`, `META_PHONE_NUMBER_ID`, `META_VERIFY_TOKEN` y
  `META_APP_SECRET` como nombres canónicos.
- Permisos de usuario del sistema:
  `whatsapp_business_management` y `whatsapp_business_messaging`.
- Publicación de la app Meta para entrega de mensajes de producción.
- GitHub Pages usado para política de privacidad e instrucciones de eliminación;
  no como hosting del backend.
- Persistencia idempotente de entradas y outbox reintentable de salidas.

## Experiencia conversacional

- Separación determinista entre diagnóstico, consulta técnica y fuera de alcance.
- Las preguntas informativas reciben orientación y no contaminan el historial de averías.
- Extracción conservadora de marca, modelo, año, motor, combustible, equipo de
  gas y kilometraje.
- Solicitud automática de información faltante antes de continuar.
- Contexto temporal persistido en `conversaciones.contexto` mediante
  `20260815_04`.
- Advertencia ante kilometrajes ambiguos.
- Cliente sin autorización: cero ML, cero RAG y cero Gemini.
- Técnico autorizado: pipeline completo ML, RAG y Gemini.

## Diagnóstico y trazabilidad

- Se guardan las tres probabilidades ML principales.
- Se separan confianza ML y similitud RAG.
- Registro de versión ML y versión del corpus.
- Registro de etapas, duración, fuente, tokens, modelo Gemini y caché.
- Nueva columna JSON/JSONB mediante migración `20260815_02`.
- Separación de `diagnostico` y `consulta_tecnica` en la cola mediante
  `20260815_03`.
- Modal administrativo con barras comparativas ML, evidencia RAG, síntesis
  Gemini y cronología de etapas.
- Modo degradado ML+RAG cuando Gemini no está disponible.
- Caché LRU de 2,000 entradas con TTL de dos horas.

## Entrenamiento ML

- Auditoría de Zenodo DOI `10.5281/zenodo.15626055`, licencia CC BY 4.0.
- Descarga reproducible y verificación MD5.
- Rechazo del entrenamiento por síntomas aplanados que perdían contexto.
- Conservación de casos completos con síntomas relacionados.
- Admisión de 33 de 99 casos: 53 sin mapeo, 12 ambiguos y 1 duplicado excluidos.
- Holdout creado antes de incorporar los registros externos.
- Barreras sobre F1 macro, exactitud, calibración y degradación por clase.
- Modelo final `2.2.0-external-audited` con 2,894 registros.
- F1 macro: 95.49 % antes y 95.95 % después.
- ECE: 25.74 % antes y 24.81 % después.
- NHTSA excluido como etiqueta de reparación confirmada.
- Deuda declarada: 110 filas del dataset base requieren completar código,
  sistema y severidad.

## Pruebas y calidad

- Pruebas de roles y navegación.
- Pruebas de edición de personal y jerarquías.
- Pruebas de refresh JWT y seguridad.
- Pruebas de caché, contexto vehicular, intención y experiencia WhatsApp.
- Pruebas de persistencia, concurrencia, outbox y resiliencia.
- Pruebas de procedencia y aislamiento del dataset externo.
- Último resultado backend: 162 aprobadas y 46 omitidas.
- Linter y build frontend habían sido aprobados en la revisión funcional; los
  cambios documentales posteriores no modificaron componentes visuales.

## Documentación

- `docs/ESTADO_FINAL_CARBOT.md`: fuente principal del estado actual.
- `docs/INDICE_DOCUMENTACION.md`: mapa de documentos.
- `docs/trazabilidad_datos_entrenamiento_y_defensa_jurado.md`: defensa ML actualizada.
- `machine_learning/data/FUENTES_ENTRENAMIENTO.md`: procedencia externa.
- Este archivo: historial consolidado de lo aplicado.
