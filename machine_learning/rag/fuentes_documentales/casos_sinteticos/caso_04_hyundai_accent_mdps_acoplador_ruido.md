# CASO SINTÉTICO DE DIAGNÓSTICO VALIDADO (PATRÓN TÉCNICO)

> [!WARNING]
> **ESTADO DE AUDITORÍA RAG-03B:** CASO SINTÉTICO / NO VERIFICADO EN CAMPO.
> Este caso fue formulado con fines didácticos integrando tolerancias de manuales de taller.
> No procede de una orden de trabajo de taller individual con telemetría original vinculada.


## 1. Identificacion del Vehiculo
- Marca y Modelo: Hyundai Accent Sedan
- Ano de Fabricacion: 2013
- Motor: 1.4L G4FA (4 cilindros, 16V DOHC Gasolina MPI)
- Direccion: Asistida Electricamente en la Columna (C-MDPS)
- Kilometraje: 126,800 km
- Mercado: Peru (Lima y Callao, servicio particular de transporte)

## 2. Sintoma Reportado por el Conductor
- Ruido seco de golpeteo o traqueteo ('clac-clac') en el volante al girar a baja velocidad o en maniobras de estacionamiento.
- Sensacion de holgura o juego muerto angular de varios grados en el volante al circular por calzadas bacheadas o adoquines.
- La asistencia electrica de direccion funciona con normalidad; no hay testigo EPS encendido.

## 3. Pruebas Realizadas y Mediciones
1. Descarte Mecanico del Tren Delantero:
   - Rotulas de suspension inferior, terminales de direccion axiales y exteriores comprobados con reloj comparador: holguras < 0.05 mm (estado optimo).
   - Bieletas de barra estabilizadora y bujes sin juego. Cremallera de direccion firmemente sujeta al subchasis. El ruido proviene del interior del habitaculo.
2. Medicion de Holgura Angular en Volante:
   - Con ruedas trabadas en el suelo, se constata un juego angular libre de 14 grados en el aro del volante antes de notar resistencia de torsion.
3. Desmontaje e Inspeccion del Servomotor MDPS:
   - Siguiendo el boletin tecnico oficial Hyundai TSB 17-ST-001 (TSB 14-ST-002-1), se desmontan los 3 pernos de fijacion del motor de asistencia en la columna.
   - Hallazgo Físico Inobjetable: El acoplador elastico flexible de caucho (fleje con forma de estrella) entre el eje del motor y la columna se encuentra totalmente pulverizado y fragmentado en trozos endurecidos, provocando contacto directo metal contra metal entre los engranajes.

## 4. Clasificacion Rigurosa de la Informacion
- Diagnostico Confirmado: Destruccion por fatiga del acoplador elastico de caucho del motor C-MDPS (defecto documentado en boletines oficiales OEM Hyundai TSB 17-ST-001 y Kia CHA084).
- Hipotesis Tecnica Descartada: Falla de cremallera mecanica o rotula de direccion (descartadas en elevador con mediciones micrometricas).
- Experiencia Anecdotica: Recomendacion de cambiar la columna y motor completos por 1,200 USD por parte de talleres genericos; practica abusiva innecesaria.
- Informacion No Verificada: Sospecha de falla del sensor de par (torque sensor); descartada al verificar senales simetricas de 2.50 V en neutro en escaner sin picos ni saltos.

## 5. Solucion y Verificacion
- Limpieza exhaustiva de restos de elastomero de la carcasa de la columna.
- Instalacion del acoplador flexible reforzado de formulacion HNBR (Numero de Parte Oficial Hyundai/Kia: 56315-2K000-FFF) y apriete a 9.8 Nm.
- Calibracion y puesta a cero del sensor de angulo de direccion (SAS) con escaner.
- Verificacion final: Eliminacion total del ruido y juego angular reducido a cero grados.