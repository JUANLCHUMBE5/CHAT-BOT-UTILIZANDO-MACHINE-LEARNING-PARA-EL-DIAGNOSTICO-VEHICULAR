"""
Casos del 2do Grupo (50 casos) para la Prueba General de CarBot (Fase 7).
Consultas coloquiales de conductores y clientes de taller: escáner, multi-síntomas, quejas directas,
condiciones climáticas/operativas y problemas post-mantenimiento.
"""

from typing import Any, Dict, List

GRUPO_2_CASOS: List[Dict[str, Any]] = [
    # 1 al 10: Dudas con escáner
    {
        "id": "G2_01",
        "subgrupo": "escaner_dudas",
        "texto": "Mira, el check está prendido. Yo le pasé el escáner y me sale que es el cilindro 1. Ya le cambié la bujía, ya le cambié la bobina, y sigue fallando igual. Ya no sé qué más hacer."
    },
    {
        "id": "G2_02",
        "subgrupo": "escaner_dudas",
        "texto": "El escáner me dice mezcla pobre, ya limpié el sensor MAF como me dijo otro mecánico, pero sigue igual. El carro anda, pero no como antes."
    },
    {
        "id": "G2_03",
        "subgrupo": "escaner_dudas",
        "texto": "Me sale catalizador ineficiente en el escáner. Pero el carro camina bien, no gasta más gasolina, no huele raro. ¿Será que de verdad está mal el catalizador?"
    },
    {
        "id": "G2_04",
        "subgrupo": "escaner_dudas",
        "texto": "Me sale voltaje bajo en el escáner. Pero la batería es nueva, la compré hace un mes. Y el alternador carga bien, lo medí y me da 13.9. No entiendo qué pasa."
    },
    {
        "id": "G2_05",
        "subgrupo": "escaner_dudas",
        "texto": "Salió un código de presión de la caja CVT. Pero el aceite de la caja es nuevo, lo cambié hace poco. ¿Será el sensor?"
    },
    {
        "id": "G2_06",
        "subgrupo": "escaner_dudas",
        "texto": "El escáner dice falla múltiple, ya le cambié bujías y bobinas y sigue fallando. Ya no sé qué más revisar."
    },
    {
        "id": "G2_07",
        "subgrupo": "escaner_dudas",
        "texto": "Me sale sensor de cigüeñal, ya lo cambié y el carro sigue sin arrancar. Ya lo llevé a otro taller y tampoco."
    },
    {
        "id": "G2_08",
        "subgrupo": "escaner_dudas",
        "texto": "Salió EGR, ya limpié la válvula y sigue el código. ¿Será otra cosa?"
    },
    {
        "id": "G2_09",
        "subgrupo": "escaner_dudas",
        "texto": "Me sale sensor de árbol de levas, ya lo cambié y sigue fallando."
    },
    {
        "id": "G2_10",
        "subgrupo": "escaner_dudas",
        "texto": "Se prendió el check de la caja automática. El escáner dice P0700 pero no me da más detalle. No sé qué hacer."
    },

    # 11 al 20: Dos o más síntomas mezclados
    {
        "id": "G2_11",
        "subgrupo": "multisintoma",
        "texto": "El carro vibra a 90 kilómetros por hora. Y también vibra cuando freno. ¿Será lo mismo o son dos cosas?"
    },
    {
        "id": "G2_12",
        "subgrupo": "multisintoma",
        "texto": "Suena un ruido cuando paso los topes. Y también suena cuando giro el timón. ¿Será lo mismo?"
    },
    {
        "id": "G2_13",
        "subgrupo": "multisintoma",
        "texto": "Está consumiendo aceite. Y cuando acelero sale humo azul. ¿Será el motor?"
    },
    {
        "id": "G2_14",
        "subgrupo": "multisintoma",
        "texto": "Se apaga en los semáforos. Y a veces no quiere arrancar. ¿Será la batería o qué?"
    },
    {
        "id": "G2_15",
        "subgrupo": "multisintoma",
        "texto": "Las revoluciones suben pero el carro no avanza. Y a veces huele a quemado. ¿Será el embrague?"
    },
    {
        "id": "G2_16",
        "subgrupo": "multisintoma",
        "texto": "Pierde fuerza en las subidas. Y el tanque hace un zumbido fuerte. ¿Será la bomba?"
    },
    {
        "id": "G2_17",
        "subgrupo": "multisintoma",
        "texto": "Se calienta en el tráfico. Y el ventilador prende muy tarde. ¿Será el termostato o el ventilador?"
    },
    {
        "id": "G2_18",
        "subgrupo": "multisintoma",
        "texto": "La dirección está dura. Y suena cuando giro. ¿Será la bomba o la cremallera?"
    },
    {
        "id": "G2_19",
        "subgrupo": "multisintoma",
        "texto": "El pedal de freno está esponjoso. Se va hasta el fondo. ¿Será aire en el sistema?"
    },
    {
        "id": "G2_20",
        "subgrupo": "multisintoma",
        "texto": "Tiembla cuando estoy parado en el semáforo. Pero cuando acelero se quita. ¿Será bujía o soporte de motor?"
    },

    # 21 al 30: Quejas directas en jerga coloquial
    {
        "id": "G2_21",
        "subgrupo": "coloquial_directo",
        "texto": "El carro está cabeceando feo. Como que quiere apagarse pero no se apaga. ¿Qué será?"
    },
    {
        "id": "G2_22",
        "subgrupo": "coloquial_directo",
        "texto": "Piso el acelerador y se queda pensando. Como si le faltara gasolina. ¿Será la bomba?"
    },
    {
        "id": "G2_23",
        "subgrupo": "coloquial_directo",
        "texto": "El pedal está esponjoso. Tengo que bombearlo para que agarre. ¿Será aire?"
    },
    {
        "id": "G2_24",
        "subgrupo": "coloquial_directo",
        "texto": "En los huecos suena como que se va a desarmar. ¿Serán los amortiguadores?"
    },
    {
        "id": "G2_25",
        "subgrupo": "coloquial_directo",
        "texto": "El motor está cascabeleando cuando le doy medio pedal. ¿Será la gasolina o qué?"
    },
    {
        "id": "G2_26",
        "subgrupo": "coloquial_directo",
        "texto": "La palanca está dura para meter primera. Sobre todo en frío. ¿Será el aceite de caja?"
    },
    {
        "id": "G2_27",
        "subgrupo": "coloquial_directo",
        "texto": "El carro está jalando corriente. Se descarga de noche. ¿Será el alternador?"
    },
    {
        "id": "G2_28",
        "subgrupo": "coloquial_directo",
        "texto": "El timón se siente suelto. Como con juego. ¿Será la cremallera?"
    },
    {
        "id": "G2_29",
        "subgrupo": "coloquial_directo",
        "texto": "La aguja de temperatura sube y baja sola. Como loca. ¿Será el termostato?"
    },
    {
        "id": "G2_30",
        "subgrupo": "coloquial_directo",
        "texto": "El carro está pedo. No pasa de 80. ¿Será el catalizador?"
    },

    # 31 al 40: Fallas condicionales
    {
        "id": "G2_31",
        "subgrupo": "condicional",
        "texto": "Falla solo cuando llueve o hay mucha humedad. En seco anda normal. ¿Será algo eléctrico?"
    },
    {
        "id": "G2_32",
        "subgrupo": "condicional",
        "texto": "Pierde fuerza solo cuando el tanque está por la mitad o menos. ¿Será la bomba?"
    },
    {
        "id": "G2_33",
        "subgrupo": "condicional",
        "texto": "Patina solo cuando ya está caliente. En frío agarra bien. ¿Será el embrague o el aceite?"
    },
    {
        "id": "G2_34",
        "subgrupo": "condicional",
        "texto": "Falla solo después de 20 minutos de manejo. Al principio anda bien. ¿Será algo que se calienta?"
    },
    {
        "id": "G2_35",
        "subgrupo": "condicional",
        "texto": "Vibra solo al frenar desde alta velocidad. En ciudad no se siente. ¿Serán los discos?"
    },
    {
        "id": "G2_36",
        "subgrupo": "condicional",
        "texto": "Consume aceite solo en carretera. En ciudad no baja nada. ¿Serán las guías de válvula?"
    },
    {
        "id": "G2_37",
        "subgrupo": "condicional",
        "texto": "Suena solo al pasar topes. No en los baches. ¿Serán los bujes?"
    },
    {
        "id": "G2_38",
        "subgrupo": "condicional",
        "texto": "Se calienta solo en subida con carga. En plano está normal. ¿Será el radiador?"
    },
    {
        "id": "G2_39",
        "subgrupo": "condicional",
        "texto": "La dirección está dura solo a baja velocidad. ¿Será la bomba?"
    },
    {
        "id": "G2_40",
        "subgrupo": "condicional",
        "texto": "Falla solo en frío. Cuando ya calienta funciona normal. ¿Será el sensor de temperatura?"
    },

    # 41 al 50: Problemas post-mantenimiento
    {
        "id": "G2_41",
        "subgrupo": "post_mantenimiento",
        "texto": "Le cambié las bujías yo mismo. Y ahora falla más que antes. ¿Habré puesto mal algo?"
    },
    {
        "id": "G2_42",
        "subgrupo": "post_mantenimiento",
        "texto": "Le puse pastillas nuevas. Y ahora chirría más que antes. ¿Será que están mal puestas?"
    },
    {
        "id": "G2_43",
        "subgrupo": "post_mantenimiento",
        "texto": "Le cambié la batería. Y ahora no quiere arrancar. ¿Será que la puse mal?"
    },
    {
        "id": "G2_44",
        "subgrupo": "post_mantenimiento",
        "texto": "Le limpié los inyectores. Y ahora consume más gasolina. ¿Será que los dañé?"
    },
    {
        "id": "G2_45",
        "subgrupo": "post_mantenimiento",
        "texto": "Le cambié los amortiguadores. Y ahora suena más. ¿Será que eran incorrectos?"
    },
    {
        "id": "G2_46",
        "subgrupo": "post_mantenimiento",
        "texto": "Le cambié el aceite. Y ahora suena un tac-tac. ¿Será que puse el aceite equivocado?"
    },
    {
        "id": "G2_47",
        "subgrupo": "post_mantenimiento",
        "texto": "Le cambié el aceite de la caja. Y ahora patina. ¿Será que era otro aceite?"
    },
    {
        "id": "G2_48",
        "subgrupo": "post_mantenimiento",
        "texto": "Le cambié el termostato. Y ahora calienta más. ¿Será que lo puse al revés?"
    },
    {
        "id": "G2_49",
        "subgrupo": "post_mantenimiento",
        "texto": "Le cambié la bomba de dirección. Y sigue dura. ¿Será que era otra cosa?"
    },
    {
        "id": "G2_50",
        "subgrupo": "post_mantenimiento",
        "texto": "Le cambié el sensor MAF. Y ahora falla más. ¿Será que el sensor era genérico?"
    }
]
