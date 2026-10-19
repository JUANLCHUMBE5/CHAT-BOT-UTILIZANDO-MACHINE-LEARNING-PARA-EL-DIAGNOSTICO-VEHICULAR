# CASO SINTÉTICO DE DIAGNÓSTICO VALIDADO (PATRÓN TÉCNICO)

> [!WARNING]
> **ESTADO DE AUDITORÍA RAG-03B:** CASO SINTÉTICO / NO VERIFICADO EN CAMPO.
> Este caso fue formulado con fines didácticos integrando tolerancias de manuales de taller.
> No procede de una orden de trabajo de taller individual con telemetría original vinculada.


## 1. Identificacion del Vehiculo
- Marca y Modelo: Nissan Tiida Sedan
- Ano de Fabricacion: 2014
- Motor: 1.6L HR16DE (4 cilindros, 16V DOHC, Inyeccion Secuencial Multipunto MPFI)
- Transmision: Manual de 5 velocidades (RS5F91R)
- Kilometraje: 142,500 km
- Mercado: Peru (Lima Metropolitana, gasolina regular de 90/95 octanos)

## 2. Sintoma Reportado por el Conductor
- Tirones intensos y vacilacion al acelerar bajo carga media-alta (ej. adelantamiento en 2da o 3ra marcha en pendiente entre 2,000 y 3,200 RPM).
- En ralenti y en autopista a velocidad constante y pedal suave, el motor funciona sin tirones perceptibles.
- Testigo Check Engine parpadea de forma intermitente durante el tironeo.

## 3. Pruebas Realizadas y Mediciones
1. Escaneo Electronico OBD-II:
   - DTC Almacenado: P0300 (Fallo de encendido detectado en multiples cilindros).
   - Freeze Frame: 2,180 RPM, carga de motor 82.4%, temperatura refrigerante 88 C, STFT +4.2%, LTFT +3.1%.
2. Sistema de Combustible:
   - Medicion manometrica en riel: 348 kPa (50.5 psi) en ralenti; 346 kPa durante el tironeo en aceleracion.
   - Especificacion FSM Nissan (Seccion EC): ~350 kPa (51 psi). Sistema de combustible nominal conforme.
3. Compresion Mecanica:
   - Cilindro 1: 172 psi | Cilindro 2: 170 psi | Cilindro 3: 168 psi | Cilindro 4: 171 psi.
   - Limite minimo fabricante: 150 psi; dispersion maxima < 15 psi. Mecanica interna conforme.
4. Osciloscopio Automotriz e Inspeccion de Alta Tension:
   - Sonda capacitiva secundaria COP: Cilindros 1, 2 y 4 con tiempo de quemado de 1.45 ms y 3 oscilaciones inductivas.
   - Cilindro 3: Tiempo de quemado anormal de 0.60 ms, perdida total de oscilaciones inductivas y colapso de la tension de arco hacia masa bajo carga.
   - Inspeccion visual: Fisura dielectrica en el capuchon de silicona de la bobina del cilindro 3 con linea de carbon tracking vertical hacia la culata y marca en ceramica de bujia.

## 4. Clasificacion Rigurosa de la Informacion
- Diagnostico Confirmado: Perforacion del aislador de silicona de la bobina COP del cilindro 3 y presencia de pista de carbon que deriva la chispa a la culata bajo alta presion de compresion.
- Hipotesis Tecnica Descartada: Falla de presion de bomba sumergida (descartada por 348 kPa estables) e inyector obstruido (descartado por tiempos de inyeccion simetricos en osciloscopio).
- Experiencia Anecdotica: Reemplazo injustificado de cuerpo de mariposa sugerido por terceros en foros; refutado por medicion de angulo nominal de 2.1 grados en escaner.
- Informacion No Verificada: Sospecha de catalizador tapado; refutado por medicion de contrapresion de escape en 0.4 psi (< 1.5 psi limite admisible).

## 5. Solucion y Verificacion
- Sustitucion de la bobina del cilindro 3 por pieza original y cambio del juego de bujias con apriete a 19.6 Nm.
- Verificacion en carretera con osciloscopio: Cero fallos de encendido, tiempo de quemado de 1.40 ms en todos los cilindros bajo aceleracion exigida.