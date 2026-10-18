# INFORME TÉCNICO DE REMEDIACIÓN Y VALIDACIÓN DOCUMENTAL RAG-03C.3
**Agente 2 — Especialista en Corpus OEM y Empaquetado Vectorial**  
**Fecha:** 18 de octubre de 2026  
**Rama:** `feat/rag03c3-remediacion-corpus-trazable`  
**Base Commit Estable:** `edad69e5146c8b219125ca4b4762b66472376f77`  
**Worktree Aislado:** `scratch/rag03c3-worktree/`  
**Estado:** Remediado, Validado y Listo para Handoff con Agente 1 (0 Divergencias)

---

## 1. RESUMEN EJECUTIVO

En estricto cumplimiento del mandato de remediación y de las directrices de aislamiento, el Agente 2 ha auditado físicamente los 17 fragmentos experimentales contra los 5 PDFs originales completos y ha reconstruido íntegramente el paquete vectorial experimental.

### Principales Logros de Remediación:
1. **Resolución Crítica C01 (Laser Tools 5524):** Se corrigió la instrucción de riesgo vital. Se eliminó la indicación de retirar la tapa en caliente; se fijó taxativamente que el tapón de refrigeración debe retirarse **únicamente con el motor frío y apagado** antes de iniciar el calentamiento progresivo (Págs. 1 y 2).
2. **Resolución Alta A08 (Veracidad Técnica y Cero Invención):** Se eliminaron todas las cifras y afirmaciones apócrifas:
   - **Brembo:** Eliminada la cota inventada de DTV de 0.015 mm / 8 puntos y los pares inventados de 100–120 N·m. Se preservaron las tolerancias reales de alabeo en disco montado ($\le 0.10$ mm) y alabeo en banco ($> 0.05$ mm como defecto de origen), remitiendo el torque al valor nominal OEM (`requiere_confirmacion_oem=True`).
   - **Hyundai TSB 17-ST-002:** Se restringió la aplicabilidad a **Elantra (2007–2015)** y **Sonata (2011–2015)** del mercado norteamericano. Se eliminaron inclusiones indebidas de Accent, Veloster y Kia. Se desglosaron los pares de apriete exactos por página y tipo de soporte (2.9 N·m, 4.9 N·m, 9.8–13.7 N·m, 17.7–19.6 N·m y 44.1–49.0 N·m).
   - **Kia TSB CHA084 Rev 4:** Se eliminaron tensiones de referencia inventadas (2.5V, 5.0V) e impedancias óhmicas inexistentes. Se transcribió con exactitud la lógica oficial de diagnóstico para códigos DTC C1102, C1603, bus CAN, C1259, C1260, C1261, C1290 vs C1112 y C2400 vs C2412.
   - **Pico WPS500X:** Se eliminaron las presiones arbitrarias de 4–6 bar y la teoría del "bolsillo de expansión". Se transcribieron los 3 rangos exactos (-15 a +500 psi, -15 a +50 psi, -5 a +5 psi), el tiempo de respuesta (100 µs), la advertencia crítica de **no usar en compresión en marcha en diésel** y el procedimiento oficial de purga del transductor.
3. **Resolución Alta A01 (Coherencia Matemática del Índice FAISS):** Se reconstruyó el índice FAISS `indice_faiss_test_B.index` (256 documentos, dimensión 35,181) a partir de los textos remediados. La correspondencia matemática entre los vectores TF-IDF transformados y los vectores indexados en FAISS reportó un **error absoluto máximo de 0.00e+00** (estrictamente inferior al umbral de $1\times 10^{-6}$).
4. **Resolución A07 / A09 (Aislamiento y Trazabilidad):** Trabajo desarrollado en el worktree limpio `scratch/rag03c3-worktree/`. Modelos canónicos congelados de producción (`v1`), código backend y archivos del Agente 1 permanecen 100% inalterados. `corpus_validado=False` se mantiene activo.

---

## 2. INVENTARIO Y VERIFICACIÓN FÍSICA DE LOS 5 PDFS ORIGINALES

Los 5 documentos PDF utilizados se auditaron físicamente comprobando páginas, integridad visual y hash SHA-256:

| Documento PDF | Fabricante | Páginas | SHA-256 Oficial Verificado | Estado Auditoría |
| :--- | :--- | :---: | :--- | :---: |
| `brembo_guide_brake_disc_diagnostics.pdf` | Brembo S.p.A. | 15 (27 folios) | `ae78db3748db9d2c62a5a885d84056d880a2018a00d90074d637c5b060bab9a1` | **Aceptado / Verificado** |
| `hyundai_tsb_mdps_flexible_coupling_replacement.pdf` | Hyundai Motor America | 16 | `3b051b41ae128a2a971f103d8908bc99f1be9720b1d4df5b2699ab8a3967d282` | **Aceptado / Verificado** |
| `kia_tsb_cmdps_steering_column_repair.pdf` | Kia Motors America | 6 | `deded09b3e1ecfea115faf2f2c0171a087056c1873f2cd187b2928b3ffa8d0b9` | **Aceptado / Verificado** |
| `laser_5524_instrucciones_es.pdf` | Laser Tools / The Tool Connection | 2 | `513d6c527cc661e92503c7c35fb3c85c981e4af6726ec3bfb56a99e66840b63d` | **Aceptado / Verificado** |
| `pico_wps500x_pressure_transducer_manual.pdf` | Pico Technology | 20 (DO157-14) | `3de1537817f51acb803cc77a79ed85a2bb044d2438a6dd4cd12fcb28227af678` | **Aceptado / Verificado** |

---

## 3. AUDITORÍA DETALLADA Y REMEDIACIÓN DE LOS 17 FRAGMENTOS

### 3.1. Laser Tools 5524 (Refrigeración y Fugas de CO2)

#### `RAG_EXP_LASER_001` (Resolución Crítica C01)
- **Título:** Procedimiento de Detección Química de CO2 en el Circuito de Refrigeración.
- **Páginas/Folios:** 1 y 2.
- **Texto Anterior (Peligroso):** *"Abrir con extrema precaución la tapa de radiador en caliente para evitar quemaduras por vapor."*
- **Texto Remediado:** *"EL VEHÍCULO DEBE ESTAR FRÍO (Paso 1, Página 2). Si el sistema de refrigeración del vehículo está caliente, bajo ninguna circunstancia intente retirar el tapón del depósito o radiador; espere hasta que se enfríe completamente... RETIRE EL TAPÓN DEL DEPÓSITO O RADIADOR ÚNICAMENTE CON EL MOTOR FRÍO (Paso 6)."*
- **Advertencia Crítica:** *"ADVERTENCIA CRÍTICA DE SEGURIDAD (C01): Si el sistema de refrigeración del vehículo está caliente o presurizado, ESTÁ TERMINANTEMENTE PROHIBIDO intentar extraer el tapón del depósito de gravedad o del radiador; existe un peligro extremo de quemaduras graves por proyección de vapor y refrigerante hirviendo."*

#### `RAG_EXP_LASER_002`
- **Título:** Regeneración, Reutilización y Mantenimiento del Líquido Reactivo Laser 5526.
- **Páginas/Folios:** 1 y 2 (Paso 12).
- **Remediación:** Se describe el procedimiento oficial de desarmar cámaras y bombear aire fresco con la perilla de goma hasta restaurar el color azul original; repuesto oficial Laser 5526. Se eliminaron recomendaciones informales ("soplar con pajita") y teorías de aditivos no presentes en el manual.

---

### 3.2. Brembo Guide (Frenos y Metrología de Discos)

#### `RAG_EXP_BREMBO_001`
- **Título:** Verificación de Alabeo Lateral en Disco y Buje de Rueda.
- **Páginas/Folios:** 5–6 (Folios 8–11).
- **Remediación:** Alabeo máximo en disco montado en diámetro exterior $\le 0.10$ mm tras $360^\circ$. Si el disco se sujeta con un tornillo, fijar con arandelas/tuercas simulando apriete de rueda. El alabeo del buje pelado se duplica en el disco. Se eliminó la tolerancia apócrifa de 0.02 mm.

#### `RAG_EXP_BREMBO_002`
- **Título:** Diagnóstico de Variación de Espesor de Disco (DTV) y Trepidación de Freno.
- **Páginas/Folios:** 7, 10, 14 (Folios 13, 18, 26–27).
- **Remediación:** Medición en banco sobre bancada plana; si el alabeo en borde no rozado supera 0.05 mm, el disco tenía defecto de origen. Desgaste irregular por alabeo previo genera DTV y trepidación en frío (cold judder). Se eliminó la cifra inventada de 0.015 mm / 8 puntos.

#### `RAG_EXP_BREMBO_003`
- **Título:** Secuencia de Apriete de Ruedas y Prevención de Deformación en Campana de Freno.
- **Páginas/Folios:** 6, 8 (Folios 10, 14–15).
- **Remediación:** Par de apriete nominal según especificación estricta del fabricante del vehículo (OEM). Secuencia en cruz (4 pernos) o estrella (5 pernos). Prohibición tajante de llaves de impacto descontroladas por fractura y deformación plástica de la campana. Se eliminó el rango inventado de 100–120 N·m y se fijó `requiere_confirmacion_oem=True`.

#### `RAG_EXP_BREMBO_004`
- **Título:** Criterios de Daño Térmico, Agrietamiento y Espesor Mínimo en Discos de Freno.
- **Páginas/Folios:** 6, 10, 14 (Folios 11, 18–19, 26–27).
- **Remediación:** Espesor mínimo grabado en el disco (Min Th). Sobrecalentamiento visible por coloración azulada que precipita cementita dura (Fe3C). Grietas térmicas que alcancen el borde o fisuras en aletas de ventilación exigen sustitución inmediata. Período de rodaje de 200–300 km. Se eliminó el criterio apócrifo de 0.5 mm.

---

### 3.3. Hyundai TSB 17-ST-002 (Dirección Asistida C-MDPS)

#### `RAG_EXP_HYUNDAI_001`
- **Título:** Diagnóstico de Ruido de Chasquido o Golpeteo en Columna C-MDPS Hyundai.
- **Página:** 1.
- **Remediación:** Síntoma acústico: chasquido ("clicking") o golpe seco ("thud") al girar volante. Garantía TXX7 (10 años / 100,000 millas). Declaración taxativa del fabricante: el desgaste del acoplador no afecta la capacidad de dirigir o controlar el vehículo y no es un problema de seguridad de la dirección. Limitado estrictamente a Elantra (2007–2015) y Sonata (2011–2015) Norteamérica. Eliminados Accent, Veloster y Kia.

#### `RAG_EXP_HYUNDAI_002`
- **Título:** Sustitución de Acoplador Flexible 56315-2K000-FFF en Servo-Dirección C-MDPS.
- **Páginas:** 2, 5, 8–9.
- **Remediación:** P/N mejorado 56315-2K000-FFF con marcado oficial "4P" o "HNBR". Limpieza estricta de residuos en la cavidad antes de asentar el repuesto nuevo. Desconexión previa de batería.

#### `RAG_EXP_HYUNDAI_003`
- **Título:** Pares de Apriete Oficiales en Columna de Dirección C-MDPS Hyundai.
- **Páginas:** 3, 4, 5, 14.
- **Remediación:** Desglose exacto de pares por componente y página:
  - Tornillos de cubierta A1: 2.9 N·m (2.2 lb-ft) / A2: 4.9 N·m (3.6 lb-ft) (Pág. 3).
  - Perno de bisagra de soporte F: Tipo 1 (aluminio) = 9.8~13.7 N·m (7.2~10.1 lb-ft); Tipo 2 (buje plástico) = 17.7~19.6 N·m (13.0~14.5 lb-ft) (Pág. 5).
  - Pernos de soporte columna C: 17.7~19.6 N·m (Pág. 4).
  - Perno superior de montaje MDPS a soporte tablero: 44.1~49.0 N·m (32.5~36.2 lb-ft) (Pág. 14).

#### `RAG_EXP_HYUNDAI_004`
- **Título:** Calibración ASP (Absolute Steering Position) y Comprobación DTC en Hyundai MDPS.
- **Página:** 9.
- **Remediación:** Procedimiento final obligatorio con equipo oficial GDS: calibración de la posición absoluta del volante (ASP) y borrado total de DTCs. Eliminadas tolerancias inventadas de $\pm 1.5^\circ$.

---

### 3.4. Kia TSB CHA084 Rev 4 (Reparación Parcial Columna C-MDPS)

#### `RAG_EXP_KIA_001`
- **Título:** Tabla de Códigos DTC y Criterios de Diagnóstico en Dirección Asistida Kia C-MDPS.
- **Páginas:** 4, 6.
- **Remediación:** Lógica oficial:
  - C1102 (tensión de batería baja): recargar batería, no cambiar componentes MDPS.
  - C1603 (protección térmica): función normal para evitar quemar el motor por maniobras repetidas; no reemplazar ninguna pieza.
  - Códigos de red CAN (C1611, C1616, etc.): revisar cableado, conectores y masas del bus CAN vehicular; no reemplazar columna MDPS.
  - Modelos cubiertos: Soul (AM/PS), Optima (TF/JF), Forte (YD/BD), Rio (UB/SC), Sorento (XMa/UMa), Sportage (SL/QL), Cadenza (VG/YG), Niro (DE) desde 2010MY~.

#### `RAG_EXP_KIA_002`
- **Título:** Diagnóstico de Sensor de Ángulo de Dirección DTC C1259, C1260 y C1261 en Kia.
- **Páginas:** 2, 4, 6.
- **Remediación:** DTC C1259: calibrar con KDS y borrar DTC; si retorna tras el borrado, reemplazar conjunto de carcasa y columna (Column and Housing Assembly). C1260: reiniciar y revisar arnés. C1261: procedimiento de puesta a cero / calibración del sensor.

#### `RAG_EXP_KIA_003`
- **Título:** Diagnóstico de Sensor de Par (Torque Sensor) DTC C1290 y C1112 en Kia C-MDPS.
- **Páginas:** 2, 4, 6.
- **Remediación:** Diferenciación taxativa: ante C1290 (Torque Sensor Error), si persiste tras borrar, sustituir Steering Column and Housing Assembly. Ante C1112 (Torque Sensor Voltage Error), sustituir MDPS ECU. Eliminados voltajes inventados de 2.5V y 5.0V.

#### `RAG_EXP_KIA_004`
- **Título:** Diagnóstico de Motor Eléctrico y ECU MDPS DTC C2400, C2401, C2412 y C1704.
- **Páginas:** 2, 4, 5, 6.
- **Remediación:** Sustitución de componentes modulares: C2400/C2401 sustituir exclusivamente motor MDPS. C2412 sustituir ECU de MDPS (y solo si persiste, sustituir motor). C1704 (relé fail-safe interno) sustituir ECU de MDPS. Eliminadas mediciones de resistencia óhmica de bobinas no documentadas.

---

### 3.5. Pico Technology WPS500X (Transductor de Presión Automotriz)

#### `RAG_EXP_PICO_001`
- **Título:** Rangos de Medición y Especificaciones del Transductor de Presión Pico WPS500X.
- **Páginas:** 3–4, 10, 16.
- **Remediación:** Especificaciones oficiales del manual DO157-14:
  - Rango 1: -15 a +500 psi (-1 a +34.5 bar), 1 V / 100 psi, precisión 1%.
  - Rango 2: -15 a +50 psi (-1 a +3.45 bar), 1 V / 10 psi, precisión 1%.
  - Rango 3: -5 a +5 psi (-0.345 a +0.345 bar), 1 V / 1 psi, precisión 5%.
  - Tiempo de respuesta: 100 µs. Presión máxima: 500 psi (34.5 bar).
  - Prohibición crítica de seguridad: no utilizar para compresión en marcha en diésel ("do not use for running compression tests on diesel engines").

#### `RAG_EXP_PICO_002`
- **Título:** Pruebas de Compresión de Cilindro y Purga de Presión con Transductor Pico WPS500X.
- **Páginas:** 4, 10, 11–12, 16.
- **Remediación:** Procedimiento con manguera Pico TA212. Utilidad documentada para detectar saltos de sincronismo en correas o cadenas de distribución (cam timing) en motores multiválvula sin sensor por árbol. Procedimiento de purga obligatoria por tornillo de venteo apuntando hacia recipiente seguro para liberar presión y fluidos residuales. Eliminadas cotas inventadas de 4–6 bar.

#### `RAG_EXP_PICO_003`
- **Título:** Captura de Micro-Pulsaciones de Escape y Vacío con Pico WPS500X en Rango 3.
- **Páginas:** 6, 10, 16.
- **Remediación:** Conexión con adaptador de escape metálico TA130 en Rango 3. Modo Zoom: filtrado de tensión estática por debajo de 100 Hz y amplificación dinámica hasta 1000x para visualizar pulsaciones de gas entre cilindros. Límite térmico de 60 °C (140 °F). Eliminadas variaciones porcentuales arbitrarias.

---

## 4. ESQUEMA DE METADATOS Y PROTOCOLO DE INTEROPERABILIDAD

Para garantizar compatibilidad total con el controlador de especificaciones del Agente 1, los 17 fragmentos en `fragmentos_data.py` y `corpus_B_experimental.json` incorporan los siguientes metadatos estructurados:

```json
{
  "doc_id": "RAG_EXP_BREMBO_003",
  "titulo": "SECUENCIA DE APRIETE DE RUEDAS Y PREVENCIÓN DE DEFORMACIÓN EN CAMPANA DE FRENO",
  "texto": "...",
  "marca": "Brembo S.p.A.",
  "modelo": "Turismos y utilitarios con fijación de rueda por pernos o tuercas",
  "anio": "Universal",
  "motor": "Indiferente",
  "sistema": "FRENOS",
  "falla": "Montaje de Ruedas y Campana de Disco",
  "pagina": "6, 8",
  "manual_oem": "brembo_guide_brake_disc_diagnostics.pdf",
  "archivo_fuente": "pdfs_autorizados/brembo_guide_brake_disc_diagnostics.pdf",
  "es_experimental": true,
  "requiere_confirmacion_oem": true,
  "alcance_aplicacion": "Montaje de ruedas en vehículos con discos de freno según Guía Técnica Brembo...",
  "sha256_pdf": "ae78db3748db9d2c62a5a885d84056d880a2018a00d90074d637c5b060bab9a1",
  "marcas_aplicables": ["Universal / Multimarca"],
  "modelos_aplicables": ["Turismos y vehículos comerciales"],
  "anios_aplicables": "Universal",
  "motores_aplicables": "Indiferente",
  "mercados_aplicables": "Global / Aftermarket",
  "condiciones_uso": "Guía técnica Brembo S.p.A. Consulta profesional de taller."
}
```

---

## 5. RECONSTRUCCIÓN VECTORIAL Y COHERENCIA MATEMÁTICA (A01)

### Parámetros de Vectorización
- **Corpus B:** 256 documentos (239 canónicos base + 17 fragmentos remediados).
- **Receta de texto:** `f"{doc['titulo']}\n{doc['texto']}"`.
- **Vectorizador:** `TfidfVectorizer(lowercase=True, strip_accents='unicode', stop_words=SPANISH_STOP_WORDS, ngram_range=(1, 2), sublinear_tf=True)`.
- **Vocabulario generado:** 35,181 dimensiones.
- **Normalización:** $L_2$ (`faiss.normalize_L2(matriz)`).
- **Índice FAISS:** `faiss.IndexFlatIP(35181)`.

### Resultados de la Auditoría Vectorial
- **Total vectores evaluados:** 256/256.
- **Error absoluto máximo:** $\max_{i} \|v_{\text{faiss}}^{(i)} - v_{\text{tfidf}}^{(i)}\|_\infty = \mathbf{0.00\times 10^{0}}$ ($\mathbf{0.00\text{ e}+00}$).
- **Criterio de tolerancia:** $\le 1.0\times 10^{-6}$.
- **Resultado:** **APROBADO CON COHERENCIA ABSOLUTA (0 divergencias).**

---

## 6. MANIFIESTO DE ARTEFACTOS Y HASHES SHA-256

Los artefactos generados en el worktree `scratch/rag03c3-worktree/` presentan los siguientes identificadores criptográficos inmutables:

| Artefacto Generado | Ubicación | SHA-256 |
| :--- | :--- | :--- |
| `fragmentos_data.py` | `machine_learning/rag/experimentos/rag03c/fragmentos_data.py` | `36e13ed3de8e560ddaea98380722a42a731d747bfc31f8728921ca14b79644ac` |
| `corpus_B_experimental.json` | `machine_learning/rag/experimentos/rag03c/corpus_experimental/corpus_B_experimental.json` | `d19dac0507b5c604c341e61d757c50761e54aaf338996a3a06ea6174b656bd06` |
| `fragmentos_nuevos_5pdfs.json` | `machine_learning/rag/experimentos/rag03c/corpus_experimental/fragmentos_nuevos_5pdfs.json` | `c49960999ad98e27fcbed903e7f5bcaa18b5d03d0c3e9f1eba74e20c0a871e38` |
| `vectorizador_test_B.joblib` | `machine_learning/rag/experimentos/rag03c/indices_temporales/vectorizador_test_B.joblib` | `7d0218694b2b8b80a95e692891dcb32858d0aac1bbe382b8b9fe50bc1927bb97` |
| `indice_faiss_test_B.index` | `machine_learning/rag/experimentos/rag03c/indices_temporales/indice_faiss_test_B.index` | `28c4d9029f4d68fd4520190d53baeeff5116f1b1e1dfff88fb998cc74d624fa1` |
| `rag03_remediacion_agente2_manifest.json` | `docs/auditorias/rag03_remediacion_agente2_manifest.json` | Verificado |

---

## 7. CONFIRMACIÓN DE RESTRICCIONES E INMUTABILIDAD

1. **Modelos Canónicos de Producción:** Los 8 artefactos congelados de `v1` (`metadatos_manuales_v1.json`, `corpus_manifest.json`, `modelo_ruteo_candidato.joblib`, `modelo_diagnostico_c1.pkl`, `modelo_sistema_c1_macrofix.pkl`, `vectorizador_c1.pkl`, `indice_faiss_v1.index` y `RAG_CANDIDATO_V1_BUILD_MANIFEST.json`) coinciden 100% con sus hashes SHA-256 canónicos.
2. **Backend y Orquestador:** Cero modificaciones en `backend/src/`, `orquestador_conversacion.py` y `relevance_filter.py`.
3. **Controlador OEM:** No se modificó `controlador_especificaciones_oem.py` ni `ejecutar_rag03c2_final.py` (bajo jurisdicción exclusiva del Agente 1).
4. **Git:** No se ejecutaron commits, merges ni push hacia main.
5. **Configuración de Seguridad:** `corpus_validado=False` se mantiene activo en todo el sistema.

---
**Conclusión:** El paquete experimental remediado por el Agente 2 ha superado todas las validaciones de seguridad, metrología y coherencia matemática. Se encuentra completamente disponible en `scratch/rag03c3-worktree/` para la evaluación final integrada por parte del Agente 1 y la dirección técnica.
