"""
Catálogo Canónico de 40 Casos Técnicos para Evaluación E2E con Rúbrica — CarBot (Fase 7)
Cubre exhaustivamente los 7 macro-sistemas automotrices y balancea averías
electromecánicas con códigos DTC y averías mecánicas puras sin escáner OBD-II.
"""

from typing import Any, Dict, List

CASOS_E2E_RUBRICA_40: List[Dict[str, Any]] = [
    # 1. MOTOR / DTC P0301 (Misfire)
    {
        "id": "E2E_01",
        "sistema": "MOTOR",
        "falla_esperada": "Falla en bujias o bobinas de encendido (misfire)",
        "dtc": "P0301",
        "es_mecanica_pura": False,
        "consulta": "Tengo un Toyota Yaris 2018 con motor 2NR-FE, tiembla bastante en mínimo y al acelerar pierde fuerza. El escáner arroja P0301."
    },
    # 2. MOTOR / Ralentí inestable
    {
        "id": "E2E_02",
        "sistema": "MOTOR",
        "falla_esperada": "Cuerpo de aceleracion o valvula IAC sucia",
        "dtc": None,
        "es_mecanica_pura": False,
        "consulta": "Nissan Versa 2019, al llegar a los semáforos y poner neutro el mínimo oscila entre 500 y 1100 RPM y a veces se apaga."
    },
    # 3. MOTOR / Sobrecalentamiento (Mecánica Pura)
    {
        "id": "E2E_03",
        "sistema": "MOTOR",
        "falla_esperada": "Empaque de culata soplado o danado",
        "dtc": None,
        "es_mecanica_pura": True,
        "consulta": "Kia Rio 2017 calienta en subidas, el depósito de refrigerante gorgotea con burbujas constantes y bota humo blanco con olor dulce por el escape."
    },
    # 4. FRENOS / Alabeo de discos (Mecánica Pura)
    {
        "id": "E2E_04",
        "sistema": "FRENOS",
        "falla_esperada": "Discos de freno alabeados o desgastados",
        "dtc": None,
        "es_mecanica_pura": True,
        "consulta": "Toyota Corolla 2018, cuando freno en autopista bajando a 90 km/h el pedal de freno vibra y zapatea con fuerza, pero en ciudad frena suave."
    },
    # 5. FRENOS / Desgaste de pastillas (Mecánica Pura)
    {
        "id": "E2E_05",
        "sistema": "FRENOS",
        "falla_esperada": "Desgaste de pastillas y zapatas de freno",
        "dtc": None,
        "es_mecanica_pura": True,
        "consulta": "Hyundai Accent 2017, la rueda delantera derecha queda hirviendo tras 15 minutos de marcha, el auto jala hacia la derecha y huele a balata quemada."
    },
    # 6. FRENOS / Pedal esponjoso (Mecánica Pura)
    {
        "id": "E2E_06",
        "sistema": "FRENOS",
        "falla_esperada": "Fuga hidraulica o aire en el sistema de frenos",
        "dtc": None,
        "es_mecanica_pura": True,
        "consulta": "Nissan Sentra 2016, el pedal de freno se va hasta el fondo muy esponjoso, solo agarra si lo bombeo dos o tres veces seguidas."
    },
    # 7. TRANSMISIÓN / Embrague patinando (Mecánica Pura)
    {
        "id": "E2E_07",
        "sistema": "TRANSMISION",
        "falla_esperada": "Disco de embrague desgastado o patinando",
        "dtc": None,
        "es_mecanica_pura": True,
        "consulta": "Chevrolet Sail 2018, en subida piso el acelerador a fondo y las revoluciones suben a 4000 RPM pero el carro no avanza con fuerza y huele a quemado."
    },
    # 8. TRANSMISIÓN / CVT con DTC P0841
    {
        "id": "E2E_08",
        "sistema": "TRANSMISION",
        "falla_esperada": "Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
        "dtc": "P0841",
        "es_mecanica_pura": False,
        "consulta": "Nissan Qashqai 2019 con transmisión CVT, se encendió testigo de transmisión y escáner marca P0841 sensor de presión de fluido de caja."
    },
    # 9. TRANSMISIÓN / Dualogic robotizada
    {
        "id": "E2E_09",
        "sistema": "TRANSMISION",
        "falla_esperada": "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)",
        "dtc": None,
        "es_mecanica_pura": False,
        "consulta": "Fiat Grand Siena Dualogic 2016, salta a neutro solo en el tráfico, la bomba eléctrica zumba a cada rato y no quiere entrar reversa."
    },
    # 10. SUSPENSIÓN / Amortiguadores reventados (Mecánica Pura)
    {
        "id": "E2E_10",
        "sistema": "SUSPENSION_CHASIS",
        "falla_esperada": "Amortiguadores reventados o bujes de suspension gastados",
        "dtc": None,
        "es_mecanica_pura": True,
        "consulta": "Toyota Yaris 2019, golpe seco metálico cloc-cloc al pasar baches pequeños y la carrocería rebota repetidas veces tras un rompemuelle."
    },
    # 11. SUSPENSIÓN / Juntas homocinéticas (Mecánica Pura)
    {
        "id": "E2E_11",
        "sistema": "SUSPENSION_CHASIS",
        "falla_esperada": "Juntas homocineticas o palieres danados",
        "dtc": None,
        "es_mecanica_pura": True,
        "consulta": "Kia Rio 2017, traqueteo metálico constante trac-trac-trac en la rueda delantera izquierda al girar cerrado acelerando en una esquina."
    },
    # 12. SUSPENSIÓN / Llantas desbalanceadas (Mecánica Pura)
    {
        "id": "E2E_12",
        "sistema": "SUSPENSION_CHASIS",
        "falla_esperada": "Llantas desbalanceadas o desalineadas",
        "dtc": None,
        "es_mecanica_pura": True,
        "consulta": "Hyundai Elantra 2018, volante tiembla en autopista recta entre 90 y 110 km/h sin pisar el freno, pasando 120 km/h la vibración disminuye."
    },
    # 13. ELÉCTRICO / Alternador defectuoso
    {
        "id": "E2E_13",
        "sistema": "ELECTRICO",
        "falla_esperada": "Alternador defectuoso o placa de diodos quemada",
        "dtc": None,
        "es_mecanica_pura": False,
        "consulta": "Chevrolet Cruze 2017, luz de batería encendida en el tablero, faros pierden intensidad al acelerar y el voltaje medido en bornes marca 11.7V con motor prendido."
    },
    # 14. ELÉCTRICO / Batería descargada
    {
        "id": "E2E_14",
        "sistema": "ELECTRICO",
        "falla_esperada": "Bateria descargada o bornes sulfatados",
        "dtc": None,
        "es_mecanica_pura": False,
        "consulta": "Suzuki Swift 2019, no da arranque por las mañanas, solo hace un chasquido 'clac' en el arrancador y las luces del tablero se atenúan por completo."
    },
    # 15. CLIMATIZACIÓN / Compresor A/C
    {
        "id": "E2E_15",
        "sistema": "CLIMATIZACION",
        "falla_esperada": "Falla en compresor de aire acondicionado o fuga de gas R134a",
        "dtc": None,
        "es_mecanica_pura": False,
        "consulta": "Nissan Tiida 2015, presiono botón A/C, el motor cabecea un poco pero sale aire caliente por las rejillas, compresor no acopla el embrague magnético."
    },
    # 16. NEUMÁTICA / Frenos de aire camión
    {
        "id": "E2E_16",
        "sistema": "CARROCERIA_NEUMATICA",
        "falla_esperada": "Fugas de aire o fallos en el sistema de frenos neumático (Camiones)",
        "dtc": None,
        "es_mecanica_pura": True,
        "consulta": "Camión Volvo FH 2016, los tanques de aire pierden presión con el vehículo apagado, se escucha silbido constante de fuga en la válvula de freno de estacionamiento."
    },
    # 17. MOTOR / Bomba de gasolina
    {
        "id": "E2E_17",
        "sistema": "MOTOR",
        "falla_esperada": "Bomba de gasolina quemada o con baja presion",
        "dtc": None,
        "es_mecanica_pura": False,
        "consulta": "Toyota Etios 2018, en subidas prolongadas el motor pierde fuerza de golpe como si no le llegara nafta, en el tanque suena un silbido agudo continuo."
    },
    # 18. MOTOR / Catalizador con DTC P0420
    {
        "id": "E2E_18",
        "sistema": "MOTOR",
        "falla_esperada": "Falla en sensor de oxigeno o mezcla rica",
        "dtc": "P0420",
        "es_mecanica_pura": False,
        "consulta": "Hyundai Elantra 2017, check engine prendido con P0420 eficiencia de catalizador banco 1 por debajo del umbral, motor amarrado a más de 3000 RPM."
    },
    # 19. MOTOR / Distribución salto de punto (Mecánica Pura)
    {
        "id": "E2E_19",
        "sistema": "MOTOR",
        "falla_esperada": "Faja o cadena de distribucion destensada o con salto de punto",
        "dtc": None,
        "es_mecanica_pura": True,
        "consulta": "Toyota Corolla 2015, cambiaron faja de distribución y el carro quedó con arranque largo, tiembla en mínimo y tiene explosiones sordas en escape."
    },
    # 20. DIRECCIÓN / Cremallera con juego (Mecánica Pura)
    {
        "id": "E2E_20",
        "sistema": "SUSPENSION_CHASIS",
        "falla_esperada": "Cremallera de direccion asistida con holgura o fuga",
        "dtc": None,
        "es_mecanica_pura": True,
        "consulta": "Kia Rio 2018, el timón tiene un juego muerto al medio de casi 2 pulgadas y al moverlo rápido de lado a lado se siente un golpe seco en la cremallera."
    },
    # 21. MOTOR / Inyectores sucios
    {
        "id": "E2E_21",
        "sistema": "MOTOR",
        "falla_esperada": "Inyectores sucios o filtro de combustible obstruido",
        "dtc": None,
        "es_mecanica_pura": False,
        "consulta": "Hyundai Tucson 2018 GDI inyección directa, motor tose y titubea fuertemente en aceleración rápida y consumo de nafta se disparó."
    },
    # 22. MOTOR / Common Rail Diesel
    {
        "id": "E2E_22",
        "sistema": "MOTOR",
        "falla_esperada": "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)",
        "dtc": "P0087",
        "es_mecanica_pura": False,
        "consulta": "Toyota Hilux 2.8 1GD-FTV 2019, pierde fuerza repentinamente en subidas, testigo de check activo y scanner marca DTC P0087 presión baja de riel."
    },
    # 23. MOTOR / DPF diesel Euro 5/6
    {
        "id": "E2E_23",
        "sistema": "MOTOR",
        "falla_esperada": "Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)",
        "dtc": "P2463",
        "es_mecanica_pura": False,
        "consulta": "Volkswagen Amarok 2.0 BiTDI, testigo de filtro DPF parpadea en tablero, motor no supera 2500 RPM y scanner lee P2463 acumulación de hollín."
    },
    # 24. MOTOR / Desfase VVT con DTC P0011
    {
        "id": "E2E_24",
        "sistema": "MOTOR",
        "falla_esperada": "Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)",
        "dtc": "P0011",
        "es_mecanica_pura": False,
        "consulta": "Nissan Sentra 1.8 B17, cascabeleo en tapa de válvulas al acelerar en caliente, luz de check encendida con código P0011 avance excesivo arbol de levas."
    },
    # 25. MOTOR / Termostato trabado
    {
        "id": "E2E_25",
        "sistema": "MOTOR",
        "falla_esperada": "Falla en termostato o motoventilador de radiador",
        "dtc": "P0128",
        "es_mecanica_pura": False,
        "consulta": "Chevrolet Cruze 2018, la aguja de temperatura no sube a su nivel normal en carretera y el escáner arroja código P0128 termostato de refrigerante."
    },
    # 26. FRENOS / Booster o servofreno (Mecánica Pura)
    {
        "id": "E2E_26",
        "sistema": "FRENOS",
        "falla_esperada": "Falla en servofreno (booster) o linea de vacio",
        "dtc": None,
        "es_mecanica_pura": True,
        "consulta": "Suzuki Swift 2019, el pedal de freno quedó completamente duro como una piedra, no tiene asistencia y al pisar se escucha un silbido de aire."
    },
    # 27. FRENOS / Sensor ABS con DTC C0035
    {
        "id": "E2E_27",
        "sistema": "FRENOS",
        "falla_esperada": "Falla en sensor de velocidad de rueda ABS",
        "dtc": "C0035",
        "es_mecanica_pura": False,
        "consulta": "Nissan Qashqai 2018, testigo de ABS y derrape activados en el tablero, al frenar suave el pedal zapatea indebidamente y scanner lee DTC C0035."
    },
    # 28. FRENOS / Frenado regenerativo híbrido con DTC C1259
    {
        "id": "E2E_28",
        "sistema": "FRENOS",
        "falla_esperada": "Falla en sistema de frenado regenerativo (EV / Hibridos)",
        "dtc": "C1259",
        "es_mecanica_pura": False,
        "consulta": "Toyota Prius 2017 híbrido, frenada áspera con tirón al cambiar de freno regenerativo a hidráulico y scanner registra DTC C1259."
    },
    # 29. TRANSMISIÓN / Bombín de embrague con fuga (Mecánica Pura)
    {
        "id": "E2E_29",
        "sistema": "TRANSMISION",
        "falla_esperada": "Falla en bombin o bomba hidraulica de embrague",
        "dtc": None,
        "es_mecanica_pura": True,
        "consulta": "Kia Rio 2019 caja mecánica, pedal de embrague se fue al piso de golpe sin resistencia y gotea líquido DOT 3 por la junta de la campana."
    },
    # 30. TRANSMISIÓN / Rodajes de caja mecánica (Mecánica Pura)
    {
        "id": "E2E_30",
        "sistema": "TRANSMISION",
        "falla_esperada": "Rodajes de caja mecanica o diferencial gastados",
        "dtc": None,
        "es_mecanica_pura": True,
        "consulta": "Toyota Corolla 2015 mecánico, zumbido bronco en la caja de cambios que aumenta con la velocidad en 3ra y 4ta marcha y desaparece al pisar embrague."
    },
    # 31. TRANSMISIÓN / Aceite ATF degradado
    {
        "id": "E2E_31",
        "sistema": "TRANSMISION",
        "falla_esperada": "Falta o degradacion de aceite de caja de cambios",
        "dtc": None,
        "es_mecanica_pura": False,
        "consulta": "Kia Cerato 2017 caja automática tradicional, sacudida fuerte al pasar de Neutro a Drive y fluido de transmisión luce oscuro con olor a quemado."
    },
    # 32. SUSPENSIÓN / Balanceo y alineación (Mecánica Pura)
    {
        "id": "E2E_32",
        "sistema": "SUSPENSION_CHASIS",
        "falla_esperada": "Llantas desbalanceadas o desalineadas",
        "dtc": None,
        "es_mecanica_pura": True,
        "consulta": "Hyundai i20 2019, volante vibra entre 95 y 115 km/h en pista lisa sin tocar el freno para nada, y el auto tiende a desviarse hacia el lado derecho."
    },
    # 33. SUSPENSIÓN / Palier y junta homocinética (Mecánica Pura)
    {
        "id": "E2E_33",
        "sistema": "SUSPENSION_CHASIS",
        "falla_esperada": "Juntas homocineticas o palieres danados",
        "dtc": None,
        "es_mecanica_pura": True,
        "consulta": "Nissan Versa 2018, ruido metálico clac-clac repetitivo al acelerar en curvas cerradas o dar vuelta en U, fuelle de palier derecho roto y sin grasa."
    },
    # 34. ELÉCTRICO / Alternador con placa de diodos quemada
    {
        "id": "E2E_34",
        "sistema": "ELECTRICO",
        "falla_esperada": "Alternador defectuoso o placa de diodos quemada",
        "dtc": None,
        "es_mecanica_pura": False,
        "consulta": "Chevrolet Sail 2018, luz roja de batería enciende al acelerar a más de 2000 RPM y el voltaje medido con multímetro no sube de 11.9V."
    },
    # 35. ELÉCTRICO / Bornes sulfatados y batería muerta
    {
        "id": "E2E_35",
        "sistema": "ELECTRICO",
        "falla_esperada": "Bateria descargada o bornes sulfatados",
        "dtc": None,
        "es_mecanica_pura": False,
        "consulta": "Toyota Hilux 2016, bornes de la batería con sarro blanco espeso, al girar la llave en frío no mueve el motor y voltaje en reposo mide 10.2V."
    },
    # 36. ELÉCTRICO / Batería de tracción híbrida con DTC P0A80
    {
        "id": "E2E_36",
        "sistema": "ELECTRICO",
        "falla_esperada": "Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)",
        "dtc": "P0A80",
        "es_mecanica_pura": False,
        "consulta": "Toyota Prius 2016 híbrido, autonomía eléctrica reducida drásticamente, ventilador de enfriamiento HV suena continuo y escáner arroja DTC P0A80."
    },
    # 37. ELÉCTRICO / Inversor de tracción con DTC P0A1A
    {
        "id": "E2E_37",
        "sistema": "ELECTRICO",
        "falla_esperada": "Fallo en inversor de corriente IGBT o motor electrico (EV)",
        "dtc": "P0A1A",
        "es_mecanica_pura": False,
        "consulta": "Nissan Leaf 2018 100% eléctrico, auto no activa indicador READY, no engrana marcha y scanner registra DTC P0A1A fallo interno en inversor de tracción."
    },
    # 38. CLIMATIZACIÓN / Fuga de gas refrigerante R134a
    {
        "id": "E2E_38",
        "sistema": "CLIMATIZACION",
        "falla_esperada": "Falla en compresor de aire acondicionado o fuga de gas R134a",
        "dtc": None,
        "es_mecanica_pura": False,
        "consulta": "Toyota Corolla 2017, aire acondicionado no enfría en cabina, compresor acopla pero las presiones de alta y baja se mantienen igualadas en 65 PSI."
    },
    # 39. CARROCERÍA / Cierre centralizado actuador trabado
    {
        "id": "E2E_39",
        "sistema": "CARROCERIA_NEUMATICA",
        "falla_esperada": "Falla electrica del cierre centralizado o actuador de puerta",
        "dtc": None,
        "es_mecanica_pura": False,
        "consulta": "Kia Cerato 2018, la puerta trasera del lado del copiloto no traba ni destraba con el control remoto ni con el botón maestro de la consola."
    },
    # 40. NEUMÁTICA / Válvula secador APS de camión (Mecánica Pura)
    {
        "id": "E2E_40",
        "sistema": "CARROCERIA_NEUMATICA",
        "falla_esperada": "Válvula de freno de aire o secador APS obstruido (Camiones)",
        "dtc": None,
        "es_mecanica_pura": True,
        "consulta": "Camión Scania R450, secador de aire APS descarga continuamente cada 6 segundos botando agua y manómetro de tanques no logra superar 6.2 bar."
    },
]
