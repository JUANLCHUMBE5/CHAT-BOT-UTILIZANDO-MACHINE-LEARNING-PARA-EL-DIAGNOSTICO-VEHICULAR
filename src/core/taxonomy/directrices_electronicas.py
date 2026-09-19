"""Directrices técnicas de taller para sistemas de transmisión automática, refrigeración, eléctricos, suspensión, clima, turbo y EV/híbridos."""

from __future__ import annotations

from src.core.taxonomy.directrices_mecanicas import DirectrizTaller

DIRECTRICES_ELECTRONICAS: list[DirectrizTaller] = [
    DirectrizTaller(
        codigo="TRANSMISION_001",
        falla="Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
        sistema="Transmisión y Embrague",
        subcomponente="Caja CVT / DSG",
        requiere_escaner=True,
        prueba_sugerida=(
            "Escaneo de temperatura de fluido de transmisión (ATF/CVT), prueba de accionamiento de electroválvulas "
            "y verificación de nivel y degradación química del fluido."
        ),
        dtc_frecuente="P0750",
        es_mecanica_pura=False,
    ),
    DirectrizTaller(
        codigo="TRANSMISION_002",
        falla="Rodajes de caja mecanica o diferencial gastados",
        sistema="Transmisión y Embrague",
        subcomponente="Rodamientos de caja / piñón",
        requiere_escaner=False,
        prueba_sugerida=(
            "Escucha directa con estetoscopio mecánico en carcasas de rodamientos de caja en elevador rodando en 4ta "
            "marcha y revisión de limaduras metálicas adheridas al imán del tapón de drenaje."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="TRANSMISION_003",
        falla="Falta o degradacion de aceite de caja de cambios",
        sistema="Transmisión y Embrague",
        subcomponente="Valvulina de caja",
        requiere_escaner=False,
        prueba_sugerida=(
            "Inspección física del nivel de lubricante en el tapón de control de rebose y evaluación de olor "
            "a quemado o pérdida de viscosidad de la valvulina."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="TRANSMISION_004",
        falla="Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)",
        sistema="Transmisión y Embrague",
        subcomponente="Unidad electrohidráulica robotizada",
        requiere_escaner=True,
        prueba_sugerida=(
            "Medición de presión de acumulación hidráulica con escáner (debe superar 45 bar), revisión de fugas "
            "de líquido de robotizador y procedimiento guiado de purga/calibración."
        ),
        dtc_frecuente="P1773",
        es_mecanica_pura=False,
    ),

    # Refrigeración
    DirectrizTaller(
        codigo="REFRIGERACION_001",
        falla="Falla en termostato o motoventilador de radiador",
        sistema="Refrigeración",
        subcomponente="Termostato y electroventilador",
        requiere_escaner=False,
        prueba_sugerida=(
            "Medición comparativa con pirómetro infrarrojo entre manguera superior (caliente) e inferior del "
            "radiador para verificar apertura de termostato y prueba de activación de relé del ventilador."
        ),
        dtc_frecuente="P0128",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="REFRIGERACION_002",
        falla="Fuga en mangueras de refrigerante o radiador picado",
        sistema="Refrigeración",
        subcomponente="Mangueras y radiador",
        requiere_escaner=False,
        prueba_sugerida=(
            "Presurización estática del circuito de refrigeración con bomba manual a 15 psi e inspección con luz "
            "de contraste en uniones de abrazaderas y paneles del panal."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),

    # Sistema Eléctrico y Carga
    DirectrizTaller(
        codigo="ELECTRICO_001",
        falla="Alternador defectuoso o placa de diodos quemada",
        sistema="Sistema Eléctrico y Carga",
        subcomponente="Alternador",
        requiere_escaner=False,
        prueba_sugerida=(
            "Medición de voltaje de carga en bornes con multímetro (13.8V a 14.4V a 2000 RPM con luces encendidas) "
            "y prueba de rizado AC con osciloscopio para detectar diodo rectificador quemado."
        ),
        dtc_frecuente="P0562",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="ELECTRICO_002",
        falla="Bateria descargada o bornes sulfatados",
        sistema="Sistema Eléctrico y Carga",
        subcomponente="Batería y motor de arranque",
        requiere_escaner=False,
        prueba_sugerida=(
            "Medición de voltaje con multímetro en Terminal 50 y Borne 30 del motor de arranque al dar marcha "
            "(mínimo 10.5V sin caída de tensión en luces). Prueba de toques ligeros al cuerpo del arrancador con mango "
            "aislado para comprobar carbones pegados o solenoide fogueado; y prueba de conductancia/CCA de batería (Sin escáner)."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),

    # Suspensión y Dirección
    DirectrizTaller(
        codigo="SUSPENSION_001",
        falla="Amortiguadores reventados o bujes de suspension gastados",
        sistema="Suspensión y Dirección",
        subcomponente="Amortiguadores y bujes",
        requiere_escaner=False,
        prueba_sugerida=(
            "Inspección de fugas de aceite en vástagos de amortiguador y palanqueo con barreta en elevador para "
            "detectar juego libre en bujes de trapecio, rótulas de suspensión y bieletas."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="SUSPENSION_002",
        falla="Juntas homocineticas o palieres danados",
        sistema="Suspensión y Dirección",
        subcomponente="Junta homocinética y palier",
        requiere_escaner=False,
        prueba_sugerida=(
            "Inspección de fuelles/guardapolvos rotos con fuga de grasa y prueba de giro en ocho con timón a tope "
            "acelerando para reproducir chasquido mecánico de canastilla."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="SUSPENSION_003",
        falla="Cremallera de direccion asistida con holgura o fuga",
        sistema="Suspensión y Dirección",
        subcomponente="Cremallera de dirección",
        requiere_escaner=False,
        prueba_sugerida=(
            "Inspección de fuelles por presencia de fluido hidráulico, control de holgura axial en axiales/precintos "
            "y calibración de cero de sensor de ángulo de dirección SAS en elevador."
        ),
        dtc_frecuente="C1511",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="SUSPENSION_004",
        falla="Llantas desbalanceadas o desalineadas",
        sistema="Suspensión y Dirección",
        subcomponente="Ruedas y alineación",
        requiere_escaner=False,
        prueba_sugerida=(
            "Calibrar presión de inflado en frío en las 4 ruedas, realizar balanceo dinámico computarizado de "
            "ruedas delanteras en máquina e inspección de cotas de alineación 3D (convergencia, caída y avance)."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),

    # Climatización y Turbo
    DirectrizTaller(
        codigo="CLIMA_001",
        falla="Falla en compresor de aire acondicionado o fuga de gas R134a",
        sistema="Climatización y Confort",
        subcomponente="Compresor de climatización",
        requiere_escaner=False,
        prueba_sugerida=(
            "Conexión de manifold de manómetros en alta y baja midiendo presiones estáticas y de trabajo del gas R134a "
            "y prueba de fuga con nitrógeno o lámpara UV."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="TURBO_001",
        falla="Fuga en mangueras de intercooler o turbocompresor danado",
        sistema="Sobrealimentación y Turbo",
        subcomponente="Turbocompresor e intercooler",
        requiere_escaner=True,
        prueba_sugerida=(
            "Monitoreo de presión de soplado MAP/Boost en escáner frente al valor deseado e inspección de fisuras "
            "en mangueras de sobrealimentación y juego axial en eje de turbina."
        ),
        dtc_frecuente="P0299",
        es_mecanica_pura=False,
    ),
    DirectrizTaller(
        codigo="TURBO_002",
        falla="Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI",
        sistema="Sobrealimentación y Turbo",
        subcomponente="Actuador de wastegate VGT",
        requiere_escaner=True,
        prueba_sugerida=(
            "Comprobación de recorrido de varilla de wastegate con reloj comparador y prueba guiada de calibración "
            "de topes del actuador electrónico con escáner."
        ),
        dtc_frecuente="P2563",
        es_mecanica_pura=False,
    ),
    DirectrizTaller(
        codigo="ESCAPE_001",
        falla="Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)",
        sistema="Sistema de Escape y Emisiones",
        subcomponente="Filtro de partículas DPF",
        requiere_escaner=True,
        prueba_sugerida=(
            "Lectura con escáner de presión diferencial de gases y gramos de hollín acumulados en el DPF, "
            "seguido de regeneración forzada estática de taller."
        ),
        dtc_frecuente="P2463",
        es_mecanica_pura=False,
    ),

    # Carrocería y Confort
    DirectrizTaller(
        codigo="CARROCERIA_001",
        falla="Falla electrica del cierre centralizado o actuador de puerta",
        sistema="Carrocería y Confort",
        subcomponente="Cierre centralizado",
        requiere_escaner=True,
        prueba_sugerida=(
            "Prueba de accionamiento con lámpara lógica de pulsos de 12V en conector de chapa y escaneo de "
            "señales de interruptor en módulo de confort BCM."
        ),
        dtc_frecuente="B1300",
        es_mecanica_pura=False,
    ),
    DirectrizTaller(
        codigo="CARROCERIA_002",
        falla="Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado",
        sistema="Carrocería y Confort",
        subcomponente="Cerradura mecánica",
        requiere_escaner=False,
        prueba_sugerida=(
            "Regulación de altura del cerradero en el pilar B/C, lubricación de varillaje interno de chapa "
            "e inspección de holguras por bisagras vencidas."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="CARROCERIA_003",
        falla="Elevalunas electrico o guaya de alzacristales rota o trabada",
        sistema="Carrocería y Confort",
        subcomponente="Mecanismo elevalunas",
        requiere_escaner=False,
        prueba_sugerida=(
            "Desmontaje de tapiz de puerta, alimentación directa a 12V al motor de luna para descartar cableado "
            "e inspección de cables de acero trenzado y poleas del alzacristales."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),
    DirectrizTaller(
        codigo="CARROCERIA_004",
        falla="Limpiaparabrisas o motor pluma quemado",
        sistema="Carrocería y Confort",
        subcomponente="Motor limpiaparabrisas",
        requiere_escaner=False,
        prueba_sugerida=(
            "Comprobación con multímetro de señal de alimentación en velocidades 1, 2 e intermitente en conector "
            "de motor pluma y desacople de bieletas mecánicas para descartar varillaje trabado."
        ),
        dtc_frecuente="N/A",
        es_mecanica_pura=True,
    ),

    # Vehículos Eléctricos e Híbridos
    DirectrizTaller(
        codigo="ELECTRICO_HV_001",
        falla="Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)",
        sistema="Vehículos Eléctricos e Híbridos",
        subcomponente="Batería de alto voltaje",
        requiere_escaner=True,
        prueba_sugerida=(
            "Medición con escáner del delta de voltaje entre bloques de celdas bajo aceleración plena "
            "(tolerancia máx. 0.20V) y comprobación de resistencia interna por bloque."
        ),
        dtc_frecuente="P0A80",
        es_mecanica_pura=False,
    ),
    DirectrizTaller(
        codigo="ELECTRICO_HV_002",
        falla="Fallo en inversor de corriente IGBT o motor electrico (EV)",
        sistema="Vehículos Eléctricos e Híbridos",
        subcomponente="Inversor IGBT",
        requiere_escaner=True,
        prueba_sugerida=(
            "Escaneo de códigos de aislamiento de alta tensión en controlador de tracción y verificación de "
            "circulación de refrigerante de la bomba dedicada del inversor."
        ),
        dtc_frecuente="P0A94",
        es_mecanica_pura=False,
    ),
    DirectrizTaller(
        codigo="ELECTRICO_HV_003",
        falla="Falla en sistema de frenado regenerativo (EV / Hibridos)",
        sistema="Vehículos Eléctricos e Híbridos",
        subcomponente="Freno electrohidráulico regenerativo",
        requiere_escaner=True,
        prueba_sugerida=(
            "Calibración de sensor de carrera de pedal de freno (stroke sensor) con escáner y purga "
            "automatizada guiada por software en la unidad hidráulica de alta presión."
        ),
        dtc_frecuente="C1391",
        es_mecanica_pura=False,
    ),
    DirectrizTaller(
        codigo="ELECTRICO_HV_004",
        falla="Foco o falla en sistema de refrigeracion de bateria/inversor (EV)",
        sistema="Vehículos Eléctricos e Híbridos",
        subcomponente="Refrigeración de batería/inversor",
        requiere_escaner=True,
        prueba_sugerida=(
            "Prueba de activación del ventilador o bomba eléctrica con escáner e inspección visual de la rejilla "
            "y ducto de ventilación de la batería de tracción."
        ),
        dtc_frecuente="P0A93",
        es_mecanica_pura=False,
    ),
]
