# CASO SINTÉTICO DE DIAGNÓSTICO VALIDADO (PATRÓN TÉCNICO)

> [!WARNING]
> **ESTADO DE AUDITORÍA RAG-03B:** CASO SINTÉTICO / NO VERIFICADO EN CAMPO.
> Este caso fue formulado con fines didácticos integrando tolerancias de manuales de taller.
> No procede de una orden de trabajo de taller individual con telemetría original vinculada.


## 1. Identificacion del Vehiculo
- Marca y Modelo: Nissan Sentra Sedan (B17)
- Ano de Fabricacion: 2016
- Motor: 1.8L MRA8DE (4 cilindros, 16V DOHC Inyeccion MPFI)
- Transmision: Automatica Continuamente Variable Jatco CVT7 (RE0F11A / JF015E)
- Kilometraje: 135,000 km
- Mercado: Peru (Lima Metropolitana, trafico denso y alta temperatura ambiental)

## 2. Sintoma Reportado por el Conductor
- Perdida severa de traccion tras frenar en reductores de velocidad o semaforos: al presionar el acelerador, el motor sube a 3,000-4,000 RPM pero el auto apenas avanza lentamente (patinamiento hidraulico masivo).
- Al apagar el motor y esperar 10 minutos, el auto vuelve a avanzar normalmente, pero reproduce el fallo tras 15 minutos en congestionamiento.
- Testigo Check Engine encendido intermitente.

## 3. Pruebas Realizadas y Mediciones
1. Escaneo Electronico del Modulo TCM:
   - DTCs Almacenados: P0746 (Solenoid de control de presion de linea - Rendimiento o atascado desactivado), P0846 (Sensor de presion de polea secundaria - Rango/Rendimiento), P17F0 (CVT Judder - Inspeccion de transmision requerida, conforme a TSB NTB19-060C y NTB20-035C).
2. Medicion Hidraulica con Manometro Físico y Escaner:
   - Presion secundaria en frio: 0.85 MPa (dentro de rango nominal 0.70-1.20 MPa).
   - Presion secundaria a 85 C de temperatura de fluido: Colapsa a 0.25 MPa al intentar salir desde detenido, provocando perdida de amarre de la correa sobre las poleas.
3. Desmontaje e Inspeccion Visual de Bomba de Aceite:
   - Aceite NS-3 drenado con color grisaceo y lodo metalico en los imanes del carter (> 3 mm de sedimento de acero).
   - Al retirar la bomba de aceite, se constata que el embolo de la valvula de control de flujo (flow control valve) presenta rayaduras axiales profundas y se encuentra trabado abierto en el cuerpo de la bomba, fugando la presion de linea al retorno en caliente.

## 4. Clasificacion Rigurosa de la Informacion
- Diagnostico Confirmado: Atascamiento por desgaste y contaminacion metalica de la valvula reguladora de flujo de la bomba de alta presion de la transmision Jatco CVT JF015E.
- Hipotesis Tecnica Descartada: Falla del modulo electronico TCM o solenoides quemados (resistencia medida de 5.2 Ohmios en solenoides, nominal 5.0-5.6 Ohmios).
- Experiencia Anecdotica: Creencia de que 'con un simple cambio de aceite y filtro la caja CVT queda reparada'; refutada porque la fuga hidraulica es por desgaste mecanico de la valvula.
- Informacion No Verificada: Supuesto fallo de sensores de velocidad de poleas; descartado mediante senales de onda cuadrada de 0-5V estables en osciloscopio.

## 5. Solucion y Verificacion
- Reemplazo de la bomba de aceite de la CVT por conjunto con valvula de flujo tratada con recubrimiento antifriccion de alta durabilidad (valvula sobremedida Sonnax).
- Lavado a presion del circuito del enfriador de aceite, cambio de filtro colador de carter y filtro de cartucho externo.
- Llenado con fluido genuino Nissan CVT Fluid NS-3 (7.8 litros) y reseteo del contador de degradacion de aceite en TCM.
- Verificacion manometrica final: Presion secundaria en caliente de 0.95 MPa en ralenti y 3.8 MPa en aceleracion a fondo sin caidas de presion ni codigos de error.