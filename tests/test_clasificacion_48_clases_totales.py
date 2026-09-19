"""Pruebas exhaustivas de clasificación para la totalidad de las 48 averías del modelo vehicular."""

from __future__ import annotations

import pytest

from src.infrastructure.modelo_ml import ModeloML


@pytest.fixture(scope="module")
def modelo_ml():
    return ModeloML()


CASOS_48_AVERIAS = [
    (
        "Alternador defectuoso o placa de diodos quemada",
        "testigo de bateria prendido en el tablero el alternador no carga y las luces bajan de intensidad",
    ),
    (
        "Amortiguadores reventados o bujes de suspension gastados",
        "el carro rebota demasiado en los baches golpe seco y amortiguadores chorreados de aceite",
    ),
    (
        "Baja presion de aceite o bomba de aceite defectuosa",
        "testigo rojo de presion de aceite encendido testigo de la aceitera parpadea en caliente",
    ),
    (
        "Bateria descargada o bornes sulfatados",
        "el carro no arranca bornes sulfatados y las luces del tablero se apagan al dar contacto",
    ),
    (
        "Bomba de gasolina quemada o con baja presion",
        "no llega presion de combustible al riel la bomba de gasolina no zumba al poner contacto",
    ),
    (
        "Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado",
        "la puerta del piloto no cierra bien el pestillo mecanico o la chapa esta trabada",
    ),
    (
        "Consumo de aceite por desgaste de anillos o retenes",
        "humo azul constante por el escape baja el nivel de aceite consumo por anillos de piston",
    ),
    (
        "Cremallera de direccion asistida con holgura o fuga",
        "timon duro juego en la cremallera de direccion y fuga de liquido hidraulico",
    ),
    (
        "Cuerpo de aceleracion o valvula IAC sucia",
        "revoluciones inestables suben y bajan en minimo ralenti inestable valvula iac sucia",
    ),
    (
        "Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)",
        "falla en celda del paquete de bateria de alto voltaje hibrido perdida de autonomia celda desbalanceada",
    ),
    (
        "Desgaste de pastillas y zapatas de freno",
        "chirrido de fierro con fierro al pisar el freno pastillas de freno desgastadas al limite",
    ),
    (
        "Disco de embrague desgastado o patinando",
        "acelero a fondo y el motor se revoluciona pero el vehiculo no avanza disco de embrague patinando",
    ),
    (
        "Discos de freno alabeados o desgastados",
        "vibracion intensa en el pedal de freno y timon al frenar a alta velocidad discos alabeados",
    ),
    (
        "Elevalunas electrico o guaya de alzacristales rota o trabada",
        "la luna no sube ni baja motor de elevalunas hace ruido o guaya de ventana rota",
    ),
    (
        "Empaque de culata soplado o danado",
        "sale bastante humo blanco espeso por el escape y se consume el refrigerante empaque de culata soplado",
    ),
    (
        "Faja o cadena de distribucion destensada o con salto de punto",
        "sonido de cascabeleo en la distribucion salto de punto faja o cadena destensada fuera de sincronia",
    ),
    (
        "Falla de correa dentada banada en aceite (Motor Ford 1.0 Dragon / GM Turbo)",
        "correa humeda banada en aceite degradada chupador de bomba de aceite tapado motor dragon turbo",
    ),
    (
        "Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)",
        "inyeccion directa gdi perdida de potencia por carbon acumulado en valvulas de admision cascabeleo",
    ),
    (
        "Falla electrica del cierre centralizado o actuador de puerta",
        "no abre con el mando a distancia actuador electrico de cierre centralizado no responde",
    ),
    (
        "Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI",
        "perdida de presion de sobrealimentacion actuador electronico de turbo vgt atascado motor tsi tfsi",
    ),
    (
        "Falla en bombin o bomba hidraulica de embrague",
        "pedal de embrague se queda en el fondo bombin o bombin esclavo hidraulico con fuga de liquido",
    ),
    (
        "Falla en bujias o bobinas de encendido (misfire)",
        "jaloneo al acelerar falla de chispa bobina quemada bujias con misfire cilindro 1",
    ),
    (
        "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)",
        "error en pantalla de cambio no disponible bomba del robot Dualogic sin presion acumulador descargado",
    ),
    (
        "Falla en compresor de aire acondicionado o fuga de gas R134a",
        "aire acondicionado no enfria compresor no acopla fuga de gas refrigerante r134a",
    ),
    (
        "Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)",
        "testigo de dpf saturado filtro de particulas tapado sistema adblue no regenera diesel euro",
    ),
    (
        "Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet)",
        "modulo de control de bomba de combustible fscm sin comunicacion pem sin voltaje motor se apaga",
    ),
    (
        "Falla en sensor de oxigeno o mezcla rica",
        "alto consumo de gasolina humo negro sensor de oxigeno lambda con lectura trabada mezcla rica",
    ),
    (
        "Falla en sensor de velocidad de rueda ABS",
        "testigo de ABS encendido sensor de velocidad de rueda abs sin lectura de revoluciones",
    ),
    (
        "Falla en servofreno (booster) o linea de vacio",
        "pedal de freno duro como una piedra servofreno booster sin vacio manguera rota",
    ),
    (
        "Falla en sistema Flex / Bi-combustible (Alcohol/Etanol)",
        "dificultad de arranque en frio con etanol calibracion de sensor flex fuel porcentaje de alcohol incorrecto",
    ),
    (
        "Falla en sistema de frenado regenerativo (EV / Hibridos)",
        "frenado regenerativo no recupera energia falla de transicion entre regeneracion y freno hidraulico ev",
    ),
    (
        "Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)",
        "valvula solenoide vvt trabada desfasaje de arbol de levas actuador valvetronic sin respuesta",
    ),
    (
        "Falla en termostato o motoventilador de radiador",
        "temperatura sube en trafico motoventilador del radiador no enciende o termostato pegado cerrado",
    ),
    (
        "Fallo en inversor de corriente IGBT o motor electrico (EV)",
        "falla en modulo de potencia igbt del inversor sobrecalentamiento del motor de traccion electrico",
    ),
    (
        "Falta o degradacion de aceite de caja de cambios",
        "cambios entran duros zumbido en la caja mecanica falta de aceite de transmision valvolina quemada",
    ),
    (
        "Foco o falla en sistema de refrigeracion de bateria/inversor (EV)",
        "bomba de refrigerante de alta tension quemada sobrecalentamiento de bateria de traccion ev",
    ),
    (
        "Fuga en mangueras de intercooler o turbocompresor danado",
        "silbido fuerte al acelerar manguera de intercooler rajada perdida de presion de turbo humo negro",
    ),
    (
        "Fuga en mangueras de refrigerante o radiador picado",
        "charco verde bajo el motor fuga en manguera de radiador picado baja nivel de anticongelante",
    ),
    (
        "Fuga hidraulica o aire en el sistema de frenos",
        "pedal de freno esponjoso se va hasta el fondo fuga de liquido o aire en el circuito de frenos",
    ),
    (
        "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)",
        "baja presion en riel common rail diesel no arranca en caliente fuga por retorno de inyector diesel",
    ),
    (
        "Fugas de aire o fallos en el sistema de frenos neumático (Camiones)",
        "perdida de presion de aire en calderines fuga en pulmon o manguera de freno de aire camion",
    ),
    (
        "Inyectores sucios o filtro de combustible obstruido",
        "tirones y perdida de potencia a cualquier velocidad inyectores tapados o filtro de gasolina sucio",
    ),
    (
        "Juntas homocineticas o palieres danados",
        "traqueteo o clac clac metalico al girar toda la direccion palier roto o junta homocinetica danada",
    ),
    (
        "Limpiaparabrisas o motor pluma quemado",
        "plumas del parabrisas no se mueven motor de limpiaparabrisas quemado varillaje trabado",
    ),
    (
        "Llantas desbalanceadas o desalineadas",
        "el timon vibra a 90 km/h en autopista y el carro se jala hacia la derecha llantas desbalanceadas",
    ),
    (
        "Rodajes de caja mecanica o diferencial gastados",
        "zumbido continuo que aumenta con la velocidad en diferencial o rodaje de eje de entrada de caja",
    ),
    (
        "Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
        "patinamiento y golpes al entrar los cambios en caja automatica cvt dsg sobrecalentamiento de fluido",
    ),
    (
        "Válvula de freno de aire o secador APS obstruido (Camiones)",
        "valvula secadora aps de camion tapada humedad en el circuito neumático valvula de descarga no corta",
    ),
]


@pytest.mark.parametrize("falla_esperada,sintoma_test", CASOS_48_AVERIAS)
def test_clasificacion_exhaustiva_48_averias(modelo_ml, falla_esperada, sintoma_test):
    """Verifica que cada una de las 48 averías del sistema sea identificada con certeza técnica."""
    top_predicciones = modelo_ml.predecir_top_fallas(sintoma_test, limite=3)
    assert len(top_predicciones) >= 1

    clases_top3 = [p["falla"] for p in top_predicciones]
    assert falla_esperada in clases_top3, (
        f"Falla '{falla_esperada}' no encontrada en top 3: {clases_top3} para síntoma '{sintoma_test}'"
    )

    prediccion_principal = top_predicciones[0]
    assert prediccion_principal["probabilidad"] > 0.0


def test_cobertura_total_48_clases_en_modelo(modelo_ml):
    """Verifica que el modelo cargado contenga al menos las 48 clases canónicas originales o 61 en Fase 8."""
    assert len(modelo_ml.modelo.classes_) in (48, 61)
    clases_modelo = set(modelo_ml.modelo.classes_)
    clases_test = {falla for falla, _ in CASOS_48_AVERIAS}
    assert clases_test.issubset(clases_modelo)


def test_vectorizador_vocabulario_robusto(modelo_ml):
    """Verifica que el vectorizador TF-IDF posea un vocabulario automotriz completo."""
    vocab = modelo_ml.vectorizador.vocabulary_
    assert len(vocab) > 500
    terminos_clave = ["freno", "motor", "aceite", "bateria", "bujia", "alternador", "embrague", "turbo"]
    for termino in terminos_clave:
        assert termino in vocab
