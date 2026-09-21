# Arquitectura del backend

El backend es un **monolito modular por capas**, inspirado en Clean
Architecture y puertos/adaptadores. No son microservicios: todos los módulos se
despliegan juntos como una sola API FastAPI.

## Capas canónicas

- `domain/`: conceptos y reglas centrales del diagnóstico vehicular.
- `application/`: casos de uso, puertos y trabajos asíncronos.
- `interfaces/`: entradas HTTP y canales de mensajería, incluido WhatsApp.
- `infrastructure/`: adaptadores de PostgreSQL, ML, RAG y servicios externos.

La dirección deseada de dependencias es:

```text
interfaces -> application -> domain
                    ^
                    |
             infrastructure
```

`application` define lo que necesita; `infrastructure` aporta las
implementaciones. El ensamblaje se realiza en `infrastructure/container.py` y
en el ciclo de vida de `main.py`.

## Migración compatible

Los paquetes `application`, `domain`, `infrastructure/ml` e
`infrastructure/rag` son los puntos de importación canónicos. Algunos reexportan
temporalmente implementaciones probadas que siguen en `core/`,
`infrastructure/modelo_ml.py` e `infrastructure/motor_rag.py`. Esto permite
mover internamente cada componente en fases posteriores sin cambiar contratos,
rutas HTTP ni comportamiento.

No debe crearse un servicio `bot` independiente: WhatsApp es un adaptador de
entrada en `interfaces/messaging/whatsapp`; el caso de uso de diagnóstico es
único y también puede ser llamado desde REST.

Las fronteras del dominio se comprueban automáticamente: `domain/` no puede
importar `interfaces/` ni `infrastructure/`. Los controladores son los endpoints
de `interfaces/api/v1/endpoints`; no se crea una segunda carpeta `controllers`.

La seguridad transversal incluye sesiones refresh de un solo uso, bloqueo
progresivo de autenticación, rate limiting compartido en producción, firmas de
webhook, límites de entrada, encabezados HTTP y verificación SHA-256 de los
artefactos ejecutables de ML.
