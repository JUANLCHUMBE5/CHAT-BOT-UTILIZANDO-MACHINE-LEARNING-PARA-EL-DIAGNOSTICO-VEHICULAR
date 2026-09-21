# CHECKLIST DE INICIO Y EJECUCIÓN DE TRABAJO DE CAMPO
**CARBOT — TESIS DE GRADO 2026**  
**Taller Sede:** CARTER MOTOR'S E.I.R.L.  
**Objetivo de Muestra:** 60 Casos Oficiales (30 Pre-test + 30 Post-test)  
**Versión de Software:** CARBOT_PRECAMPO_FROZEN  

---

## 1. ANTES DE INICIAR LA JORNADA DIAGNÓSTICA (VERIFICACIÓN PRE-VUELO)

Marque cada casilla antes de permitir el ingreso del primer vehículo de la sesión experimental:

- [ ] **PostgreSQL operativo:** Servicio PostgreSQL en ejecución local o contenedor accesible en puerto 5432.
- [ ] **Backend operativo:** API FastAPI iniciada y respondiendo satisfactoriamente en `http://localhost:8000/docs` o endpoint de salud.
- [ ] **Frontend operativo:** Panel web React/Vite operativo en navegador web en `http://localhost:5173`.
- [ ] **CarBot responde:** Consulta de prueba de conectividad por WhatsApp o simulador respondiendo oportunamente.
- [ ] **RAG responde:** Búsqueda en índice vectorial FAISS y recuperación de fragmentos OEM validada.
- [ ] **Hashes correctos:** Integridad SHA-256 de los 13 artefactos productivos verificada mediante `scripts/audit_hashes_fase12_3.py` (0 modificaciones).
- [ ] **Entorno correcto:** Verificación de que el selector de entorno en la interfaz de usuario esté en el modo correspondiente (modo `PILOTO` para calibración inicial o `OFICIAL DE TESIS` para recolección formal).
- [ ] **PRE 0/30:** Contador oficial Pre-test en base de datos PostgreSQL validado en cero casos al arrancar la recolección.
- [ ] **POST 0/30:** Contador oficial Post-test en base de datos PostgreSQL validado en cero casos al arrancar la recolección.
- [ ] **Backup realizado:** Copia de seguridad lógica ejecutada sobre PostgreSQL (`pg_dump`) previa a la sesión.
- [ ] **Fecha/hora sistema correctas:** Reloj del servidor sincronizado con zona horaria oficial de Lima, Perú (`America/Lima`, UTC-5).
- [ ] **Ficha accesible:** Formulario digital de recolección de Anexo 2 accesible y verificado en la pantalla del taller.

---

## 2. DURANTE LA ATENCIÓN DIAGNÓSTICA (PROTOCOLO OPERATIVO)

Para cada vehículo ingresado a la bahía de diagnóstico, el observador y el mecánico deben cumplir estrictamente:

- [ ] **Verificar entorno antes de cada registro:** Comprobar visualmente que el badge del modal indique `OFICIAL DE TESIS (N=60)` (o `PILOTO` si es un caso de prueba).
- [ ] **PRE sin CarBot:** En fase Pre-test, el mecánico realiza el diagnóstico tradicional con herramientas convencionales, prohibiendo terminantemente abrir o consultar CarBot.
- [ ] **POST con CarBot:** En fase Post-test, ingresar los síntomas y quejas a CarBot y consultar el reporte estructurado emitido por el clasificador Linear SVM y RAG.
- [ ] **Medir tiempo metodológico:** Iniciar cronómetro al recibir el vehículo y detenerlo al confirmar concluyentemente la avería física, registrando el valor en `tiempo_diagnostico_minutos`.
- [ ] **Registrar evidencia:** Adjuntar código de fotografía, oscilograma, medición con multímetro o informe metrológico en `evidencia_ref`.
- [ ] **Confirmar falla real:** No registrar hipótesis no comprobadas; toda falla debe ser contrastada físicamente en elevador o con instrumental.
- [ ] **No editar predicción CarBot:** La sugerencia diagnóstica emitida por el chatbot se mantiene estrictamente inmutable en el formulario digital (`readOnly`).
- [ ] **No tocar DB manualmente:** Prohibido realizar inserciones, actualizaciones o manipulaciones directas mediante SQL sobre la tabla `validaciones_taller`.

---

## 3. AL FINALIZAR LA JORNADA (CIERRE Y RESGUARDO)

Al concluir el turno de atención en el taller:

- [ ] **Revisar contador:** Verificar en el panel web el avance oficial acumulado (`X/30 Pre-test`, `Y/30 Post-test`, total `Z/60`).
- [ ] **Revisar registros verificados:** Asegurar que todos los casos completados tengan el estado `verificado` y no hayan quedado inadvertidamente como `borrador`.
- [ ] **Backup:** Ejecutar volcado de seguridad de la base de datos con fecha y hora del cierre de jornada.
- [ ] **Export de control:** Descargar el CSV oficial de control mediante `/api/v1/validacion-taller/exportar-fichas-anexo2-csv` para validación de consistencia tabular.
- [ ] **Conservar evidencias:** Archivar ordenadamente los archivos multimedia o informes técnicos de respaldo vinculados a las referencias `evidencia_ref`.
