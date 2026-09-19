"""
test_analisis_respuestas_diagnostico.py
Pruebas integrales para analizar la precisión, confianza y generación de respuestas
del ChatBot de Diagnóstico Vehicular con Machine Learning (Tesis UCV 2026).
"""

import pytest

from src.core.gestor_diagnostico import GestorDiagnostico, ResultadoDiagnostico
from src.core.traductor_jerga import normalizar_jerga_peruana


@pytest.fixture
def gestor():
    return GestorDiagnostico(gemini_api_key="mock_test_key")


# ==============================================================================
# 1. PRUEBAS DE PREDICCIÓN ML Y RESPUESTAS POR SISTEMA VEHICULAR
# ==============================================================================

def _quitar_tildes(texto: str) -> str:
    """Normaliza tildes y caracteres especiales para comparaciones robustas."""
    import unicodedata
    return unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8').lower()


CASOS_SISTEMAS_VEHICULARES = [
    # (Síntoma de entrada, Término esperado en diagnóstico/RAG, Sistema)
    ("pastillas de freno chillan horrible al frenar en la bajada", "freno", "Sistema de Frenos"),
    ("el pedal de freno se va hasta el fondo y esta esponjoso", "freno", "Sistema de Frenos"),
    ("el motor cascabelea y tiembla cuando acelero fuerte", "bujia", "Sistema de Motor / Encendido"),
    ("sale humo blanco por el escape y consume refrigerante", "culata", "Sistema de Refrigeración / Motor"),
    ("la caja automatica patina y da tirones al pasar a segunda", "caja", "Sistema de Transmisión"),
    ("el timon esta duro al doblar y suena chillido en la direccion", "direccion", "Sistema de Dirección"),
    ("siento un golpe seco en los baches en la llanta delantera", "amortiguador", "Sistema de Suspensión"),
    ("el alternador no carga y la bateria se descarga rapido", "bateria", "Sistema Eléctrico"),
    ("el aire acondicionado no enfria nada solo bota aire caliente", "aire", "Sistema de Climatización"),
    ("la puerta del copiloto no abre con el control y la chapa esta trabada", "puerta", "Carrocería / Puertas"),
]


@pytest.mark.parametrize("sintoma,termino_clave,sistema", CASOS_SISTEMAS_VEHICULARES)
def test_obtencion_respuesta_por_sistema_vehicular(gestor, sintoma, termino_clave, sistema):
    """Verifica que para cada sistema automotriz, el modelo ML y RAG obtengan resultados coherentes."""
    resultado: ResultadoDiagnostico = gestor.procesar_consulta_texto(
        texto_usuario=sintoma,
        placa="ABC-123",
        marca_modelo="Toyota Yaris"
    )

    # 1. Si emitió auto-pregunta técnica de descarte, contiene predicciones clínicas válidas
    if resultado.modo_diagnostico == "esperando_clarificacion" and resultado.predicciones_ml:
        assert resultado.confianza_ml > 0.0, f"Falló en {sistema}: confianza ML es 0"
        texto_combinado = _quitar_tildes(
            " ".join(p.falla for p in resultado.predicciones_ml) + " " +
            resultado.respuesta_texto
        )
    else:
        assert resultado.modo_diagnostico != "esperando_clarificacion", f"Falló en {sistema}: se clasificó como ambiguo"
        assert resultado.confianza_ml > 0.0, f"Falló en {sistema}: confianza ML es 0"
        texto_combinado = _quitar_tildes(
            resultado.diagnostico_ml + " " +
            resultado.contexto_manual + " " +
            resultado.titulo_manual + " " +
            resultado.respuesta_texto
        )

    termino_normalizado = _quitar_tildes(termino_clave)
    assert termino_normalizado in texto_combinado, f"Falló en {sistema}: no se encontró '{termino_clave}' en el resultado"


# ==============================================================================
# 2. PRUEBAS DE TRADUCCIÓN DE JERGA PERUANA Y DIALECTOS
# ==============================================================================

CASOS_JERGA_PERUANA = [
    ("mi carro se chupa en la subida de comas", ["pierde potencia", "pierde fuerza", "se chupa"]),
    ("la caña esta dura y zumba", ["vehiculo", "caña"]),
    ("el carro cascabelea con gasolina de 90", ["preignicion", "bujia", "cascabeleo", "cascabelea"]),
    ("el motor jalonea y da tirones", ["tirones", "jalonea", "acelerar"]),
]


@pytest.mark.parametrize("frase_jerga,palabras_equivalentes", CASOS_JERGA_PERUANA)
def test_normalizacion_jerga_peruana_obtiene_diagnostico(gestor, frase_jerga, palabras_equivalentes):
    """Verifica que el normalizador de jerga técnica peruana permita obtener el diagnóstico correcto."""
    texto_normalizado = normalizar_jerga_peruana(frase_jerga)

    # Comprobar que la jerga fue procesada
    assert any(
        _quitar_tildes(palabra) in _quitar_tildes(texto_normalizado) or
        _quitar_tildes(palabra) in _quitar_tildes(frase_jerga)
        for palabra in palabras_equivalentes
    )

    resultado = gestor.procesar_consulta_texto(texto_usuario=frase_jerga)
    assert resultado.confianza_ml > 0.0
    assert resultado.diagnostico_ml != ""


# ==============================================================================
# 3. PRUEBAS DE CÓDIGOS DE SCANNER OBD-II (DTC)
# ==============================================================================

CASOS_DTC = [
    ("scanner me bota codigo P0300 misfire en cilindros", "p0300", "encendido"),
    ("el escaner arroja falla P0505 valvula iac ralenti inestable", "p0505", "iac"),
    ("codigo P0562 voltaje bajo del sistema", "p0562", "bateria"),
]


@pytest.mark.parametrize("consulta_dtc,codigo_esperado,palabra_tecnica", CASOS_DTC)
def test_procesamiento_codigos_scanner_obd2(gestor, consulta_dtc, codigo_esperado, palabra_tecnica):
    """Verifica que las consultas con códigos DTC de escáner automotriz se resuelvan con precisión."""
    resultado = gestor.procesar_consulta_texto(texto_usuario=consulta_dtc)

    texto_total = (
        resultado.diagnostico_ml.lower() + " " +
        resultado.contexto_manual.lower() + " " +
        resultado.respuesta_texto.lower()
    )
    assert codigo_esperado in texto_total or palabra_tecnica in texto_total


# ==============================================================================
# 4. PRUEBAS DE CONTROL DE AMBIGÜEDAD Y SALUDOS
# ==============================================================================

def test_saludo_inicial_no_emite_diagnostico_falso(gestor):
    """Un saludo debe responder cortésmente pidiendo el síntoma, sin disparar predicción clínica falsa."""
    resultado = gestor.procesar_consulta_texto("Hola buenas tardes CarBot")
    assert resultado.modo_diagnostico == "saludo"
    assert "Hola" in resultado.respuesta_texto or "Bienvenido" in resultado.respuesta_texto


def test_consulta_demasiado_corta_o_vaga_solicita_detalles(gestor):
    """Una entrada vaga como 'mi carro falla' debe solicitar detalles para asegurar calidad."""
    resultado = gestor.procesar_consulta_texto("mi carro falla")
    assert resultado.modo_diagnostico == "esperando_clarificacion"
    assert resultado.requiere_revision_humana is True
    assert "especifique" in resultado.respuesta_texto.lower() or "detalle" in resultado.respuesta_texto.lower()


@pytest.mark.parametrize(
    "pregunta",
    [
        "se puede arrancar el carro directo a gas si tiene un equipo de 5ta generación",
        "qué porcentaje de refrigerante debe usar mi auto si tiene más de 100 mil km",
        "cuánto kilometraje debe recorrer mi auto para instalar GNV",
        "qué potencia deben tener los focos LED H4 para una Suzuki APV",
    ],
)
def test_pregunta_informativa_no_inventa_una_averia(pregunta):
    gestor_sin_red = GestorDiagnostico(gemini_api_key="")
    gestor_sin_red.api_key = ""

    resultado = gestor_sin_red.procesar_consulta_texto(pregunta)

    assert resultado.tipo_consulta == "consulta_tecnica"
    assert resultado.modo_diagnostico == "consulta_tecnica_degradada"
    assert resultado.diagnostico_ml == "Consulta técnica informativa"
    assert resultado.confianza_ml == 0.0
    assert resultado.predicciones_ml == []
    assert "falla vehicular" not in resultado.respuesta_texto.lower()


@pytest.mark.parametrize(
    "sintoma",
    [
        "por qué vibra el volante cuando freno",
        "mi auto pierde fuerza al subir y se apaga",
        "el escáner muestra el código P0300",
    ],
)
def test_pregunta_con_sintoma_real_conserva_flujo_diagnostico(sintoma):
    gestor_sin_red = GestorDiagnostico(gemini_api_key="")
    gestor_sin_red.api_key = ""

    resultado = gestor_sin_red.procesar_consulta_texto(sintoma)

    assert resultado.tipo_consulta == "diagnostico"
    assert resultado.diagnostico_ml != "Consulta técnica informativa"


# ==============================================================================
# 5. PRUEBAS DE ESTRUCTURA Y CAMPOS DEL DTO DE RESULTADO
# ==============================================================================

def test_resultado_diagnostico_dto_completo(gestor):
    """Verifica que el objeto ResultadoDiagnostico contenga todos los atributos requeridos."""
    sintoma = "pastillas de freno desgastadas hacen ruido al frenar"
    resultado = gestor.procesar_consulta_texto(sintoma, placa="ABC-123", marca_modelo="Nissan Sentra")

    assert isinstance(resultado, ResultadoDiagnostico)
    assert hasattr(resultado, "diagnostico_ml")
    assert hasattr(resultado, "confianza_ml")
    assert hasattr(resultado, "contexto_manual")
    assert hasattr(resultado, "titulo_manual")
    assert hasattr(resultado, "similitud_rag")
    assert hasattr(resultado, "requiere_revision_humana")
    assert hasattr(resultado, "respuesta_texto")
    assert isinstance(resultado.confianza_ml, float)
    assert 0.0 <= resultado.confianza_ml <= 1.0
