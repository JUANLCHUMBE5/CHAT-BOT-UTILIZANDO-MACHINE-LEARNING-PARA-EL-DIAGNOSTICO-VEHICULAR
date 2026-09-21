# Vocabulario de Síntomas Reales Extraído de Perú (Indecopi) y NHTSA

**Fecha:** 2026-09-19  
**Objetivo:** Sistematizar las expresiones coloquiales de mecánicos y conductores para robustecer el diccionario de normalización y RAG de CarBot sin inventar datos sintéticos.

---

| Clúster de Síntoma | Frecuencia Documental | Macro-Sistema | Expresiones en Español (Perú/Taller) | Expresiones en Inglés (NHTSA) |
|---|---|---|---|---|
| **SE APAGA** | **55,624** | `MOTOR / ELECTRICO` | se apaga<br>se detiene en marcha<br>se apaga de golpe<br>cortó corriente<br>se apaga en semáforo | stalls<br>stalled<br>died while driving<br>engine died<br>shut off unexpectedly<br>sudden shut down |
| **VIBRA / TIEMBLA** | **14,346** | `FRENOS / SUSPENSION_CHASIS / MOTOR` | vibra<br>tiembla<br>temblor en el volante<br>vibra al frenar<br>tiembla en mínimo<br>sacudida | vibration<br>shaking<br>shudder<br>vibrating<br>shimmy<br>steering wobble |
| **RUIDO / SILBIDO** | **10,072** | `MOTOR / FRENOS / TRANSMISION` | silbido de turbo<br>chillido de frenos<br>ruido a lata<br>cascabeleo<br>golpeteo seco<br>zumbido de rodaje | whining<br>squeal<br>grinding<br>whistle<br>clunk<br>hissing<br>rattling<br>knocking |
| **SOBRECALENTAMIENTO** | **9,244** | `MOTOR` | calienta<br>sobrecalentamiento<br>aguja de temperatura sube<br>hierve el agua<br>bota refrigerante | overheat<br>overheating<br>high coolant temp<br>coolant boiling<br>steam from radiator |
| **TESTIGO ENCENDIDO** | **8,598** | `MOTOR / ELECTRICO / FRENOS` | check engine prendido<br>testigo encendido<br>luz de motor<br>alarma en el tablero | check engine light<br>mil illuminated<br>dtc code stored<br>warning chime |
| **PIERDE POTENCIA** | **7,130** | `MOTOR` | pierde potencia<br>pierde fuerza<br>no tiene fuerza<br>se queda en subida<br>no pasa de 40 km/h<br>modo degradado | loss of power<br>loss of motive power<br>lack of power<br>no power<br>reduced power<br>limp mode |
| **JALONEA** | **3,920** | `MOTOR / TRANSMISION` | jalonea<br>da tirones<br>tironea<br>cabecea<br>da jalones en aceleración | hesitation<br>jerking<br>surging<br>bucking<br>stumble<br>hesitates on acceleration |
| **RALENTÍ INESTABLE** | **2,028** | `MOTOR` | ralentí inestable<br>mínimo disparejo<br>sube y baja revoluciones<br>motor irregular parado | rough idle<br>erratic idle<br>idle hunting<br>idle fluctuation<br>misfire at idle |
| **NO ARRANCA** | **1,874** | `ELECTRICO / MOTOR` | no arranca<br>no enciende<br>no da marcha<br>gira pero no prende<br>se queda mudo<br>clac seco | crank no start<br>won't start<br>will not start<br>no crank<br>starter click<br>dead engine |
| **HUMO** | **1,775** | `MOTOR` | humo negro<br>humo blanco<br>humo azul<br>olor a quemado<br>bota humo por el escape | black smoke<br>white smoke<br>blue smoke<br>smoke from exhaust<br>burning smell |
| **ARRANQUE DIFÍCIL** | **243** | `MOTOR` | arranque prolongado<br>tarda en arrancar<br>demora en encender<br>cuesta prender en frío | hard start<br>extended crank<br>long crank<br>delayed start |
| **DIRECCIÓN DURA** | **160** | `SUSPENSION_CHASIS` | dirección dura<br>timón duro<br>bloqueo de volante<br>pérdida de dirección asistida | stiff steering<br>power steering loss<br>steering locked<br>hard to turn wheel |
| **FALLA AL ACELERAR / BAJO CARGA** | **75** | `MOTOR` | se ahoga al acelerar<br>se chupa en subida<br>no responde al pisar el pedal<br>falla bajo carga | hesitates under load<br>fails to accelerate<br>bogging down<br>choking on acceleration |
| **PEDAL DURO** | **61** | `FRENOS` | pedal de freno duro<br>servofreno no asiste<br>freno como piedra<br>no frena suave | stiff brake pedal<br>hard brake pedal<br>brake pedal won't depress<br>loss of brake assist |
| **CONSUMO ELEVADO** | **28** | `MOTOR` | consume mucha gasolina<br>gasta demasiado combustible<br>rinde pocos kilómetros | poor fuel economy<br>excessive fuel consumption<br>gas mileage dropped |
| **FRENADO IRREGULAR** | **20** | `FRENOS` | pedal pulsa al frenar<br>se va para un lado al frenar<br>pedal esponjoso<br>frena largo | pulsating pedal<br>pulls to one side when braking<br>spongy brake pedal |

---

## Ejemplos Reales Documentados por Clúster

### No arranca
- **Frecuencia identificada:** 1,874 registros.
  - *"THE PARK/RUN VALVE IN THE WINDSHIELD WIPER MOTOR MAY STICK IN THE PARK POSITION. AN OUT OF BALANCE DIMENSION IN THE CYLINDER RESULTED IN AN UNDERSIZED BORE WHICH MAY CAUSE THE PLUN..."*
  - *"THE PARK/RUN VALVE IN THE WINDSHIELD WIPER MOTOR MAY STICK IN THE PARK POSITION. AN OUT OF BALANCE DIMENSION IN THE CYLINDER RESULTED IN AN UNDERSIZED BORE WHICH MAY CAUSE THE PLUN..."*
  - *"THE IGNITION SWITCH IS DEFECTIVE AND CAUSES STARTING DIFFICULTIES. THE ENGINE MAY FAIL TO START WHEN THE IGNITION KEY IS TURNED...."*

### Arranque difícil
- **Frecuencia identificada:** 243 registros.
  - *"NAVISTAR IS RECALLING 24,975 MY 2003 THROUGH 2008 IC BE, CE, HC, AND RE SCHOOL AND COMMERCIAL BUSES AND 2002 THROUGH 2008 INTERNATIONAL 3200 AND 3300 MODEL BUSES MANUFACTURED BETWE..."*
  - *"NAVISTAR IS RECALLING 24,975 MY 2003 THROUGH 2008 IC BE, CE, HC, AND RE SCHOOL AND COMMERCIAL BUSES AND 2002 THROUGH 2008 INTERNATIONAL 3200 AND 3300 MODEL BUSES MANUFACTURED BETWE..."*
  - *"NAVISTAR IS RECALLING 24,975 MY 2003 THROUGH 2008 IC BE, CE, HC, AND RE SCHOOL AND COMMERCIAL BUSES AND 2002 THROUGH 2008 INTERNATIONAL 3200 AND 3300 MODEL BUSES MANUFACTURED BETWE..."*

### Se apaga
- **Frecuencia identificada:** 55,624 registros.
  - *"Se ha constatado mediante un control de calidad, que en casos aislados se podría presentar un mayor desgaste en la cerradura de contacto debido a las vibraciones. Ante el improbabl..."*
  - *"THE "SPOKER WHEELS", INSTALLED ON THE INVOLVED VEHICLES, MAY FAIL IN SERVICE DUE TO CRACKS THAT MAY DEVELOP IN USE. CONTINUED DRIVING WITH A CRACKED WHEEL COULD LEAD TO FAILURE OF ..."*
  - *"THE "SPOKER WHEELS", INSTALLED ON THE INVOLVED VEHICLES, MAY FAIL IN SERVICE DUE TO CRACKS THAT MAY DEVELOP IN USE. CONTINUED DRIVING WITH A CRACKED WHEEL COULD LEAD TO FAILURE OF ..."*

### Pierde potencia
- **Frecuencia identificada:** 7,130 registros.
  - *"THE EXHAUST GAS RECIRCULATION MANIFOLD CORE PLUGS MAY BECOME DISPLACED RESULTING IN A LOSS OF ENGINE VACUUM AND SUBSEQUENT STALLING. THIS WOULD PRODUCE IMMEDIATE ERRATIC ENGINE OPE..."*
  - *"THE EXHAUST GAS RECIRCULATION MANIFOLD CORE PLUGS MAY BECOME DISPLACED RESULTING IN A LOSS OF ENGINE VACUUM AND SUBSEQUENT STALLING. THIS WOULD PRODUCE IMMEDIATE ERRATIC ENGINE OPE..."*
  - *"THE EXHAUST GAS RECIRCULATION MANIFOLD CORE PLUGS MAY BECOME DISPLACED RESULTING IN A LOSS OF ENGINE VACUUM AND SUBSEQUENT STALLING. THIS WOULD PRODUCE IMMEDIATE ERRATIC ENGINE OPE..."*

### Jalonea
- **Frecuencia identificada:** 3,920 registros.
  - *"UNDER EXTREME TEMPERATURE CONDITIONS, THE FUEL SYSTEM PRESSURE RELIEF VALVE WILL CAUSE THE VALVE SPRING SEAT TO DISLODGE AND THE FUEL SUPPLY TO THE CARBURETOR WILL DECREASE. ENGINE..."*
  - *"UNDER EXTREME TEMPERATURE CONDITIONS, THE FUEL SYSTEM PRESSURE RELIEF VALVE WILL CAUSE THE VALVE SPRING SEAT TO DISLODGE AND THE FUEL SUPPLY TO THE CARBURETOR WILL DECREASE. ENGINE..."*
  - *"UNDER CERTAIN CONDITIONS SUCH AS AMBIENT HUMIDITY AND VEHICLE PRE-CONDITIONING BY REPEATED COLD START, AND SHORT TRIP DRIVING CYCLES IN COMBINATION WITH SUB-ZERO TEMPERATURES, THER..."*

### Vibra / tiembla
- **Frecuencia identificada:** 14,346 registros.
  - *"Se ha constatado mediante un control de calidad, que en casos aislados se podría presentar un mayor desgaste en la cerradura de contacto debido a las vibraciones. Ante el improbabl..."*
  - *"THE INVOLVED VEHICLES MAY CONTAIN FRONT PARK/TURN SIGNAL LAMP ASSEMBLIES THAT MAY BE IN NON-COMPLIANCE TO FEDERAL MOTOR VEHICLE SAFETY STANDARD NO. 108, "LAMPS, REFLECTIVE DEVICES ..."*
  - *"ON THE INVOLVED VEHICLES, THE WATER HEATER IS MOUNTED AT THE EXTREME REAR POSITION OF THE MOTORHOME. BECAUSE OF ITS POSITION, VIBRATIONS COULD CAUSE THE COPPER L.P. GAS LINE SUPPLY..."*

### Humo
- **Frecuencia identificada:** 1,775 registros.
  - *"Descarga o choque eléctrico, Fuego, incendio o quemaduras, Lesiones físicas o laceraciones..."*
  - *"Otros..."*
  - *"ON CERTAIN PASSENGER VEHICLES, THE CAMSHAFT POSITION SENSOR MAY MELT RESULTING IN A BURNING SMELL AND VISIBLE SMOKE, WHICH MAY SUBSEQUENTLY LEAD TO THE MELTING OF THE CAMSHAFT COVE..."*

### Ruido / silbido
- **Frecuencia identificada:** 10,072 registros.
  - *"DURING ASSEMBLY THE UPPER STEERING COLUMN SHAFT PINCH BOLT MAY NOT HAVE BEEN SUFFICIENTLY TIGHTENED. MOVEMENT MAY OCCUR BETWEEN THE UPPER STEERING SHAFT AND THE YOKE, CAUSING ACCEL..."*
  - *"DURING ASSEMBLY THE UPPER STEERING COLUMN SHAFT PINCH BOLT MAY NOT HAVE BEEN SUFFICIENTLY TIGHTENED. MOVEMENT MAY OCCUR BETWEEN THE UPPER STEERING SHAFT AND THE YOKE, CAUSING ACCEL..."*
  - *"DURING ASSEMBLY THE UPPER STEERING COLUMN SHAFT PINCH BOLT MAY NOT HAVE BEEN SUFFICIENTLY TIGHTENED. MOVEMENT MAY OCCUR BETWEEN THE UPPER STEERING SHAFT AND THE YOKE, CAUSING ACCEL..."*

### Sobrecalentamiento
- **Frecuencia identificada:** 9,244 registros.
  - *"THE INVOLVED VEHICLES ARE EQUIPPED WITH AIR CONDITIONING UNITS WHICH CONTAIN BLOWER MOTOR RESISTOR WIRES WHICH ARE IMPROPERLY POSITIONED. AS A RESULT, UNDER CERTAIN CONDITIONS THE ..."*
  - *"THE INVOLVED VEHICLES ARE EQUIPPED WITH AIR CONDITIONING UNITS WHICH CONTAIN BLOWER MOTOR RESISTOR WIRES WHICH ARE IMPROPERLY POSITIONED. AS A RESULT, UNDER CERTAIN CONDITIONS THE ..."*
  - *"THE INVOLVED FURNACES CONTAIN AN ELECTRICAL TRANSFORMER, WHICH IS A COMPONENT PART OF A FURNACE ELECTRICAL POWER CONVERTER, THAT MAY OVERHEAT AND FAIL. THIS FAILURE CAN CAUSE THE T..."*

### Falla al acelerar / bajo carga
- **Frecuencia identificada:** 75 registros.
  - *"TRUCK SPUTTERS AND FAILS TO ACCELERATE AT RANDOM DUE TO MOISTURE.  THE CAUSE ACCORDING TO DEALER IS THE DISTRIBUTOR CAP AND ROTOR BUTTON. HAD SEVERAL CLOSE CALLS PULLING OUT INTO T..."*
  - *"OCTOBER 2000 CHECK ENGINE LIGHT ON IMMEDIATELY AFTER REFUELING.  OCCURED ON SATURDAY, CHECKED OWNERS MANUAL, "OK TO DRIVE, HAVE DEALER CHECK".  TOOK TRUCK TO TOWN EAST FORD MONDAY,..."*
  - *"I HAVE A JEEP GRAND CHEROKEE WITH AN AUTOMATIC TRANSMISSION.  THE TRANSMISSION HAS A DEFECTIVE TRANSMISSION CONTROL MODULE.  THE TRANSMISSION LOCKS IN 3RD GEAR GIVING YOU THE FALSE..."*

### Ralentí inestable
- **Frecuencia identificada:** 2,028 registros.
  - *"EXCESSIVE WEAR OF IDLE STABILIZER COULD CAUSE IDLE FLUCTUATIONS...."*
  - *"EXCESSIVE WEAR OF IDLE STABILIZER COULD CAUSE IDLE FLUCTUATIONS...."*
  - *"EXCESSIVE WEAR OF IDLE STABILIZER COULD CAUSE IDLE FLUCTUATIONS...."*

### Consumo elevado
- **Frecuencia identificada:** 28 registros.
  - *"TRANSMISSION WAS REPLACED AT 26378 PROBLEMS CONTINUE. VEHICKLE DOES NOT WANT TO SHIFT INTO SECOND GEAR,WITHOUT REVVING THE ENGINE CAUSING NOT ONLY UNSAFE SHIFTING, BUT POOR FUEL EC..."*
  - *"VEHICLE STALLING INTERMITTENTLY, AT ANY SPEED/ANY TIME. DEALER STATED THIS  WAS DUE TO A FAULTY IGNITION DEVICE. *AK  VEHICLE WILL NOT START WHETHER IT IS IN PARK OR NEUTRAL.  STAR..."*
  - *"THIS APPEARS TO BE A COMMON PROBLEM FOR THE 1994 FORD EXPLORER THAT THE MANUFACTURER WILL NOT ACKNOWLEDGE. I KNOW OF 3 OTHER OWNERS PERSONALLY THAT HAVE THE SAME COINCIDENTAL PROBL..."*

### Pedal duro
- **Frecuencia identificada:** 61 registros.
  - *"SOME OF THE ABS EQUIPPED VEHICLES WERE BUILT WITH AN UNDERSIZED BRAKE RETURN CHECK VALVE. IN INCIDENTS WHERE HARD BRAKE PEDAL EFFORT IS APPLIED ON LOW FRICTION ROAD SURFACES, LIKE ..."*
  - *"SOME OF THE ABS EQUIPPED VEHICLES WERE BUILT WITH AN UNDERSIZED BRAKE RETURN CHECK VALVE. IN INCIDENTS WHERE HARD BRAKE PEDAL EFFORT IS APPLIED ON LOW FRICTION ROAD SURFACES, LIKE ..."*
  - *"General Motors (GM) is recalling certain model year 2011-2012 Chevrolet Cruze vehicles equipped with 1.4L DOHC gasoline turbo engines and 6T40 front wheel drive automatic transmiss..."*

### Dirección dura
- **Frecuencia identificada:** 160 registros.
  - *"A PROTECTIVE BOOT COVERING THE STEERING RACK AND PINION SHAFT CAN COME LOOSE IN EXTREME COLD. WHEN UNPROTECTED, THE RACK SHAFT MAY CORRODE, RESULTING IN HARD OR STIFF STEERING...."*
  - *"VEHICLE DESCRIPTION:  PASSENGER VEHICLES.     A NUT IN THE STEERING GEAR ASSEMBLY WAS NOT PROPERLY TIGHTENED, RESULTING IN SYMPTOMS RANGING FROM STEERING WHEEL VIBRATION TO STIFF S..."*
  - *"VEHICLE DESCRIPTION:  PASSENGER VEHICLES.     A NUT IN THE STEERING GEAR ASSEMBLY WAS NOT PROPERLY TIGHTENED, RESULTING IN SYMPTOMS RANGING FROM STEERING WHEEL VIBRATION TO STIFF S..."*

### Frenado irregular
- **Frecuencia identificada:** 20 registros.
  - *"BRAKES LOCK UP AT 20-35 MPH UNDER NORMAL BREAKING CONDITIONS CAUSING LOSS OF CONTROL. CONSTANT WHINE FROM FRONT LEFT SIDE. FRONT LEFT ROTOR TURNED ONCE DUE TO PULSATING PEDAL. PULS..."*
  - *"VEHICLE SAFETY ISSUE: 2003 CHEVY MALIBU HAS BEEN INTO THE DEALER THREE (3) TIMES FOR BRAKE REPAIRS. FIRST COMPLAINT I WAS TOLD BRAKES NEEDED TO "WEAR IN", CAR ONE (1) WEEK OLD. SEC..."*
  - *"THE BRAKE ROTORS ON MY 2005 SUBARU HAVE WARPED (ALL 4) AT 14,000 MILES PRODUCING A VIOLENT PULSATING PEDAL AND INEFFICIENT BRAKING.  THIS ALONE COULD CAUSE SOME DRIVERS TO ALLOW FO..."*

### Testigo encendido
- **Frecuencia identificada:** 8,598 registros.
  - *"THESE VEHICLES WERE ASSEMBLED WITH A MALFUNCTION ALARM, LIGHTING AND LOCKING (MALL) MODULE THAT CAN CONTAIN A DAMAGED CAPACITOR. IF THE CAPACITOR IS DAMAGED, THE "KEY IN THE IGNITI..."*
  - *"THESE VEHICLES WERE ASSEMBLED WITH A MALFUNCTION ALARM, LIGHTING AND LOCKING (MALL) MODULE THAT CAN CONTAIN A DAMAGED CAPACITOR. IF THE CAPACITOR IS DAMAGED, THE "KEY IN THE IGNITI..."*
  - *"THESE VEHICLES WERE ASSEMBLED WITH A MALFUNCTION ALARM, LIGHTING AND LOCKING (MALL) MODULE THAT CAN CONTAIN A DAMAGED CAPACITOR. IF THE CAPACITOR IS DAMAGED, THE "KEY IN THE IGNITI..."*

