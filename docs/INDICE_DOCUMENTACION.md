# Índice de documentación de CarBot

## Arquitectura y organización

- Estructura del monorepo: `docs/arquitectura/estructura_proyecto.md`.
- Conexiones entre frontend, backend, ML e infraestructura:
  `docs/arquitectura/conexiones_modulos.md`.

## Documentos vigentes

| Necesidad | Documento |
|---|---|
| Estado funcional completo | `docs/ESTADO_FINAL_CARBOT.md` |
| Cambios aplicados en la revisión | `docs/REGISTRO_CAMBIOS_2026-08-15.md` |
| Instalación rápida | `README.md` |
| Arquitectura de carpetas | `docs/arquitectura/estructura_proyecto.md` |
| PostgreSQL y migraciones | `docs/base_datos_postgresql.md` |
| Fuentes y entrenamiento ML | `machine_learning/data/FUENTES_ENTRENAMIENTO.md` |
| Fuentes documentales RAG | `machine_learning/manuals/FUENTES_Y_VALIDACION.md` |
| Recolección de casos reales | `docs/guia_recoleccion_datos.md` |
| Seguridad y secretos | `SECURITY.md` |
| Contribución y calidad | `CONTRIBUTING.md` |
| Manual técnico | `docs/manual_tecnico_chatbot.md` |
| Defensa de tesis | `docs/guia_defensa_tesis.md` |

## Evidencias generadas automáticamente

- `machine_learning/models/metricas_modelo.json`: evaluación interna vigente.
- `machine_learning/models/metricas_externas.json`: estado de validación externa.
- `machine_learning/data/reporte_calidad_dataset.json`: fotografía histórica de
  la limpieza que produjo 2,751 filas; el estado posterior se explica en el
  reporte maestro y en la trazabilidad de entrenamiento.
- `machine_learning/data/reporte_dataset_externo.json`: admisión de Zenodo.
- `docs/graficas/matriz_confusion_ml.png`: matriz del holdout agrupado.

## Documentos históricos o académicos

Los archivos de `docs/notas`, `docs/arquitectura_modular` y
`docs/reporte_profesionalizacion.md` explican decisiones y etapas anteriores.
Cuando una cifra o comportamiento difiera, prevalecen en este orden:

1. código y migraciones vigentes;
2. `docs/ESTADO_FINAL_CARBOT.md`;
3. métricas JSON generadas;
4. documentos históricos.

## Política de actualización

No guardar secretos, números completos, contraseñas ni tokens en documentación.
Toda cifra de pruebas debe indicar su fecha. Toda métrica ML debe enlazar el
artefacto JSON que la produjo.
