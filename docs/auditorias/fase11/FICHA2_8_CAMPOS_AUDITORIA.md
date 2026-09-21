# Fase 11.5.1 - Auditoría documental de los 8 campos de Ficha 2

**Proyecto:** CarBot - Chatbot utilizando machine learning para el diagnóstico vehicular en talleres mecánicos en Carabayllo 2026  
**Fecha:** 2026-09-19  
**Indicador:** RDC / PRDC = Registros completos / Total de registros evaluados x 100  

## Documentos revisados

- `C:\Users\leonc\OneDrive\Pictures\AnyDesk\LIMA-NORTE_PI_LEON_POMA.docx`
- `C:\Users\leonc\Downloads\Anexo_2_3_Instrumentos_validacion_CORREGIDO.docx`
- `C:\Users\leonc\Downloads\Matriz_de_consistencia_Tesis_Leon_Poma.docx`
- `C:\Users\leonc\Downloads\Matriz_de_consistencia_resumida_Leon_Poma.docx`
- `docs/TESIS_CHATBOL_ML with WhatsApp.md`
- `docs/proyecto/historial_y_evaluacion.md`
- `docs/auditorias/fase11/TESIS_INSTRUMENTOS_DATA_MAPPING.md`
- `docs/auditorias/fase11/FASE11_5_THESIS_DATA_AUDIT.md`
- `docs/auditorias/fase11/FASE11_5_REPORTE_FINAL.md`

## Matriz de evidencia

| N° | Campo candidato | Documento fuente | Texto/evidencia encontrada | Estado |
|----|-----------------|------------------|----------------------------|--------|
| 1 | Código de registro | `Anexo_2_3_Instrumentos_validacion_CORREGIDO.docx`, Instrumento 1, sección E | En la tabla "E. Registro de síntomas y diagnósticos" aparece como primer campo obligatorio: "Código de registro". | CONFIRMADO_DOCUMENTALMENTE |
| 2 | Fecha de atención | `Anexo_2_3_Instrumentos_validacion_CORREGIDO.docx`, Instrumento 1, sección E | La misma tabla enumera "Fecha de atención" como campo obligatorio. | CONFIRMADO_DOCUMENTALMENTE |
| 3 | Datos generales del vehículo | `Anexo_2_3_Instrumentos_validacion_CORREGIDO.docx`, Instrumento 1, sección E | La tabla de completitud exige "Datos generales del vehículo". La sección B del instrumento detalla marca, modelo, año, kilometraje, combustible y transmisión. | CONFIRMADO_DOCUMENTALMENTE |
| 4 | Síntomas reportados | `Anexo_2_3_Instrumentos_validacion_CORREGIDO.docx`, Instrumento 1, sección E | La tabla de completitud incluye "Síntomas reportados"; la sección C indica marcar síntomas reportados durante la atención. | CONFIRMADO_DOCUMENTALMENTE |
| 5 | Descripción del síntoma | `Anexo_2_3_Instrumentos_validacion_CORREGIDO.docx`, Instrumento 1, sección E | La tabla de completitud incluye "Descripción del síntoma". En la sección C aparece "Descripción breve del síntoma reportado por el cliente". | CONFIRMADO_DOCUMENTALMENTE |
| 6 | Sistema afectado probable | `Anexo_2_3_Instrumentos_validacion_CORREGIDO.docx`, Instrumento 1, secciones D y E | En diagnóstico vehicular se solicita "Sistema afectado probable" y la tabla de completitud lo repite como obligatorio. | CONFIRMADO_DOCUMENTALMENTE |
| 7 | Diagnóstico confirmado por el mecánico | `Anexo_2_3_Instrumentos_validacion_CORREGIDO.docx`, Instrumento 1, secciones D y E | La sección D registra el diagnóstico confirmado y la sección E lo exige como campo obligatorio. | CONFIRMADO_DOCUMENTALMENTE |
| 8 | Tiempo de atención registrado | `Anexo_2_3_Instrumentos_validacion_CORREGIDO.docx`, Instrumento 1, secciones E y F | La sección E exige "Tiempo de atención registrado"; la sección F registra hora de inicio, hora de término y tiempo total. | CONFIRMADO_DOCUMENTALMENTE |

## Resultado documental

**DEFINICION_8_CAMPOS_CONFIRMADA**

La definición oficial no corresponde a la propuesta técnica provisional de Fase 11.5. La fuente metodológica prioritaria es el Anexo 2 corregido, que sí enumera los 8 campos obligatorios de la Ficha 2.

## Regla metodológica aplicable

- 8/8 campos completos -> `campos_completos = 1`
- 7/8 o menos -> `campos_completos = 0`
- `RDC = SUM(campos_completos) / COUNT(registros_evaluados) x 100`
- La regla aplica igual a `THESIS_PRETEST` y `THESIS_POSTTEST`.
- `DEVELOPMENT` y `REGRESSION` quedan excluidos del cálculo oficial.
