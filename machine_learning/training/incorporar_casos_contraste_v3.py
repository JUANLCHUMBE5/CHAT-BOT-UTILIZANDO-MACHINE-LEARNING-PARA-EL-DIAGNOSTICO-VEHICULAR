"""
Generador e incorporador de casos dirigidos de contraste V3
para resolver las confusiones detectadas en el Benchmark V2:
1. Caja automática (demora reversa en frío / ATF / solenoides) vs IAC.
2. Compresor de aire neumático (camiones / tanques) vs Compresor A/C.
3. Taqués hidráulicos / cadena distribución fuera de punto vs A/C / Sensor O2.
4. Caliper trabado / rueda caliente / olor balata vs Desalineación.
5. Palier / copa y triceta (trompa sacude al acelerar) vs Discos alabeados.
6. Rodamiento de rueda que modula al virar vs Llantas desbalanceadas.
7. Cremallera de dirección (juego muerto al centro) vs Llantas.
8. Trepidación de embrague al salir en 1ra vs Misfire.
9. Fuga de vacío en servofreno / booster silbido vs IAC.

Regla Estricta: Zero Data Leakage (No copiar los 100 textos del benchmark).
"""

import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))


DATASET_PATH = BASE_DIR / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"

# CASOS NUEVOS DE TALLER DIRIGIDOS POR CONFUSIÓN
NUEVOS_CASOS = []

# 1. Caja automática (demora reversa / golpe frío / nivel ATF) -> TRANSMISION
CASOS_CAJA_AUTOMATICA = [
    "caja automatica demora en acoplar reversa cuando esta fria en las mananas y luego patea al entrar",
    "en frio pongo r en la palanca automatica y tarda varios segundos en enganchar la marcha trasera con sacudida",
    "transmision automatica no engancha retroceso inmediatamente despues de encender, golpea al aplicar r",
    "demora en aplicar reversa con motor frio en transmision automatica luego da un tiron seco",
    "tarda en enganchar reversa en frias mananas transmision automatica hidraulica cuerpo de valvulas sucio",
    "reversa demora en entrar cuando recien arranco en la manana y golpea la caja automatica",
    "caja automatica golpea al meter retroceso cuando el fluido atf todavia esta frio",
    "demora de varios segundos para que enganche reversa en caja automatica de 4 velocidades",
    "caja automatica no aplica retroceso rapido en frio se queda libre y luego entra con golpe brusco",
    "caja de cambios automatica tarda en entrar marcha atras en frio y suelta golpe fuerte",
    "retardo en aplicacion de reversa en transmision automatica por baja presion de atf en frio",
    "tiron al meter retroceso en caja automatica despues de estar estacionado toda la noche",
    "demora en aplicar reversa caja automatica convertidor de par o solenoides pegados en frio",
    "al poner r en caja automatica demora 4 segundos en reaccionar y entra pateando el eje trasero",
    "nivel bajo de fluido atf produce retraso al acoplar retroceso y cambio brusco con sacudida en frio"
]
for c in CASOS_CAJA_AUTOMATICA:
    NUEVOS_CASOS.append((c, "Falta o degradacion de aceite de caja de cambios", "TRA_001", "Transmisión y Embrague", "Alta"))
    NUEVOS_CASOS.append((c + " sintomas de solenoide de retroceso pegado", "Sobrecalentamiento o solenoides en caja automatica CVT / DSG", "TRA_005", "Transmisión y Embrague", "Alta"))

# 2. Compresor de aire neumático (camiones / pulmones de freno) -> CARROCERIA_NEUMATICA
CASOS_COMPRESOR_CAMION = [
    "camion no levanta presion de aire en los tanques y el compresor de piston trabaja sin cortar",
    "compresor de aire de camion trabaja continuo y las agujas de los manometros no suben a 8 bares",
    "compresor neumatico de freno de camion demora mucho tiempo en cargar los tanques principales",
    "camion pesado pierde aire y el compresor de freno neumatico bombea todo el tiempo sin descansar",
    "compresor de aire del sistema de frenos de camion trabaja forzado y no levanta presion de servicio",
    "compresor neumatico de dos pistones de camion sopla aire pero no llena los calderines",
    "demora excesiva en levantar presion en tanques de aire de camion compresor de frenos desgastado",
    "compresor de frenos de aire de camion recalienta por trabajar continuo y no carga los tanques",
    "compresor de aire vehicular de camion no comprime suficiente presion para soltar los frenos de resorte",
    "fuga en circuito neumatico hace que el compresor de aire de camion trabaje constantemente",
    "compresor de aire de frenos de camion de carga bombea continuo y no alcanza presion de descarga",
    "culatin de compresor de aire neumatico de camion con fugas no permite cargar tanques principales",
    "manometro de aire de camion no sube compresor mecanico accionado por engranaje no rinde suficiente caudal",
    "compresor de aire de tractocamion no corta la carga y tarda media hora en inflar el sistema",
    "camion demora demasiado en cargar aire compresor de frenos neumaticos con anillos desgastados"
]
for c in CASOS_COMPRESOR_CAMION:
    NUEVOS_CASOS.append((c, "Fugas de aire o fallos en el sistema de frenos neumático (Camiones)", "NEU_001", "Frenos Neumáticos", "Alta"))
    NUEVOS_CASOS.append((c + " valvula gobernadora y secador no purgan", "Válvula de freno de aire o secador APS obstruido (Camiones)", "NEU_002", "Frenos Neumáticos", "Alta"))

# 3. Faja o cadena de distribución fuera de punto / taqués hidráulicos -> MOTOR
CASOS_DISTRIBUCION_TAQUES = [
    "acaban de cambiar la faja de distribucion y el motor quedo sin fuerza tiembla y tira pedos por escape",
    "despues de cambio de correa de distribucion motor quedo fuera de punto pierde potencia y tironea",
    "faja de distribucion mal sincronizada motor tiembla disparejo explosiones sordas por tubo de escape",
    "cambiaron kit de distribucion y el carro quedo sin pique vibra en ralenti y suena sordo por escape",
    "motor con salto de diente en la faja de tiempo contraexplosiones en multiple y falta de fuerza",
    "distribucion saltada un diente ralenti disparejo y petardeo por el escape al acelerar en vacio",
    "salto de punto en correa de tiempo valvulas desfasadas motor inestable y pedorreo por tubo de escape",
    "despues de cambiar faja de tiempo motor no acelera bien tiembla en minimo y tose por el escape",
    "cambio de cadena de tiempo quedo corrida un diente falta de fuerza y detonaciones sordas en escape",
    "faja de distribucion destensada salto punto de sincronizacion genera temblor y perdida de fuerza",
    "taqueteo metalico rapido arriba en la culata al arrancar en frio que desaparece a los 5 minutos",
    "sonido de taques hidraulicos tac tac tac arriba en la tapa de valvulas en las mananas al prender",
    "en frio suena golpeteo metalico de taques o punterias arriba del motor luego de calentar se silencia",
    "taqueteo de taques arriba en el motor en frio tac tac tac despues de calentar el aceite se quita",
    "ruido de taques descargados en las mananas por baja presion de aceite inicial en culata"
]
for c in CASOS_DISTRIBUCION_TAQUES:
    if "taque" in c:
        NUEVOS_CASOS.append((c, "Baja presion de aceite o bomba de aceite defectuosa", "MOT_010", "Motor", "Media"))
        NUEVOS_CASOS.append((c + " ruido de cadena y taques", "Faja o cadena de distribucion destensada o con salto de punto", "MOT_011", "Motor", "Alta"))
    else:
        NUEVOS_CASOS.append((c, "Faja o cadena de distribucion destensada o con salto de punto", "MOT_011", "Motor", "Alta"))

# 4. Caliper trabado / rueda caliente y jala -> FRENOS
CASOS_CALIPER_TRABADO = [
    "una sola rueda delantera queda hirviendo despues de manejar y el carro se jala hacia ese lado",
    "caliper de freno delantero pegado la llanta calienta muchisimo y despide fuerte olor a balata quemada",
    "mordaza de freno trabada rueda delantera derecha quema al tocar el aro y tira la direccion",
    "embolo o piston de mordaza atascado rueda queda frenada calienta en exceso y auto se desvia",
    "freno delantero pegado llanta echa humo y calienta el aro olor amargo de pastilla de freno chamuscada",
    "caliper atascado en una rueda delantera el vehiculo jala con fuerza hacia la derecha al rodar",
    "pernos guia de mordaza de freno oxidados rueda se queda frenada disco al rojo vivo y aro caliente",
    "rueda delantera se frena sola aro caliente despues de rodar 15 minutos desvio lateral al manejar",
    "piston de caliper no regresa rueda queda frenada se calienta el tambor o disco y jala la direccion",
    "despues de manejar en pista un aro delantero quema al tocarlo y el auto se frena hacia ese costado",
    "olor a pastilla quemada en una rueda delantera y direccion jalando hacia la rueda que frena sola",
    "disco y pastilla de un lado quedan aprisionados rueda hirviendo y sensacion de freno pegado",
    "mordaza pegada rueda derecha ardiendo desvio continuo de carril hacia el lado que calienta",
    "freno pegado en rueda delantera genera calor excesivo en el rin y deriva lateral del volante",
    "caliper trabado presiona pastilla constantemente aro quema y vehiculo tiende a irse hacia ese lado"
]
for c in CASOS_CALIPER_TRABADO:
    NUEVOS_CASOS.append((c, "Desgaste de pastillas y zapatas de freno", "FRE_001", "Frenos", "Alta"))
    NUEVOS_CASOS.append((c + " alabeo en disco por sobrecalentamiento", "Discos de freno alabeados o desgastados", "FRE_002", "Frenos", "Alta"))

# 5. Copa y triceta / palier (trompa sacude al acelerar en 3ra/4ta) -> SUSPENSION_CHASIS
CASOS_COPA_TRICETA = [
    "trompa del carro se sacude de lado a lado solo cuando acelero en tercera o cuarta en pista",
    "vibracion oscilatoria en el frente del vehiculo al pisar acelerador bajo carga en cambios altos",
    "al acelerar en carretera la trompa bambolea de izquierda a derecha al soltar acelerador desaparece",
    "sacudida fuerte en la parte delantera solo al pisar gas en 3ra o 4ta marcha juego en copa de palier",
    "trompa cabecea de lado a lado al exigir aceleracion en pista juego excesivo en triceta y copa de semieje",
    "vibracion en el tren delantero unicamente bajo aceleracion en cuarta velocidad suelto gas y se calma",
    "palier con desgaste en triceta produce que la trompa del auto se mueva de lado a lado al acelerar",
    "carro se sacude adelante al acelerar en subida en 3ra marcha al dejar rodar en neutro rueda sedita",
    "juego en junta interior copa triceta hace que el frente del auto zigzaguee al pisar el pedal",
    "bamboleo lateral de la parte delantera al acelerar entre 60 y 90 kmh transmitido por el semieje",
    "semieje con holgura en copa sacude toda la trompa al ganar velocidad en carretera al soltar se quita",
    "sacudida delantera bajo torque en tercera y cuarta velocidad atribuible a triceta picada o desalineada",
    "al presionar el acelerador la trompa se mueve de lado a lado al quitar el pie se estabiliza al instante",
    "vibracion de oscilacion lateral del frente del carro provocada por desgaste interno en copa de palier",
    "trompa sacude al acelerar en cambios altos por holgura en semieje delantero y triceta desgastada"
]
for c in CASOS_COPA_TRICETA:
    NUEVOS_CASOS.append((c, "Juntas homocineticas o palieres danados", "SUS_002", "Suspensión y Dirección", "Alta"))

# 6. Rodamiento de rueda (zumbido turbina modula al virar) -> SUSPENSION_CHASIS
CASOS_RODAJE_RUEDA = [
    "zumbido sordo como turbina de avion en una rueda delantera que aumenta con la velocidad",
    "al pasar 60 o 70 kmh empieza zumbido que se calla al doblar a la izquierda y suena fuerte al doblar derecha",
    "ruido de rodamiento de masa en rueda delantera zumba continuo y modula al cargar peso en curvas",
    "zumbido metalico en rueda delantera cambia de tono al girar el volante en carretera",
    "rodamiento de maza picado hace ruido de zumbido ronco que se intensifica a mayor velocidad en recta",
    "zumbido en rueda que se apaga al virar hacia un lado y redobla al girar hacia el lado opuesto",
    "ruido de rodaje de rueda delantera zumbido tipo avion que incrementa de 60 a 100 km por hora",
    "masa de rueda con rodamiento desgastado produce zumbido sordo modulado por la inclinacion del vehiculo",
    "rueda zumba fuerte al rodar rapido y el sonido cambia al cambiar de carril en autopista",
    "zumbido constante en rueda delantera derecha que se acentua al apoyar el peso en curva izquierda"
]
for c in CASOS_RODAJE_RUEDA:
    NUEVOS_CASOS.append((c, "Rodajes de caja mecanica o diferencial gastados", "TRA_004", "Transmisión y Embrague", "Alta"))
    NUEVOS_CASOS.append((c + " holgura en rodamiento de rueda", "Juntas homocineticas o palieres danados", "SUS_002", "Suspensión y Dirección", "Media"))

# 7. Cremallera de dirección (juego muerto al centro / timón flotante) -> SUSPENSION_CHASIS
CASOS_CREMALLERA_DIRECCION = [
    "timon flotante con juego muerto al centro tengo que ir corrigiendo la trayectoria en autopista",
    "direccion con zona muerta en el centro el auto flota en carretera y no mantiene la linea recta",
    "holgura en cremallera de direccion timon tiene juego libre al medio y volante no responde inmediato",
    "timon se siente flojo con vaiven en el centro y obliga a corregir constantemente para no salir de carril",
    "juego en volante de direccion y sensacion de flotabilidad a alta velocidad por desgaste en caja de direccion",
    "cremallera de direccion mecanica o hidraulica con juego central ocasiona desviacion erratica",
    "volante con movimiento muerto al centro auto navega como lancha en pista recta sin respuesta rapida",
    "holgura de direccion volante baila en el centro antes de que las ruedas comiencen a cruzar",
    "timon no tiene firmeza al centro se mueve libre dos centimetros y el carro viborea en carretera",
    "cremallera con desgaste en dientes centrales perdida de precision y juego muerto al manejar en linea recta"
]
for c in CASOS_CREMALLERA_DIRECCION:
    NUEVOS_CASOS.append((c, "Cremallera de direccion asistida con holgura o fuga", "SUS_004", "Suspensión y Dirección", "Alta"))

# 8. Trepidación de embrague al salir en 1ra -> TRANSMISION
CASOS_TREPIDACION_EMBRAGUE = [
    "al soltar el embrague para salir en primera marcha todo el carro tiembla y cabecea bastante",
    "trepidacion fuerte al acoplar primera marcha embrague vibra al arrancar desde parado",
    "disco de embrague vidriado o deformado hace que el carro tironee y tiemble al salir en primera",
    "cuando saco el pie del pedal de embrague en primera sacude la carroceria una vez que avanza va normal",
    "embrague salta y tironea al arrancar de cero en primera velocidad prensa o disco alabeado",
    "vibracion fuerte al embragar en primera velocidad transmision mecanica tironea al iniciar marcha",
    "embrague zapatea al salir en primera marcha prensa desalineada o resortes de disco vencidos",
    "sacudida en primera marcha al soltar pedal de clutch una vez acoplado rueda parejo y suave",
    "embrague trepida al salir en pendientes en primera velocidad volantemotor con recalentamiento y manchas",
    "carro tiembla como si se fuera a desarmar solo al sacar el pedal de embrague en primera"
]
for c in CASOS_TREPIDACION_EMBRAGUE:
    NUEVOS_CASOS.append((c, "Disco de embrague desgastado o patinando", "TRA_002", "Transmisión y Embrague", "Alta"))

# 9. Servofreno / booster silbido chupada de aire -> FRENOS
CASOS_SERVOFRENO_VACIO = [
    "pedal de freno durisimo para detener el carro hay que pararse en el pedal y silba aire al pisar",
    "se escucha silbido o siseo de aire cerca del pedal al frenar y el pedal esta como una piedra",
    "fuga de vacio en diafragma de servofreno pedal de freno duro y siseo de aire en el habitaculo",
    "booster de freno pinchado silba aire constante bajo el tablero y requiere gran fuerza para frenar",
    "pedal de freno pierde asistencia de vacio se pone duro como palo y silba al mantenerlo presionado",
    "manguera de vacio de servofreno rajada genera pedal duro y chupada de aire en multiple de admision",
    "servofreno con membrana rota silbido de aire al aplicar freno y motor tiende a alterar su ralenti",
    "al pisar el freno se escucha una fuga de aire siseante en los pies y el carro frena con mucha dificultad",
    "diafragma de booster de frenos roto pedal excesivamente rigido y soplido de vacio continuo",
    "pedal duro silbido de aire al pisar y aumento de distancia de frenado por falla de servofreno"
]
for c in CASOS_SERVOFRENO_VACIO:
    NUEVOS_CASOS.append((c, "Falla en servofreno (booster) o linea de vacio", "FRE_003", "Frenos", "Alta"))

def incorporar_casos():
    print(f"Cargando dataset actual desde: {DATASET_PATH}")
    df_actual = pd.read_csv(DATASET_PATH, encoding="utf-8")
    conteo_inicial = len(df_actual)
    print(f"Total registros actuales: {conteo_inicial}")

    nuevas_filas = []
    textos_existentes = set(df_actual["sintoma"].astype(str).str.lower().str.strip())

    agregados = 0
    duplicados = 0

    for sintoma, falla, cod, sist, sev in NUEVOS_CASOS:
        sint_clean = sintoma.strip().lower()
        if sint_clean not in textos_existentes:
            textos_existentes.add(sint_clean)
            nuevas_filas.append({
                "sintoma": sintoma.strip(),
                "falla": falla,
                "codigo_falla": cod,
                "sistema": sist,
                "severidad": sev
            })
            agregados += 1
        else:
            duplicados += 1

    df_nuevos = pd.DataFrame(nuevas_filas)
    df_final = pd.concat([df_actual, df_nuevos], ignore_index=True)

    # Eliminar posibles duplicados
    df_final = df_final.drop_duplicates(subset=["sintoma"])
    conteo_final = len(df_final)

    # Guardar dataset actualizado
    df_final.to_csv(DATASET_PATH, index=False, encoding="utf-8")

    print(f"Nuevos casos incorporados: {agregados}")
    print(f"Casos omitidos (ya existentes): {duplicados}")
    print(f"Total registros finales: {conteo_final} (+{conteo_final - conteo_inicial})")

if __name__ == "__main__":
    incorporar_casos()
