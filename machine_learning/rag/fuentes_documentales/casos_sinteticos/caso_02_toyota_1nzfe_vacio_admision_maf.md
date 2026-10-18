# CASO SINTÉTICO DE DIAGNÓSTICO VALIDADO (PATRÓN TÉCNICO)

> [!WARNING]
> **ESTADO DE AUDITORÍA RAG-03B:** CASO SINTÉTICO / NO VERIFICADO EN CAMPO.
> Este caso fue formulado con fines didácticos integrando tolerancias de manuales de taller.
> No procede de una orden de trabajo de taller individual con telemetría original vinculada.


## 1. Identificacion del Vehiculo
- Marca y Modelo: Toyota Yaris Sedan
- Ano de Fabricacion: 2012
- Motor: 1.5L 1NZ-FE (4 cilindros, 16V DOHC VVT-i Gasolina con conversion dual GLP 5ta generacion)
- Transmision: Manual de 5 velocidades (C150)
- Kilometraje: 178,200 km
- Mercado: Peru (Arequipa / Lima)

## 2. Sintoma Reportado por el Conductor
- Ralenti sumamente inestable y vibracion fuerte al detenerse en semaforos tanto en gasolina como en GLP.
- Calado esporadico del motor al accionar el pedal de embrague al frenar en esquinas.
- Sobre 2,500 RPM el motor responde normalmente y la marcha es suave.
- Luz Check Engine encendida permanentemente.

## 3. Pruebas Realizadas y Mediciones
1. Escaneo Electronico OBD-II:
   - DTC Activo: P0171 (Sistema de combustible demasiado pobre - Banco 1).
   - Parametros en Ralenti (650 RPM): STFT +19.5%, LTFT +23.4% (Compensacion total: +42.9%, umbral DTC > +35%).
   - Flujo de Aire MAF en Ralenti: 1.32 g/s (Especificacion Toyota 1NZ-FE: 1.60 a 2.00 g/s a 650 RPM).
2. Prueba Dinamica de Compensadores a 2,500 RPM:
   - STFT desciende a +2.3%; LTFT desciende a +6.2%.
   - MAF sube a 5.8 g/s.
   - Diagnostico diferencial: La recuperacion de valores normales al aumentar el volumen de aire confirma una entrada de aire no medido (vacio) o suciedad del MAF.
3. Generador de Humo y Medicion de Vacio:
   - Presurizacion a 1.5 psi con humo sintetico: Fuga detectada en la junta del multiple de admision contra la culata en los cilindros 1 y 2.
   - Sonda MAF: Capa de polvo aceitoso sobre el hilo termico (hot wire) por uso de filtro de aire de baja calidad.

## 4. Clasificacion Rigurosa de la Informacion
- Diagnostico Confirmado: Deformacion termica del empaque del multiple de admision (PN 17177-21020) sumado a contaminacion superficial del sensor MAF.
- Hipotesis Tecnica Descartada: Falla de la bomba de gasolina (el defecto persistia identico en GLP) y fuga de gas en inyectores de GLP.
- Experiencia Anecdotica: Creencia popular de que 'el P0171 en autos a gas siempre es culpa de la calibracion del reductor'; descartada por compensadores desfasados en gasolina.
- Informacion No Verificada: Sospecha de valvulas de escape quemadas; refutado con manometro de compresion arrojando 175 psi en los 4 cilindros.

## 5. Solucion y Verificacion
- Sustitucion del empaque de multiple de admision por repuesto genuino y limpieza dieléctrica sin contacto del sensor MAF.
- Reseteo de adaptativos: Ralenti estable a 650 RPM, MAF en 1.80 g/s, STFT entre -1.0% y +2.0%, LTFT en +3.0%. Cero DTCs tras 100 km de prueba.