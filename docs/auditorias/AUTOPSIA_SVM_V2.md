# Autopsia Forense de Datos Externos V2 y Análisis de Interferencia de Recalls

**Fecha:** 2026-09-19  
**Población Auditada:** 337 registros externos seleccionados en Fase V2  

---

## 1. Distribución del Efecto Estimado en los 337 Registros

| Clasificación del Efecto | Cantidad | Porcentaje | Interpretación Técnica |
|---|---|---|---|
| **`NEUTRAL`** | 154 | 45.7% | Mantuvo desempeño estable sin impacto significativo en precisión ni recall.
| **`BENEFICIAL`** | 122 | 36.2% | Aportó vocabulario electro-mecánico de alta discriminación que mejoró F1 en clases clave.
| **`SUSPECTED_NOISE`** | 43 | 12.8% | Lenguaje administrativo vago de recalls que generó confusión cruzada y degradó F1.
| **`AMBIGUOUS`** | 18 | 5.3% | Solapamiento léxico entre clases afines (e.g. pastillas vs discos; frenos convencionales vs regenerativos).

## 2. Nivel de Especificidad Diagnóstica (Interferencia de Recalls)

| Nivel de Especificidad | Registros | Porcentaje | Política para V2.1 |
|---|---|---|---|
| **`MEDIA_ESPECIFICIDAD`** | 327 | 97.0% | ⚠️ **RESTRINGIDO** (Solo con confianza >= 0.90).
| **`ALTA_ESPECIFICIDAD`** | 10 | 3.0% | ✅ **APROBADO** para V2.1 (Términos de taller inequívocos).

## 3. Análisis Causal: ¿Por qué Mejoraron unas Clases y Empeoraron Otras?

### A. Clases que Mejoraron Contundentemente (Efecto BENEFICIAL):
1. **Motor de arranque o solenoide defectuoso (+0.200 F1):**
   - Se agregaron términos inequívocos como `'solenoide pegado'`, `'carbones gastados'`, `'arrancador'`, `'clac seco'`. El modelo separó limpiamente fallas de arranque de fallas de batería descargada.
2. **Alternador defectuoso o placa de diodos (+0.196 F1):**
   - Los datos externos reforzaron n-grams de voltaje (`'placa de diodos'`, `'bajo voltaje'`, `'alternador'`), eliminando falsos positivos con bornes sulfatados.
3. **Sensor de posición de cigüeñal CKP (+0.182 F1):**
   - Se inyectó terminología técnica precisa (`'sensor ckp'`, `'posicion del cigueñal'`), resolviendo el déficit histórico de la clase.

### B. Clases que Sufrieron Retroceso (Efecto SUSPECTED_NOISE / AMBIGUOUS):
1. **Empaque de culata soplado (-0.283 F1):**
   - Recibió recalls con descripciones genéricas de sobrecalentamiento y fugas de refrigerante que colisionaron con `'Fuga en mangueras de refrigerante o radiador picado'`.
2. **Discos de freno alabeados (-0.140 F1) y Pastillas de freno (-0.044 F1):**
   - Los textos de recalls utilizan expresiones genéricas como `'brake assembly'`, `'rotor and pad inspection'`, difuminando la frontera entre la queja cinemática de alabeo (vibración en pedal) y el desgaste de fricción (chillido).
3. **Frenado regenerativo EV (-0.196 F1):**
   - Textos de recalls sobre software de control de frenos introdujeron tokens de freno genérico en una clase que requiere contexto eléctrico/EV estricto.

## 4. Conclusión y Lineamiento Quirúrgico para V2.1

Para CarBot V2.1 se implementará un **filtro ultraestricto quirúrgico** que:
1. **Elimine el 100% de los registros clasificados como `SUSPECTED_NOISE` y `BAJA_ESPECIFICIDAD`**.
2. **Bloquee la adición de datos en clases con riesgo de solapamiento semántico** (`empaque culata`, `discos alabeados`, `frenado regenerativo`).
3. **Conserve y concentre la expansión exclusivamente en las clases con evidencia `BENEFICIAL`**.
