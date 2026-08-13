# Persistencia PostgreSQL de CarBot

## Propósito

PostgreSQL almacena la información operacional del chatbot: talleres, mecánicos autorizados, vehículos, diagnósticos, mensajes y consumo de servicios externos. Los archivos CSV continúan siendo artefactos de entrenamiento y evaluación del modelo de Machine Learning; no sustituyen la base transaccional.

La aplicación usa:

- SQLAlchemy 2.0 como ORM asíncrono.
- `asyncpg` como controlador de PostgreSQL.
- Alembic como historial versionado del esquema.
- Un pool de conexiones por proceso de la aplicación.

## Modelo inicial

| Tabla | Responsabilidad |
|---|---|
| `talleres` | Organización propietaria de sus registros. |
| `roles` | Catálogo de administrador, mecánico y supervisor. |
| `usuarios` | Mecánicos autorizados, identificados mediante hash del número de WhatsApp. |
| `vehiculos` | Datos técnicos del vehículo; la placa completa no se almacena en texto plano. |
| `conversaciones` | Sesiones y ventana de servicio de WhatsApp. |
| `mensajes` | Entrada/salida, estado de entrega, categoría y costo estimado. |
| `diagnosticos` | Síntoma, predicción, confianza, fuente y conclusión del mecánico. |
| `hipotesis_diagnostico` | Posibles fallas y pruebas recomendadas ordenadas. |
| `uso_api` | Tokens, unidades y costo estimado de Meta, Google, AWS o procesos locales. |
| `auditoria` | Trazabilidad de acciones sin guardar payloads completos ni secretos. |

Todas las entidades operativas usan UUID, fechas con zona horaria, claves foráneas, restricciones de dominio e índices para sus relaciones principales.

## Creación local

1. Abrir `infrastructure/database/postgresql/crear_carbot.sql` en pgAdmin.
2. Reemplazar la contraseña de ejemplo y ejecutar el script una sola vez como administrador.
3. Configurar `.env` sin compartirlo ni subirlo al repositorio.
4. Verificar la conexión:

```powershell
python -m scripts.postgresql.verificar_conexion
```

5. Aplicar el esquema:

```powershell
python -m alembic upgrade head
```

6. Comprobar la revisión instalada:

```powershell
python -m alembic current
```

## Registrar el primer taller y usuario

El número de WhatsApp identifica al mecánico autorizado. El comando no guarda
el número completo: persiste un HMAC-SHA256 y solamente sus últimos cuatro
dígitos. Ejecute el registro localmente y omita `--telefono` para escribirlo en
un prompt oculto (así tampoco queda en el historial de PowerShell):

```powershell
python -m scripts.registrar_taller_admin --taller "Nombre del taller" --ruc "20123456789" --nombres "Nombre" --apellidos "Apellido" --rol administrador
```

Roles válidos: `administrador`, `mecanico` y `supervisor`. El alias `admin` se
mantiene únicamente por compatibilidad. El mismo número puede ejecutarse otra
vez sin duplicar al usuario.

## Persistencia del webhook

Con `DATABASE_ENABLED=true`, el webhook autoriza al remitente por el hash de su
número y guarda conversación, mensajes, diagnóstico, hipótesis, auditoría y uso
de APIs. `meta_message_id` es único para hacer el procesamiento idempotente,
incluso ante reintentos concurrentes de Meta. Los eventos de entrega o lectura
se aceptan pero no generan diagnósticos.

El consumo de Gemini solo se registra cuando Google responde correctamente y
entrega `usageMetadata`; el fallback local no se contabiliza como uso externo.
El modelo se configura con `GEMINI_MODEL` y no queda fijado dentro del código.

## Cambios futuros

No se deben crear o modificar tablas manualmente en pgAdmin. Cada cambio se expresa primero en los modelos y luego se genera como una nueva revisión:

```powershell
python -m alembic revision --autogenerate -m "describir cambio en español"
python -m alembic upgrade head
```

La migración generada siempre debe revisarse antes de ejecutarla. Alembic detecta muchos cambios estructurales, pero no sustituye la revisión técnica.

## AWS

En Amazon RDS para PostgreSQL se utilizará el mismo esquema y las mismas migraciones. Solo cambiarán `DATABASE_URL` o las variables `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` y `POSTGRES_PASSWORD`. La contraseña nunca debe almacenarse en GitHub.

