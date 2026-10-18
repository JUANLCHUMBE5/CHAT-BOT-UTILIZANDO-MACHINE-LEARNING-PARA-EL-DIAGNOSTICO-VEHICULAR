# CASO SINTÉTICO DE DIAGNÓSTICO VALIDADO (PATRÓN TÉCNICO)

> [!WARNING]
> **ESTADO DE AUDITORÍA RAG-03B:** CASO SINTÉTICO / NO VERIFICADO EN CAMPO.
> Este caso fue formulado con fines didácticos integrando tolerancias de manuales de taller.
> No procede de una orden de trabajo de taller individual con telemetría original vinculada.


## 1. Identificacion del Vehiculo
- Marca y Modelo: Toyota Corolla Sedan
- Ano de Fabricacion: 2015
- Motor: 1.8L 2ZR-FE (4 cilindros, 16V DOHC Dual VVT-i)
- Transmision: Automatica Continuamente Variable CVT (K311 / K313)
- Kilometraje: 118,400 km
- Mercado: Peru (Lima Urbana y Panamericana Sur)

## 2. Sintoma Reportado por el Conductor
- Trepidacion o vibracion leve (sensacion de serrucho / judder) al acelerar suavemente entre 20 y 45 km/h.
- Al acelerar a fondo o por encima de 60 km/h la transmision opera con suavidad.
- No hay codigo de error ni aviso en el tablero.

## 3. Pruebas Realizadas y Mediciones
1. Escaneo Electronico y Calibracion TCM:
   - Cero DTCs en ECM/TCM.
   - Version de software de transmision: Calibracion de fabrica original 312G8000.
   - Correspondencia oficial: Campanya Especial Toyota SSC JSD (Special Service Campaign JSD: Continuously Variable Transaxle Software Update).
2. Analisis de Datos en Vivo con GTS/Techstream:
   - Presion hidraulica secundaria en aceleracion suave (30 km/h): Oscilaciones de +-0.3 MPa alrededor de consigna, provocando micropatinamiento de la correa metalica en la polea.
3. Inspeccion del Fluido de Transmision:
   - Verificacion de nivel por rebose a 40 C: Nivel correcto, fluido oscurecido sin olor a quemado ni particulas mayores en bandeja.

## 4. Clasificacion Rigurosa de la Informacion
- Diagnostico Confirmado: Presion hidraulica de amarre insuficiente en poleas CVT a baja velocidad por logica de software de fabrica corregida por la campanya SSC JSD, sumada a degradacion del coeficiente de friccion del fluido CVT.
- Hipotesis Tecnica Descartada: Desperfecto del convertidor de par (el micropatinamiento desaparecia al forzar marcha fija secuencial).
- Experiencia Anecdotica: Dictamen de taller externo recomendando cambio de caja por 4,000 USD; innecesario.
- Informacion No Verificada: Falla de soportes de motor o semiejes; verificados sin roturas ni holguras.

## 5. Solucion y Verificacion
- Reprogramacion de software ECM/TCM mediante Techstream GTS segun campanya SSC JSD.
- Reemplazo de fluido con 4.2 L de Toyota Genuine CVT Fluid FE mediante procedimiento termico de nivelacion a 40 C.
- Calibracion de memoria y prueba de 50 km: Desaparicion total de la trepidacion en todas las condiciones de carga.