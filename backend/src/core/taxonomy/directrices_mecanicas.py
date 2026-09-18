"""Directrices técnicas de taller para sistemas de frenos, motor mecánico, combustible y embrague."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DirectrizTaller:
    codigo: str
    falla: str
    sistema: str
    subcomponente: str
    requiere_escaner: bool
    prueba_sugerida: str
    dtc_frecuente: str
    es_mecanica_pura: bool


DIRECTRICES_MECANICAS: list[DirectrizTaller] = [
    # Frenos
    DirectrizTaller(
        codigo="FRENO_001",
        falla="Desgaste de pastillas y zapatas de freno",
        sistema="Frenos",
        subcomponente="Pastillas y zapatas",
        requiere_escaner=False,
        prueba_sugerida=(
            "Inspección de espesor en milímetros de pastillas con vernier/micrómetro "
            "(reemplazar si es menor a 3 mm), estado de pistas del disco y guías de cáliper."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="FRENO_002",
        falla="Fuga hidraulica o aire en el sistema de frenos",
        sistema="Frenos",
        subcomponente="Circuito hidráulico",
        requiere_escaner=False,
        prueba_sugerida=(
            "Prueba de retención estática del pedal de freno durante 60 segundos, "
            "inspección visual de fugas en bombines/latiguillos y purgado de circuito hidráulico."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="FRENO_003",
        falla="Discos de freno alabeados o desgastados",
        sistema="Frenos",
        subcomponente="Discos de freno",
        requiere_escaner=False,
        prueba_sugerida=(
            "Medición de alabeo axial y variación de espesor (DTV) con reloj comparador montado "
            "en base magnética en ambas caras del disco (tolerancia máx. 0.05 mm)."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="FRENO_004",
        falla="Falla en servofreno (booster) o linea de vacio",
        sistema="Frenos",
        subcomponente="Servofreno (booster)",
        requiere_escaner=False,
        prueba_sugerida=(
            "Prueba de estanqueidad de pedal con motor apagado y medición de depresión con "
            "vacuómetro en manguera de admisión conectada al servofreno (mínimo 18 inHg)."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="FRENO_005",
        falla="Falla en sensor de velocidad de rueda ABS",
        sistema="Frenos",
        subcomponente="Sensor ABS",
        requiere_escaner=True,
        prueba_sugerida=(
            "Lectura de velocidad de giro de rueda en datos en vivo con escáner, comprobación "
            "de entrehierro de rueda fónica e inspección de viruta metálica en la punta del captador."
        ),
        dtc_frecuente="C0035",
        es_mecanica_pura=False,
    ),
    DirectrizTaller(
        codigo="FRENO_006",
        falla="Fugas de aire o fallos en el sistema de frenos neumático (Camiones)",
        sistema="Frenos Neumáticos",
        subcomponente="Líneas neumáticas",
        requiere_escaner=False,
        prueba_sugerida=(
            "Inspección de fugas con solución espumante en racores de tecalán y verificación de caída "
            "de presión en manómetros de calderines con motor detenido."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="FRENO_007",
        falla="Válvula de freno de aire o secador APS obstruido (Camiones)",
        sistema="Frenos Neumáticos",
        subcomponente="Secador de aire APS",
        requiere_escaner=False,
        prueba_sugerida=(
            "Drenaje manual de calderines verificando emulsión de agua/aceite y comprobación de ciclo "
            "de descarga de la válvula gobernadora del secador."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),

    # Motor Mecánico
    DirectrizTaller(
        codigo="MOTOR_001",
        falla="Falla en bujias o bobinas de encendido (misfire)",
        sistema="Motor",
        subcomponente="Bujías y bobinas",
        requiere_escaner=True,
        prueba_sugerida=(
            "Lectura de conteo de misfire por cilindro en escáner OBD-II, prueba de chispómetro en secundario "
            "e intercambiar bobina sospechosa con cilindro adyacente para contrastar DTC."
        ),
        dtc_frecuente="P0301",
        es_mecanica_pura=False,
    ),
    DirectrizTaller(
        codigo="MOTOR_002",
        falla="Consumo de aceite por desgaste de anillos o retenes",
        sistema="Motor",
        subcomponente="Retenes y anillos",
        requiere_escaner=False,
        prueba_sugerida=(
            "Inspección de depósitos húmedos en bujías, prueba comparativa de compresión seca y húmeda "
            "(agregando aceite a los cilindros) y prueba de estanqueidad de cilindros con neumogafas."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="MOTOR_003",
        falla="Empaque de culata soplado o danado",
        sistema="Motor",
        subcomponente="Empaque de culata",
        requiere_escaner=False,
        prueba_sugerida=(
            "Prueba química con líquido reactivo detector de CO2 en el depósito de refrigerante y medición "
            "de compresión neumática entre cilindros contiguos con motor apagado sin encenderlo (precaución: no hacer "
            "funcionar el motor si el aceite está emulsionado para evitar fundir metales de biela y bancada)."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="MOTOR_004",
        falla="Baja presion de aceite o bomba de aceite defectuosa",
        sistema="Motor",
        subcomponente="Bomba de aceite y coladera",
        requiere_escaner=False,
        prueba_sugerida=(
            "Instalación de manómetro hidráulico mecánico en el puerto del bulbo de presión (mínimo 20 psi "
            "en caliente a ralentí) y desmontaje de cárter para revisar coladera/chupona."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="MOTOR_005",
        falla="Faja o cadena de distribucion destensada o con salto de punto",
        sistema="Motor",
        subcomponente="Distribución sincronizada",
        requiere_escaner=True,
        prueba_sugerida=(
            "Comprobación visual de marcas de calado de distribución y osciloscopio correlacionando "
            "señales de posición CKP (cigüeñal) y CMP (árbol de levas)."
        ),
        dtc_frecuente="P0016",
        es_mecanica_pura=False,
    ),
    DirectrizTaller(
        codigo="MOTOR_006",
        falla="Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)",
        sistema="Motor",
        subcomponente="Válvulas de admisión GDI",
        requiere_escaner=True,
        prueba_sugerida=(
            "Inspección con boroscopio óptico en los ductos de admisión para evaluar carbonilla en asientos "
            "y monitoreo de ajustes de combustible STFT/LTFT en escáner."
        ),
        dtc_frecuente="P0300",
        es_mecanica_pura=False,
    ),
    DirectrizTaller(
        codigo="MOTOR_007",
        falla="Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)",
        sistema="Motor",
        subcomponente="Solenoide y piñón VVT",
        requiere_escaner=True,
        prueba_sugerida=(
            "Prueba activa de actuador OCV con escáner, limpieza de microfiltro de malla VVT y revisión de "
            "resistencia eléctrica del solenoide."
        ),
        dtc_frecuente="P0011",
        es_mecanica_pura=False,
    ),
    DirectrizTaller(
        codigo="MOTOR_008",
        falla="Falla de correa dentada banada en aceite (Motor Ford 1.0 Dragon / GM Turbo)",
        sistema="Motor",
        subcomponente="Correa húmeda de aceite",
        requiere_escaner=False,
        prueba_sugerida=(
            "Inspección del ancho de correa con calibre por la boca de llenado de aceite y desmontaje de "
            "cárter para verificar si la coladera de la bomba está tupida de virutas de caucho."
        ),
        dtc_frecuente="P0524",
        es_mecanica_pura=True,
    ),

    # Inyección y Combustible
    DirectrizTaller(
        codigo="COMBUSTIBLE_001",
        falla="Inyectores sucios o filtro de combustible obstruido",
        sistema="Inyección de Combustible",
        subcomponente="Inyectores y filtros",
        requiere_escaner=True,
        prueba_sugerida=(
            "Lectura de ajuste de combustible a corto y largo plazo (STFT/LTFT) en escáner y prueba de caudal, "
            "estanqueidad y atomización en banco de ultrasonido."
        ),
        dtc_frecuente="P0300",
        es_mecanica_pura=False,
    ),
    DirectrizTaller(
        codigo="COMBUSTIBLE_002",
        falla="Bomba de gasolina quemada o con baja presion",
        sistema="Inyección de Combustible",
        subcomponente="Bomba de combustible",
        requiere_escaner=False,
        prueba_sugerida=(
            "Conexión de manómetro en riel de inyectores midiendo presión sostenida de trabajo (45-60 psi) "
            "y prueba de caudal volumétrico (mínimo 1 litro en 30 segundos)."
        ),
        dtc_frecuente="P0087",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="COMBUSTIBLE_003",
        falla="Cuerpo de aceleracion o valvula IAC sucia",
        sistema="Inyección de Combustible",
        subcomponente="Cuerpo de aceleración / IAC",
        requiere_escaner=True,
        prueba_sugerida=(
            "Limpieza de carbonilla en garganta y mariposa de aceleración, prueba de actuador de ralentí "
            "y procedimiento de reaprendizaje de marcha mínima con escáner."
        ),
        dtc_frecuente="P0505",
        es_mecanica_pura=False,
    ),
    DirectrizTaller(
        codigo="COMBUSTIBLE_004",
        falla="Falla en sensor de oxigeno o mezcla rica",
        sistema="Inyección de Combustible",
        subcomponente="Sensor de oxígeno",
        requiere_escaner=True,
        prueba_sugerida=(
            "Graficación de curva de voltaje de sonda lambda en escáner (debe ciclar ágilmente entre 0.1V y 0.9V) "
            "y medición de resistencia del calefactor con multímetro."
        ),
        dtc_frecuente="P0130",
        es_mecanica_pura=False,
    ),
    DirectrizTaller(
        codigo="COMBUSTIBLE_005",
        falla="Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)",
        sistema="Inyección Diésel",
        subcomponente="Riel Common Rail",
        requiere_escaner=True,
        prueba_sugerida=(
            "Monitoreo de presión de rampa con escáner en fase de arranque (mínimo 250 bar) y prueba "
            "de probetas graduadas para medir el caudal de retorno de cada inyector."
        ),
        dtc_frecuente="P0087",
        es_mecanica_pura=False,
    ),
    DirectrizTaller(
        codigo="COMBUSTIBLE_006",
        falla="Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet)",
        sistema="Inyección de Combustible",
        subcomponente="Módulo de bomba FSCM",
        requiere_escaner=True,
        prueba_sugerida=(
            "Comprobación de ciclo de trabajo PWM con osciloscopio hacia la bomba sumergida y lectura de "
            "códigos DTC de red y alimentación en el módulo FSCM."
        ),
        dtc_frecuente="U0109",
        es_mecanica_pura=False,
    ),
    DirectrizTaller(
        codigo="COMBUSTIBLE_007",
        falla="Falla en sistema Flex / Bi-combustible (Alcohol/Etanol)",
        sistema="Inyección de Combustible",
        subcomponente="Lógica Flex / Etanol",
        requiere_escaner=True,
        prueba_sugerida=(
            "Reinicio y calibración de adaptación de combustible (A/F Learn) con escáner para forzar el "
            "reaprendizaje del porcentaje real de etanol en el tanque."
        ),
        dtc_frecuente="P0171",
        es_mecanica_pura=False,
    ),

    # Transmisión y Embrague
    DirectrizTaller(
        codigo="EMBRAGUE_001",
        falla="Disco de embrague desgastado o patinando",
        sistema="Transmisión y Embrague",
        subcomponente="Disco de embrague",
        requiere_escaner=False,
        prueba_sugerida=(
            "Prueba física de calado en 3ra marcha con freno de mano accionado a fondo y verificación de "
            "altura de desacople en el recorrido superior del pedal."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="EMBRAGUE_002",
        falla="Falla en bombin o bomba hidraulica de embrague",
        sistema="Transmisión y Embrague",
        subcomponente="Bombín hidráulico",
        requiere_escaner=False,
        prueba_sugerida=(
            "Inspección de fugas en guardapolvos de bombín maestro y esclavo, control de nivel de DOT 4 "
            "y purgado completo del circuito hidráulico de embrague."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),
]
