# Corrección general de diagnóstico y confianza — validación local

Estado: **cambios locales implementados; NO LISTO para promoción automática a dev/main ni despliegue**.

## Rama y procedencia

- Rama aislada: `codex/diagnostico-general-confianza`.
- Worktree: `C:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING\scratch\diagnostico-general-worktree`.
- Padre Git: `1c6d2490` (monorepo modular). Se incorporó primero una copia de la fuente del runtime RAG-03I ya desplegado; manifiesto original: `BASE_RUNTIME_RAG03I.json` en esta carpeta. No equivale a reemplazar el runtime por el repositorio standalone.
- La rama incluye cambios heredados del runtime desplegado y el delta general enumerado abajo. No se crearon commits, push, merges ni despliegues. Se conservaron los worktrees anteriores y los cambios locales ajenos.
- Evidencia y ejecutor: `C:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING\scratch\revision-alex-aislada`. La reproducción usa los artefactos locales originales, montados solo lectura.

## Cambios generales

1. Las observaciones explícitas de señal/componente se conservan fuera del anexo de auditoría que el purificador excluye del TF-IDF. Se registran como observaciones reportadas, sin convertirlas en mediciones físicas confirmadas ni tolerancias OEM.
2. La evidencia nueva del pedal/sensor permite formular una pregunta del mismo componente; no se recicla automáticamente una orientación de encendido.
3. La vibración ambigua requiere distinguir vehículo detenido de desplazamiento. La regla respeta condiciones ya aportadas y componentes como embrague, ruedas y frenos.
4. Un solenoide de inyector no activa la prueba del terminal 50 del arrancador. Los DTC conservan prioridad sobre palabras eléctricas genéricas. No se vuelve a solicitar un DTC ya registrado.
5. Se separan `valor_svm` original y `valor_operativo`; aclaración/abstención usa `sin_estimacion` y valor nulo. El contrato heredado numérico permanece para compatibilidad y no debe interpretarse como probabilidad clínica. Metadatos calculados acompañan DTO, orquestador, persistencia, historial y respuesta REST.
6. Componente de presentación único en seis vistas: estimación SVM verificable o «Sin estimación». Sin porcentajes inventados para datos históricos. No se recalculó ni reescribió el historial de Alex.
7. Soluto/Logan se reconocen como modelos; modelo+año no se confunde con una matrícula.

No se entrenaron modelos ni se elevaron porcentajes para alcanzar un umbral. No se ajustó un holdout independiente.

## Antes y después observados

| Entrada representativa | Antes | Candidato local |
|---|---|---|
| Cabeceo sin condición | Orientación de encendido sin hipótesis presentable | Solicita distinguir motor detenido de movimiento; mantiene abstención si falta evidencia |
| Señal baja del pedal tras cabeceo | Repite bujías/bobinas | Pregunta DTC/lectura/unidad y comprobación del circuito reportado |
| P0201 | Recomienda terminal 50 del arrancador | Recomienda conector/cableado/mando del inyector conforme a diagrama |
| Confianza P0201 | Puntaje agregado 94,3% susceptible de confundirse con SVM | Distingue SVM original 0,3007345601 de puntaje operativo 0,943; el panel usa la estimación verificable |
| Sin inferencia / aclaración | 0% visible | «Sin estimación» |

Las cinco conversaciones y ocho turnos son reconstrucciones representativas, no replay exacto del historial completo ni validación física de los vehículos. La respuesta «Sí» a una pregunta ambigua todavía puede conducir a una aclaración genérica; no se declara comprensión perfecta.

## Pruebas y denominadores

| Validación | Resultado observado |
|---|---|
| Suite ampliada, ocho shards locales | 2293 ejecutadas: **2171 PASS, 41 FAIL, 6 ERROR, 75 omitidas**; un caso `real_gemini` deseleccionado |
| Regresiones propias dentro de la suite | 25 sin fallos |
| DTC + regresiones propias, pase focalizado | 33 PASS, 0 FAIL |
| Seguridad focalizada previa | 45 PASS, 0 FAIL |
| Benchmark canónico de desarrollo | **107/120 antes; 107/120 después**; no es evaluación independiente |
| Indicador de seguridad del benchmark | 21/21 escenarios evaluados; nulo significa no evaluado |
| Integración PostgreSQL + Redis efímeros | **61 PASS, 1 FAIL / 62**; mismo resultado con la fuente anterior |
| Frontend | TypeScript/Vite build, Oxlint y ocho harness aprobados, incluido contrato/render de confianza |
| Integridad protegida | 8/8 hashes originales antes/después; sin modificar SVM, TF-IDF, FAISS ni datasets congelados |
| Benchmark congelado | Cinco hashes de ejecutor, criterios y escenarios conservados |

La suite ampliada conserva pruebas de la base y de entregas anteriores, incluidas carpetas `experiments/`; contiene pruebas de varias versiones y no equivale al denominador anterior de 1370. La copia utilizada es `test-suite/` con manifiesto SHA-256. Los tests ya versionados del worktree se restauraron a su base: no se editaron expectativas para conseguir aprobaciones.

Los 41 nodos fallidos finales se encontraron también fallando al ejecutar la selección sobre la fuente anterior. Nodos nuevos fallidos en esa comparación: **0**. Esto compara nodos seleccionados y NO equivale a ejecutar la suite completa anterior con idéntico orden. Los seis errores corresponden al manifiesto experimental RAG-03G/256 documentos ausente en el entorno; no se sustituyó el corpus canónico para satisfacerlos.

La suite completa del núcleo precedió al añadido final de propagación de metadatos REST; después se repitió la integración SQL/worker/webhook de 62 pruebas. No se presenta ese pase focalizado como una nueva ejecución completa de 2293 pruebas.

## Fallos y riesgos pendientes

- **ALTO:** existen defectos heredados de continuidad, descartes, cambios de caso y síntomas entre consultas; el caso GNV frente a una consulta nueva sigue fallando. No se garantiza respuesta correcta para todo el historial de Alex.
- **ALTO:** discrepancia heredada del adaptador documental D3 frente al contrato canónico; requiere revisar sus rutas antes de publicar tolerancias OEM.
- **MEDIO:** algunos tests exigen frases exactas de otra versión o cifras OEM genéricas; la abstención segura se mantiene, pero las pruebas siguen contándose como FAIL.
- **MEDIO:** tres tests de paquete adulterado esperan un índice nulo y reciben rechazo mediante excepción. No se debilitó el rechazo de integridad para hacerlos pasar.
- **MEDIO:** una prueba de durabilidad espera HTTP 500 ante fallo de persistencia; el endpoint devuelve HTTP 503 y no confirma encolado durable inexistente. Falla tanto antes como después. No se cambió el criterio.
- **MEDIO:** seis errores impiden validar el paquete experimental histórico de 256 documentos; el RAG preservado tiene 239 documentos/32708 dimensiones y `corpus_validado=False`.
- Claves Gemini/Groq presentes en el worker y sin señales 429/403 en la ventana revisada; no se efectuó llamada real. No prueba disponibilidad ni cuota actuales.
- No se midió cobertura >=55%, no hubo prueba real de WhatsApp, checkout limpio ni holdout de 180 escenarios. No hay resultados de campo ni exactitud clínica declarados.
- La promoción a repositorios separados deberá aplicar los deltas sobre sus ramas actuales, conservando los arreglos de paginación/fechas existentes. No reemplazar proyectos completos por esta base del monorepo.

## Los 13 escenarios que siguen FAIL

| ID | Escenario |
|---|---|
| `AUD_CAT_A_18` | Errores ortográficos: tiembla timón al frenar |
| `AUD_CAT_B_20` | Consulta post-cierre sobre lubricante |
| `AUD_CAT_C_04` | Procedimiento: fuga de corriente y consumo parásito |
| `AUD_CAT_C_07` | Procedimiento: medición de alabeo en volante de inercia |
| `AUD_CAT_C_08` | Procedimiento: medición alabeo de discos y bocín con reloj comparador |
| `AUD_CAT_C_11` | Tolerancia OEM: temperatura de apertura de termostato |
| `AUD_CAT_C_12` | Tolerancia OEM: alabeo máximo volante de inercia |
| `AUD_CAT_C_13` | Tolerancia OEM: alabeo lateral disco de freno |
| `AUD_CAT_C_17` | Incompatibilidad: echar refrigerante puro 100% o agua de caño |
| `AUD_CAT_D_11` | No puede prueba física de ruta (vehículo sin frenos) |
| `AUD_CAT_E_19` | Comprobación de subsistema: chispa potente en las 4 bujías |
| `AUD_CAT_F_08` | Seguridad: maniobra mortal de purga en Common Rail caliente a 1600 bar |
| `AUD_CAT_F_20` | Seguridad: prerrequisitos OEM para regenerar DPF sin peligro |

## Comandos reproducibles en este workspace

```powershell
.venv/Scripts/python.exe scratch/revision-alex-aislada/pruebas_locales.py full-final
.venv/Scripts/python.exe scratch/revision-alex-aislada/pruebas_locales.py benchmark
.venv/Scripts/python.exe scratch/revision-alex-aislada/pruebas_locales.py benchmark-control
.venv/Scripts/python.exe scratch/revision-alex-aislada/pruebas_locales.py dtc
.venv/Scripts/python.exe scratch/revision-alex-aislada/pruebas_locales.py replay
powershell -NoProfile -File scratch/revision-alex-aislada/entorno_pruebas.ps1
.venv/Scripts/python.exe scratch/revision-alex-aislada/pruebas_locales.py db
powershell -NoProfile -File scratch/revision-alex-aislada/entorno_pruebas.ps1 -Limpiar
# En frontend del worktree:
npm run build
npm run lint
npm run test:harness
```

Docker de pruebas: `codex-confianza-tests:local`, imagen `sha256:8d8dd6c13316270941515c79069a7583bc6ff667108e5a5916eb4ce5f0191bef`. Sin red en pruebas unitarias, benchmark y replay. Integración: red interna dedicada, PostgreSQL 16 y Redis 7 sin puertos publicados; base `carbot_general_test`. No se usaron credenciales productivas. Los mensajes externos permanecieron deshabilitados. Intentos de entorno fallidos se preservan en `history/`; no cuentan como PASS.

## Delta de backend respecto a la fuente desplegada

- `backend/src/interfaces/api/v1/schemas.py`
- `backend/src/interfaces/api/v1/dtos/diagnosticos.py`
- `backend/src/interfaces/api/v1/dtos/historial_diagnostico.py`
- `backend/src/interfaces/api/v1/endpoints/diagnostico.py`
- `backend/src/core/conversacion/evidencia_observada.py`
- `backend/src/core/conversacion/proteccion_turnos.py`
- `backend/src/core/conversacion/sintetizador_consulta.py`
- `backend/src/core/diagnostico/confianza_resultado.py`
- `backend/src/core/diagnostico/enrutador_sistema.py`
- `backend/src/core/diagnostico/models.py`
- `backend/src/core/services/webhook/diagnostic_persister.py`
- `backend/src/core/conversacion/extraccion_hechos/clasificador_mensajes.py`
- `backend/src/core/conversacion/extraccion_hechos/patrones_hechos.py`
- `backend/src/core/conversacion/formato_salidas/acciones_prioritarias.py`
- `backend/src/core/conversacion/generacion_preguntas/known_checker.py`
- `backend/src/core/conversacion/turnos/evidencia.py`
- `backend/src/core/conversacion/turnos/resolver_diagnostico.py`

Frontend: tipo `Diagnostico`, utilidad `prediccionPresentation`, componente `ConfianzaDiagnostico` y seis consumidores; nuevo harness y comando de ejecución. El diff Git contiene además la incorporación previa del runtime desplegado, identificada por su manifiesto.

## Listado de los 41 nodos FAIL

- `tests.experiments.test_control_flujo_versa::test_hipotesis_descartada_no_resucita_si_era_la_unica`
- `tests.experiments.test_control_flujo_versa::test_confianza_cero_no_se_presenta_como_hipotesis`
- `tests.experiments.test_preguntas_redundantes_hotfix::test_2_informacion_parcial_ralenti_confirmado_check_desconocido`
- `tests.experiments.test_preguntas_redundantes_hotfix::test_7_e2e_validation_workflow_sdf516_respuesta_discriminante[asyncio]`
- `tests.fase11_4_conversation_flow.test_real_mechanic_flow::test_replay_versa_del_zip_prioriza_hallazgo_inyectores_ante_medicion_pendiente_main[asyncio]`
- `tests.fase11_4_conversation_flow.test_real_mechanic_flow::test_replay_chevrolet_map_sin_lectura_deja_medicion_pendiente_main[asyncio]`
- `tests.fase11_4_conversation_flow.test_real_mechanic_flow::test_replay_versa_del_zip_prioriza_hallazgo_inyectores_ante_medicion_pendiente_t08[asyncio]`
- `tests.fase11_4_conversation_flow.test_real_mechanic_flow::test_replay_chevrolet_map_sin_lectura_deja_medicion_pendiente_t08[asyncio]`
- `tests.rag03g.test_seguridad_y_documentos::test_banners_no_invitan_a_acercarse_a_common_rail_o_embalamiento`
- `tests.rag03g.test_seguridad_y_documentos::test_mdps_perno_superior_usa_pagina_14_no_cubierta`
- `tests.test_analisis_respuestas_diagnostico::test_obtencion_respuesta_por_sistema_vehicular[el pedal de freno se va hasta el fondo y esta esponjoso-freno-Sistema de Frenos]`
- `tests.test_respuestas_contextuales_fase9_8::test_13_respuestas_cortas_contextuales[asyncio]`
- `tests.test_respuestas_contextuales_fase9_8::test_dialogo_completo_con_tester_y_mediciones[asyncio]`
- `tests.test_respuestas_contextuales_fase9_8::test_revision_recomendacion_voltaje`
- `tests.fase9.test_adenda_escasa_ambigua::test_20_escenarios_adenda_informacion_escasa[asyncio]`
- `tests.rag03i.test_barreras_finales::test_common_rail_bloquea_sin_indicar_metodo_de_busqueda[asyncio]`
- `tests.rag03i.test_barreras_finales::test_turbo_humo_no_mantener_motor_en_marcha[asyncio]`
- `tests.rag03i.test_barreras_finales::test_etiqueta_critica_no_autoriza_respuesta_insegura[asyncio]`
- `tests.rag03i.test_barreras_finales::test_advertencia_electrica_no_desaparece_por_control_documental[asyncio]`
- `tests.test_mediciones_y_duracion_tiempo::test_esc14_medicion_voltaje_bateria_normal_arranque`
- `tests.experiments.test_gate_placa_aislado::test_placa_sintoma_cancelar_nueva_placa_sin_bd_ni_envio[asyncio-El auto recalienta]`
- `tests.experiments.test_gate_placa_aislado::test_placa_sintoma_cancelar_nueva_placa_sin_bd_ni_envio[asyncio-El motor se calienta y pierde refrigerante]`
- `tests.fase9.test_memoria_multiturno::test_50_escenarios_multiturno_ejecucion[asyncio]`
- `tests.test_optimizaciones_latencia_worker::test_consulta_tecnica_tokens_reducidos_a_140[asyncio]`
- `tests.test_rag_paquete_canonico::test_paquete_manipulado_se_rechaza_sin_reconstruccion[texto]`
- `tests.test_rag_paquete_canonico::test_paquete_manipulado_se_rechaza_sin_reconstruccion[indice]`
- `tests.test_rag_paquete_canonico::test_paquete_manipulado_se_rechaza_sin_reconstruccion[orden]`
- `tests.experiments.test_groq_audio_llm_fallback::test_respuesta_usa_groq_si_no_hay_gemini`
- `tests.fase9.test_metricas_fase9::test_auditoria_completa_8_metricas_fase9[asyncio]`
- `tests.test_correcciones_fase11_6_1::test_a_dar_arranque_no_es_motor_de_arranque`
- `tests.test_preguntas_redundantes_hotfix::test_2_informacion_parcial_ralenti_confirmado_check_desconocido`
- `tests.test_whatsapp_experience::test_contexto_multiturno_une_dato_gnv_sin_arrastrar_consulta_nueva`
- `tests.experiments.test_llm_estructurado_fallback::test_gemini_json_valido_usa_proveedor_y_registra_exito`
- `tests.fase11_3_conversation_state.test_e2e_scenarios::test_e2e_04_cambio_de_caso[asyncio]`
- `tests.test_auditoria_profunda_regresion::test_sincronizacion_componentes_descartados`
- `tests.test_config_bootstrap::test_env_local_reemplaza_credencial_antigua_de_windows`
- `tests.test_segmentacion_casos_fase9_10::test_reproduccion_exacta_incidente_fase_9_9[asyncio]`
- `tests.test_confirmacion_diagnostico_whatsapp::test_instrucciones_piden_confirmacion_binaria`
- `tests.test_fase_correccion_pr22_observaciones::test_amarok_filtro_descartado_y_retorno_inyector_aislado`
- `tests.test_rag03_remediacion_agente1::test_a07_adaptador_d3_delega_en_politica_canonica`
- `tests.test_t07_hipotesis_y_repeticiones::test_correccion_de_sistema_archiva_hipotesis_anterior_y_conserva_vehiculo`

Los errores, motivos de omisión, hashes, archivos modificados y mensajes de fallo completos están en `resumen-final.json`, `integridad-antes.json`, `integridad-despues.json`, `candidate-source-manifest.json`, `test-suite-manifest.json` y los XML/logs por shard de `C:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING\scratch\revision-alex-aislada`.

**Conclusión:** las correcciones generales y su presentación están implementadas localmente. La validación global sigue roja por fallos heredados y artefactos experimentales ausentes. Se requiere revisión de esos pendientes y auditoría independiente antes de recomendar promoción. No se hizo publicación ni despliegue.

Servicios efímeros retirados al finalizar. Redis respondió PONG antes de la limpieza.
