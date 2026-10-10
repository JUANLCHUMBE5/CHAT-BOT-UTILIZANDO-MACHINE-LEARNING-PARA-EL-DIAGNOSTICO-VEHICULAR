"""Regresiones T05: evidencia RAG y origen de confianza, sin servicios reales."""

from src.core.conversacion.formateador_compacto import FormateadorCompacto
from src.core.diagnostico.models import PrediccionML
from src.core.diagnostico.politica_fusion import PoliticaFusionDiagnostica
from src.core.diagnostico.prompt_builder import construir_prompt_diagnostico
from src.core.gestor_diagnostico import GestorDiagnostico

FALLAS = [
    {"falla": "Falla en termostato o motoventilador de radiador", "probabilidad": 0.55},
    {"falla": "Bomba de agua con circulación insuficiente", "probabilidad": 0.31},
    {"falla": "Tapa del radiador defectuosa", "probabilidad": 0.14},
]
META_PRELIMINAR = {
    "falla": FALLAS[1]["falla"],
    "sistema": "MOTOR",
    "estado_validacion": "pendiente",
    "manual_oem": "Corpus multimarca preliminar",
}


def _fusionar(meta=META_PRELIMINAR, similitud=0.99, validada=False):
    return PoliticaFusionDiagnostica.fusionar_evidencia(
        sintoma_texto="El motor recalienta en tráfico",
        predicciones_ml=FALLAS,
        macro_sistema_ml="MOTOR",
        rag_meta=meta,
        rag_similitud=similitud,
        rag_evidencia_validada=validada,
    )


def test_rag_preliminar_con_similitud_alta_no_reemplaza_top1_ni_agrega_causa():
    resultado = _fusionar()

    assert resultado.falla_principal == FALLAS[0]["falla"]
    assert resultado.confianza_final == FALLAS[0]["probabilidad"]
    assert [item["falla"] for item in resultado.diferenciales] == [
        FALLAS[1]["falla"], FALLAS[2]["falla"]
    ]
    assert [item["probabilidad"] for item in resultado.diferenciales] == [0.31, 0.14]
    assert all(item["origen_probabilidad"] == "SVM" for item in resultado.diferenciales)


def test_rag_no_influye_si_fuente_es_valida_pero_sistema_o_umbral_no_coinciden():
    meta_otro_sistema = {
        **META_PRELIMINAR,
        "falla": "Disco de embrague desgastado o patinando",
        "sistema": "TRANSMISION",
    }

    assert _fusionar(meta=meta_otro_sistema, validada=True).falla_principal == FALLAS[0]["falla"]
    assert _fusionar(similitud=0.79, validada=True).falla_principal == FALLAS[0]["falla"]


def test_macro_declarado_no_puede_encubrir_una_falla_de_otro_sistema():
    meta_sistema_mentiroso = {
        **META_PRELIMINAR,
        "falla": "Disco de embrague desgastado o patinando",
        "sistema": "MOTOR",
    }

    resultado = _fusionar(meta=meta_sistema_mentiroso, validada=True, similitud=0.95)

    assert resultado.falla_principal == FALLAS[0]["falla"]
    assert all(item["falla"] != meta_sistema_mentiroso["falla"] for item in resultado.diferenciales)


def test_rag_validado_mismo_sistema_solo_reordena_candidato_y_conserva_su_score_svm():
    meta_validada = {
        **META_PRELIMINAR,
        "estado_validacion": "validado_oem_taller",
        "manual_oem": "Manual OEM Mazda",
        "auditoria": {
            "verificado_documental": True,
            "auditoria_mecanica_formal_firmada": True,
        },
    }

    resultado = _fusionar(meta=meta_validada, similitud=0.91, validada=True)

    assert resultado.falla_principal == FALLAS[1]["falla"]
    assert resultado.confianza_final == FALLAS[1]["probabilidad"]
    assert resultado.origen_confianza == "SVM"
    assert [item["probabilidad"] for item in resultado.diferenciales] == [0.55, 0.14]


def test_causa_elegida_por_regla_no_se_presenta_como_porcentaje_svm():
    hipotesis = [
        {"falla": "Termostato priorizado por hallazgo", "probabilidad": 0.0, "origen_probabilidad": "REGLA"},
        {"falla": FALLAS[0]["falla"], "probabilidad": 0.55, "origen_probabilidad": "SVM"},
    ]
    respuesta = FormateadorCompacto.formatear_respuesta_diagnostico(
        hipotesis,
        sintoma_original="Recalienta y la manguera inferior está fría",
        pregunta_personalizada="¿Puedes verificar circulación?",
    )
    prompt = construir_prompt_diagnostico(
        pregunta_llm="Recalienta y la manguera inferior está fría",
        diagnostico_ml="Termostato priorizado por hallazgo",
        confianza_pct=0,
        titulo_manual="Sin procedimiento validado",
        contexto_llm="",
        alerta_revision="",
        predicciones_ml=[PrediccionML(**item) for item in hipotesis],
    )

    assert "priorizada por evidencia; sin porcentaje SVM" in respuesta
    assert "Termostato priorizado por hallazgo (priorizada por evidencia; sin porcentaje SVM)" in prompt
    assert "Termostato priorizado por hallazgo (0%" not in prompt


class _ModeloSintetico:
    def predecir_top_fallas(self, texto, limite=3):
        return FALLAS[:limite]


class _RagSintetico:
    corpus_validado = False

    def recuperar_procedimiento_hibrido(self, **_):
        return (
            "Fragmento exploratorio preliminar sobre circulación de refrigerante.",
            "RAG preliminar de bomba de agua",
            0.99,
            # Este caso aísla la política de fuente no validada. La eliminación
            # por contradicción con una falla RAG específica se prueba aparte.
            {**META_PRELIMINAR, "falla": None},
        )


def test_text_processor_preserva_recuperacion_exploratoria_pero_no_la_inyecta():
    gestor = GestorDiagnostico(modelo_ml=_ModeloSintetico(), motor_rag=_RagSintetico())
    gestor.api_key = ""
    gestor._registrar_en_tracker = lambda **_: None
    llamadas_llm = []

    def respuesta_determinista(**kwargs):
        llamadas_llm.append(kwargs)
        return "Respuesta segura simulada.", {"usado": False, "modo": "prueba_local"}

    gestor._generar_respuesta_con_metadatos = respuesta_determinista

    resultado = gestor.procesar_consulta_texto(
        "El motor recalienta en tráfico y pierde refrigerante",
        placa="TST000",
        marca_modelo="Mazda 3",
        proveedor="local",
    )

    assert resultado.diagnostico_ml == FALLAS[0]["falla"]
    assert resultado.confianza_ml == 0.55
    assert resultado.origen_confianza == "SVM"
    assert resultado.contexto_manual.startswith("Fragmento exploratorio")
    assert resultado.contexto_manual_verificado == ""
    assert llamadas_llm and llamadas_llm[0]["contexto_manual"] == ""
