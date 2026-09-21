"""Pruebas unitarias para auto-preguntas técnicas dirigidas y formateo de porcentajes."""

from __future__ import annotations

from src.core.diagnostico.auto_interrogador import (
    MAPA_DESCRIPCION_OPCION,
    MAPA_HIPOTESIS_A_CLASE_CANONICA,
    AutoPreguntaTecnica,
    evaluar_auto_pregunta_descarte,
    formatear_mensaje_auto_pregunta,
    resolver_respuesta_autopregunta,
)


def test_alta_confianza_nunca_genera_autopregunta():
    pregunta = evaluar_auto_pregunta_descarte(
        texto="el carro vibra",
        diagnostico_top1="Discos de freno alabeados o desgastados",
        confianza_top1=0.75,
        predicciones_top=[
            {"falla": "Discos de freno alabeados o desgastados", "probabilidad": 0.75},
            {"falla": "Llantas desbalanceadas o desalineadas", "probabilidad": 0.25},
        ],
    )
    assert pregunta is None


def test_discriminador_claro_al_frenar_evita_pregunta():
    frases = [
        "tiembla el timon al pisar el freno",
        "el pedal vibra cuando freno a 60",
        "apenas piso el freno el carro sacude",
    ]
    for frase in frases:
        pregunta = evaluar_auto_pregunta_descarte(
            texto=frase,
            diagnostico_top1="Discos de freno alabeados o desgastados",
            confianza_top1=0.35,
            predicciones_top=[
                {"falla": "Discos de freno alabeados o desgastados", "probabilidad": 0.35},
                {"falla": "Llantas desbalanceadas o desalineadas", "probabilidad": 0.30},
            ],
        )
        assert pregunta is None, f"No debió generar pregunta para: {frase}"


def test_discriminador_velocidad_sin_frenar_evita_pregunta():
    pregunta = evaluar_auto_pregunta_descarte(
        texto="tiembla a 100 en carretera sin frenar",
        diagnostico_top1="Llantas desbalanceadas o desalineadas",
        confianza_top1=0.40,
        predicciones_top=[
            {"falla": "Llantas desbalanceadas o desalineadas", "probabilidad": 0.40},
            {"falla": "Discos de freno alabeados o desgastados", "probabilidad": 0.30},
        ],
    )
    assert pregunta is None


def test_generacion_dinamica_con_porcentajes():
    predicciones = [
        {"falla": "Discos de freno alabeados o desgastados", "probabilidad": 0.45},
        {"falla": "Llantas desbalanceadas o desalineadas", "probabilidad": 0.35},
        {"falla": "Cremallera de direccion asistida con holgura o fuga", "probabilidad": 0.20},
    ]
    pregunta = evaluar_auto_pregunta_descarte(
        texto="el timón vibra raro",
        diagnostico_top1="Discos de freno alabeados o desgastados",
        confianza_top1=0.45,
        predicciones_top=predicciones,
    )

    assert pregunta is not None
    assert pregunta.es_necesaria is True
    assert len(pregunta.opciones) == 3
    assert "— 45%" in pregunta.opciones[0]
    assert "— 35%" in pregunta.opciones[1]
    assert "— 20%" in pregunta.opciones[2]
    assert "1️⃣" in pregunta.opciones[0]
    assert "2️⃣" in pregunta.opciones[1]
    assert "3️⃣" in pregunta.opciones[2]
    assert "vibración" in pregunta.pregunta.lower()


def test_titulos_segun_categoria_sintoma():
    casos = [
        ("el carro no prende", "arranque"),
        ("el pedal del embrague patina", "embrague"),
        ("el pedal de freno esta esponjoso", "frenos"),
        ("el motor calienta en subida", "temperatura"),
        ("el auto tironea en baja", "tironeo"),
    ]
    for texto, palabra_clave in casos:
        pregunta = evaluar_auto_pregunta_descarte(
            texto=texto,
            diagnostico_top1="Generico",
            confianza_top1=0.4,
            predicciones_top=[
                {"falla": "Falla en bujias o bobinas de encendido (misfire)", "probabilidad": 0.4},
                {"falla": "Inyectores sucios o filtro de combustible obstruido", "probabilidad": 0.3},
            ],
        )
        assert pregunta is not None
        assert palabra_clave in pregunta.pregunta.lower() or "hipótesis" in pregunta.pregunta.lower()


def test_formatear_mensaje_auto_pregunta():
    pregunta = AutoPreguntaTecnica(
        es_necesaria=True,
        pregunta="🔍 Para precisar la causa del tironeo:",
        opciones=[
            "1️⃣ Bujías o bobinas — 60%",
            "2️⃣ Inyectores sucios — 40%",
        ],
        hipotesis_diferenciales=["Falla bujias", "Falla inyectores"],
    )
    mensaje = formatear_mensaje_auto_pregunta(pregunta)
    assert "🤖 🔍 Para precisar la causa del tironeo:" in mensaje
    assert "• 1️⃣ Bujías o bobinas — 60%" in mensaje
    assert "• 2️⃣ Inyectores sucios — 40%" in mensaje
    assert "👉 *Responde indicando 1, 2" in mensaje


def test_resolver_respuesta_por_numero():
    opciones = ["1️⃣ Opción A", "2️⃣ Opción B", "3️⃣ Opción C"]
    hipotesis = ["Clase A", "Clase B", "Clase C"]

    assert resolver_respuesta_autopregunta("1", opciones, hipotesis)[0] == 0
    assert resolver_respuesta_autopregunta("2", opciones, hipotesis)[0] == 1
    assert resolver_respuesta_autopregunta("3", opciones, hipotesis)[0] == 2
    assert resolver_respuesta_autopregunta("4", opciones, hipotesis)[0] is None  # no existe opcion 4


def test_resolver_respuesta_por_palabras_orden():
    opciones = ["1️⃣ Opción A", "2️⃣ Opción B", "3️⃣ Opción C"]
    hipotesis = ["Clase A", "Clase B", "Clase C"]

    assert resolver_respuesta_autopregunta("opción 1", opciones, hipotesis)[0] == 0
    assert resolver_respuesta_autopregunta("la 2", opciones, hipotesis)[0] == 1
    assert resolver_respuesta_autopregunta("primera", opciones, hipotesis)[0] == 0
    assert resolver_respuesta_autopregunta("segunda", opciones, hipotesis)[0] == 1
    assert resolver_respuesta_autopregunta("tercera", opciones, hipotesis)[0] == 2
    assert resolver_respuesta_autopregunta("1️⃣", opciones, hipotesis)[0] == 0


def test_resolver_respuesta_por_contenido_semantico():
    opciones = [
        "1️⃣ Jalonea o cabecea con pérdida de fuerza al acelerar en subida (Bujías o bobinas)",
        "2️⃣ Las revoluciones (RPM) suben y bajan solas o se apaga al desacelerar (Cuerpo de aceleración / IAC)",
    ]
    hipotesis = [
        "Falla en bujias o bobinas de encendido (misfire)",
        "Cuerpo de aceleracion o valvula IAC sucia",
    ]

    idx, texto, clase = resolver_respuesta_autopregunta(
        "siento que las revoluciones suben y bajan solas en neutro",
        opciones,
        hipotesis,
    )
    assert idx == 1
    assert clase == "Cuerpo de aceleracion o valvula IAC sucia"


def test_resolver_respuesta_no_coincidente_retorna_nulos():
    opciones = ["1️⃣ Opción A", "2️⃣ Opción B"]
    hipotesis = ["A", "B"]

    idx, texto, clase = resolver_respuesta_autopregunta(
        "cuánto cuesta cambiar la llanta de repuesto?",
        opciones,
        hipotesis,
    )
    assert idx is None
    assert texto is None
    assert clase is None


def test_mapa_descripcion_opcion_contiene_sistemas_clave():
    assert "Discos de freno alabeados o desgastados" in MAPA_DESCRIPCION_OPCION
    assert "Falla en bujias o bobinas de encendido (misfire)" in MAPA_DESCRIPCION_OPCION
    assert "Bomba de gasolina quemada o con baja presion" in MAPA_DESCRIPCION_OPCION
    assert "Disco de embrague desgastado o patinando" in MAPA_DESCRIPCION_OPCION
    assert "Bateria descargada o bornes sulfatados" in MAPA_DESCRIPCION_OPCION
    assert "Alternador defectuoso o placa de diodos quemada" in MAPA_DESCRIPCION_OPCION


def test_mapa_compatibilidad_clases_canonicas():
    assert (
        MAPA_HIPOTESIS_A_CLASE_CANONICA.get("Discos de freno alabeados")
        == "Discos de freno alabeados o desgastados"
    )
    assert (
        MAPA_HIPOTESIS_A_CLASE_CANONICA.get("Misfire bujías/bobinas")
        == "Falla en bujias o bobinas de encendido (misfire)"
    )
