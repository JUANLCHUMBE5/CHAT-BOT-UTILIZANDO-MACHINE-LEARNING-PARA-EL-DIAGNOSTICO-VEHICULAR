"""
Casos del 1er Grupo (50 casos) para la Prueba General de CarBot (Fase 7).
Consultas técnicas de taller, fallas específicas, DTCs, componentes y condiciones de operación.
"""

from typing import Any, Dict, List

GRUPO_1_CASOS: List[Dict[str, Any]] = [
    {
        "id": "G1_01",
        "texto": "Corolla 2017 en frío prende perfecto, después de 25 minutos empieza a tironear y termina apagándose. En caliente gira motor pero no prende; espero 15 minutos y arranca como si nada. No tengo DTC."
    },
    {
        "id": "G1_02",
        "texto": "Yaris 2018 pierde fuerza solo cuando subo cerro con 4 pasajeros. En plano anda normal. Si piso a fondo se ahoga un poco, pero si acelero progresivamente responde mejor."
    },
    {
        "id": "G1_03",
        "texto": "Kia Rio 2019 mínimo inestable, a veces se apaga en semáforo. Ya limpiaron cuerpo de aceleración y sigue igual. Al prender A/C empeora bastante."
    },
    {
        "id": "G1_04",
        "texto": "Sentra 2016 arranca normal, pero cuando calienta comienza a fallar un cilindro. Cambié bujías y bobinas de posición y la falla sigue en el mismo cilindro."
    },
    {
        "id": "G1_05",
        "texto": "Mazda 3 2018 check parpadea únicamente cuando acelero fuerte. Scanner P0303. En mínimo casi no se siente falla y bujía del cilindro 3 sale húmeda."
    },
    {
        "id": "G1_06",
        "texto": "Corolla 2015 tiene P0171. Ya revisé mangueras visibles y no encuentro fuga. En mínimo los fuel trims se van positivos pero acelerando a 2500 rpm mejoran bastante."
    },
    {
        "id": "G1_07",
        "texto": "Hyundai Accent demora en prender únicamente después de cargar gasolina hasta llenar el tanque. Cuando prende huele fuerte a combustible y luego trabaja normal."
    },
    {
        "id": "G1_08",
        "texto": "Motor diésel Common Rail demora en arrancar en las mañanas, después trabaja normal. Un inyector tiene retorno bastante mayor que los otros tres."
    },
    {
        "id": "G1_09",
        "texto": "Toyota prende bien frío, pero caliente demora bastante en arrancar. No hay DTC. Presión de combustible queda dentro de rango y el motor de arranque gira normal."
    },
    {
        "id": "G1_10",
        "texto": "Después de cambiar la faja de distribución el carro quedó chancho, tiembla en mínimo y hace explosiones sordas por escape. Antes del trabajo funcionaba normal."
    },
    {
        "id": "G1_11",
        "texto": "Sentra P0420 vuelve cada dos días después de borrarlo. No hay misfire, consumo normal y el sensor delantero oscila, pero el sensor posterior copia casi la misma señal."
    },
    {
        "id": "G1_12",
        "texto": "Toyota P0301. Cambié bujía y bobina del cilindro 1 por las del cilindro 2 pero P0301 continúa. Compresión del cilindro 1 está bastante más baja que los demás."
    },
    {
        "id": "G1_13",
        "texto": "Kia con humo negro y consumo alto. Scanner marca mezcla rica. Presión de combustible está por encima de especificación y al retirar la manguera de vacío del regulador aparece gasolina."
    },
    {
        "id": "G1_14",
        "texto": "Hyundai pierde potencia en alta. Presión de combustible es normal en mínimo pero cae fuerte apenas acelero a fondo. La bomba hace más ruido cuando el tanque está casi vacío."
    },
    {
        "id": "G1_15",
        "texto": "Motor tiembla y no tiene fuerza, pero no hay check. Al desconectar inyector 2 prácticamente no cambia nada; al desconectar cualquiera de los otros cilindros empeora."
    },
    {
        "id": "G1_16",
        "texto": "Pedal de freno se va lentamente hasta abajo mientras estoy detenido. Si bombeo recupera altura. No existe fuga externa y el depósito mantiene nivel."
    },
    {
        "id": "G1_17",
        "texto": "Pedal de freno está durísimo con motor prendido. Apago motor, bombeo varias veces y casi no cambia. Se escucha siseo cerca del booster cuando mantengo el pedal."
    },
    {
        "id": "G1_18",
        "texto": "Después de manejar 15 minutos la rueda delantera derecha queda hirviendo y el carro comienza a jalar. Lo dejo enfriar y vuelve a rodar libremente."
    },
    {
        "id": "G1_19",
        "texto": "A 100 km/h no vibra nada mientras acelero. Piso freno suavemente y empieza a temblar el timón; mientras más fuerte freno, más fuerte vibra."
    },
    {
        "id": "G1_20",
        "texto": "Timón vibra entre 85 y 105 km/h sin tocar freno. Ya balancearon las cuatro ruedas dos veces y sigue exactamente igual. Una llanta tiene una pequeña deformación visible."
    },
    {
        "id": "G1_21",
        "texto": "ABS entra casi siempre justo antes de detenerme aunque el piso esté seco. No hay rueda bloqueada. Scanner muestra una rueda cayendo a 0 km/h antes que las otras."
    },
    {
        "id": "G1_22",
        "texto": "Después de cambiar pastillas el pedal quedó largo y esponjoso. No hay fugas. Bombeándolo tres veces queda firme, pero después vuelve a bajar."
    },
    {
        "id": "G1_23",
        "texto": "Caja automática en frío demora 4 segundos en enganchar R y luego entra con golpe. En D entra normal. Cuando calienta, reversa mejora bastante."
    },
    {
        "id": "G1_24",
        "texto": "Sentra CVT después de 40 minutos en tráfico pierde respuesta y entra en protección. Scanner P0841. Apago 10 minutos y vuelve a trabajar."
    },
    {
        "id": "G1_25",
        "texto": "Volkswagen DSG en frío trabaja normal, pero caliente tiembla al salir en primera y demora en enganchar D. No presenta falla de motor."
    },
    {
        "id": "G1_26",
        "texto": "Fiat Dualogic estando en semáforo cambia solo a N, la bomba electrohidráulica trabaja demasiado seguido y algunas veces no permite seleccionar primera."
    },
    {
        "id": "G1_27",
        "texto": "Auto mecánico en cuarta piso a fondo, RPM suben de 2500 a 4500 pero velocidad casi no aumenta. No hay tirones del motor ni check engine."
    },
    {
        "id": "G1_28",
        "texto": "Al pisar embrague aparece un ronquido. Suelto pedal y desaparece completamente. Los cambios entran bien y el embrague no patina."
    },
    {
        "id": "G1_29",
        "texto": "En neutro caja hace un zumbido. Piso embrague y el ruido desaparece. Al soltarlo vuelve inmediatamente aunque el carro esté detenido."
    },
    {
        "id": "G1_30",
        "texto": "Al salir en primera el carro sacude fuerte, pero una vez que embrague queda completamente acoplado ya no vibra. Motor en mínimo trabaja parejo."
    },
    {
        "id": "G1_31",
        "texto": "Después de caer en un hueco el volante quedó torcido y el carro jala a la derecha. No vibra a velocidad y las llantas están correctamente balanceadas."
    },
    {
        "id": "G1_32",
        "texto": "Al doblar completamente a la izquierda y acelerar despacio suena tac-tac-tac. Si avanzo recto desaparece. En carretera no vibra."
    },
    {
        "id": "G1_33",
        "texto": "A 70 km/h aparece zumbido ronco adelante. Al hacer una curva larga hacia la izquierda el ruido disminuye y hacia la derecha aumenta."
    },
    {
        "id": "G1_34",
        "texto": "El carro rebota dos o tres veces después de cada rompemuelle y en carretera se siente flotando. Las llantas tienen presión correcta."
    },
    {
        "id": "G1_35",
        "texto": "Volante tiene juego muerto al centro. En autopista tengo que corregir constantemente, pero no existe vibración y el balanceo está correcto."
    },
    {
        "id": "G1_36",
        "texto": "Desgasta únicamente el borde interno de ambas llantas delanteras. No vibra y tampoco jala demasiado, pero las llantas nuevas se gastaron rápido."
    },
    {
        "id": "G1_37",
        "texto": "Motor calienta solamente en tráfico. En carretera la temperatura vuelve a normal. Cuando está caliente reviso y el electroventilador no entra."
    },
    {
        "id": "G1_38",
        "texto": "Temperatura sube rápido. Manguera superior del radiador está muy caliente y la inferior permanece fría. Ventilador sí funciona."
    },
    {
        "id": "G1_39",
        "texto": "Consume refrigerante sin gotear al piso. Depósito hace burbujas constantes y las mangueras se ponen durísimas pocos minutos después de arrancar en frío."
    },
    {
        "id": "G1_40",
        "texto": "Testigo de aceite parpadea únicamente cuando motor está caliente en mínimo. A 1500 rpm se apaga. Nivel de aceite está correcto."
    },
    {
        "id": "G1_41",
        "texto": "En las mañanas hace tac-tac metálico arriba del motor durante 3 minutos. Cuando llega aceite y calienta desaparece por completo. No hay check engine."
    },
    {
        "id": "G1_42",
        "texto": "Luces aumentan demasiado de intensidad cuando acelero, ya quemó dos focos y la batería huele raro después de manejar. Medí 16.1 voltios con motor prendido."
    },
    {
        "id": "G1_43",
        "texto": "P0562 presente. En mínimo tengo 11.9 V y acelerando apenas llega a 12.3 V. Batería fue cambiada hace una semana."
    },
    {
        "id": "G1_44",
        "texto": "Giro llave y solo hace clac una vez. Faros mantienen buen brillo y batería mide 12.7 V. Golpeando suavemente el motor de arranque algunas veces prende."
    },
    {
        "id": "G1_45",
        "texto": "Batería nueva se descarga durante la noche. Alternador carga 14.2 V andando. Con carro apagado medí consumo de 650 mA y al retirar un fusible baja a 35 mA."
    },
    {
        "id": "G1_46",
        "texto": "Camión carga aire muy lentamente. No escucho fuga grande externa, compresor trabaja todo el tiempo y tarda demasiado en llegar a presión de operación."
    },
    {
        "id": "G1_47",
        "texto": "Camión llega a presión normal pero el secador hace PSSHH cada pocos segundos aunque nadie toque el freno. Después vuelve a cargar y repite."
    },
    {
        "id": "G1_48",
        "texto": "Camión estacionado pierde presión de un tanque. Se escucha fuga constante por una cámara de freno trasera, pero al pisar el pedal el sonido cambia."
    },
    {
        "id": "G1_49",
        "texto": "Cliente solo dice: 'cuando calienta se pone pesado, tiembla un poco y a veces se apaga; después de descansar vuelve normal'. No hay scanner conectado ni más datos."
    },
    {
        "id": "G1_50",
        "texto": "Cliente dice: 'adelante hace cloc, a veces jala y siento algo raro en el timón'. No sabe cuándo empezó, no sabe si ocurre frenando y no hay inspección todavía."
    }
]
