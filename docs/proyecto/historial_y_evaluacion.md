# Historial y evaluación de CarBot

La sección **Impacto y validación → Tesis y validación** abre la comparación de fichas
con registros guardados por taller. La colección fija de 60 casos del frontend se
conserva en el repositorio, pero ya no alimenta la pantalla ni la exportación de resultados.

## Consulta

- **Comparación pre/post:** muestra PPCF, PRDC y TPRD de todo el período. Presenta
  «Sin datos» cuando falta una fase y conserva diferencias negativas. No afirma
  significancia estadística ni empareja registros por su posición.
- **Consultas del bot:** resumen del período e historial con detalle del diagnóstico,
  predicciones y trazabilidad disponibles. Los filtros de búsqueda y estado afectan
  la lista; el resumen sigue indicando todos los diagnósticos del período.
- Períodos: últimos 7 días, 14 días, todo y rango inclusivo. Las consultas por
  fecha se interpretan en America/Lima.
- Historial: diez registros por página, del más antiguo al más reciente, con
  controles anterior, siguiente, primera y última. Se actualiza cada 30 segundos
  mientras la pestaña está visible y también permite actualización manual.

## Persistencia y cálculo

PostgreSQL aplica filtros, orden estable y LIMIT/OFFSET antes de enviar la página.
Las métricas de las fichas usan agregaciones SQL por fase, independientes de la página.
El modo CSV local conserva los mismos filtros y orden, pero lee el archivo completo.
La exportación autenticada incluye todo el período seleccionado del taller autorizado.

El formulario permite registrar la fecha real del pre-test y diferencia la hipótesis
manual de la predicción del chatbot. El contrato acepta `prediccion_inicial` y mantiene
compatibilidad con `chatbot_prediccion` en los registros existentes. No precarga
vehículo, tiempo, acierto ni completitud como resultados favorables.

El guardado de consultas del bot permanece en su flujo existente. Una consulta
guardada no se convierte automáticamente en un caso evaluado: la falla comprobada,
el tiempo diagnóstico y la completitud requieren revisión del evaluador. Los ocho
campos de la ficha aún deben definirse metodológicamente; PRDC refleja la evaluación
de completitud registrada, no una comprobación automática de ocho campos.

## Verificación

- Backend: `python -m pytest tests/test_validacion_periodo.py -q`.
- Frontend: `npm run verify` (incluye límites de fechas en Lima).
- UI con API simulada: establecer `CARBOT_PLAYWRIGHT` a un módulo Playwright disponible,
  iniciar Vite en el puerto 5175 y ejecutar desde la raíz
  `node frontend/tests/harness/tesis-ui.cjs`. Requiere Edge instalado y la carpeta `tmp/`.
- La verificación de UI no autentica usuarios reales ni escribe en PostgreSQL.

No se requieren nuevas migraciones para estos cambios. Reiniciar la API y actualizar
el frontend desplegado para cargar los contratos y vistas modificados.
