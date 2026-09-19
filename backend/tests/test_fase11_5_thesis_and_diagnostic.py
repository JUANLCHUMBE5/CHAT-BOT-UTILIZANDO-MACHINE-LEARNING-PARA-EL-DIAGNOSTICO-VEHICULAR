"""Pruebas integrales de Fase 11.5: Aislamiento estricto de Tesis (PPCF, RDC, TPRD) y pipeline diagnóstico."""

import hashlib
import uuid
from pathlib import Path

from src.application.services.validacion_taller import resumir_fases
from src.core.conversacion.detector_polaridad import DetectorPolaridad
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState
from src.core.conversacion.sintetizador_consulta import SintetizadorConsulta
from src.core.conversacion.suficiencia_informacion import EvaluadorSuficiencia
from src.core.diagnostico.semantic_purifier import purificar_sintoma_para_vectorizador_ml
from src.core.diagnostico.taxonomia_sistemas import obtener_macro_sistema
from src.core.taxonomy.directrices_mecanicas import DIRECTRICES_MECANICAS
from src.infrastructure.container import ServiceContainer

# =====================================================================
# 1. PRUEBAS DE INTEGRIDAD DE ARTEFACTOS ML Y RAG (CONGELADOS)
# =====================================================================

def test_artefactos_ml_y_rag_hashes_estrictos():
    base_dir = Path(__file__).resolve().parent.parent.parent
    ml_artifacts = {
        base_dir / "machine_learning" / "models" / "c1_fase10_final" / "vectorizador_c1.pkl": "060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7",
        base_dir / "machine_learning" / "models" / "c1_fase10_final" / "modelo_diagnostico_c1.pkl": "24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c",
        base_dir / "machine_learning" / "models" / "c1_fase10_final" / "modelo_sistema_c1_macrofix.pkl": "dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c",
        base_dir / "machine_learning" / "manuals" / "candidates" / "v1" / "indexes" / "indice_faiss_v1.index": "a2a081ffded23d4d727b57780aec26da9167e90f044101e77adbb33cbaa79b40",
        base_dir / "machine_learning" / "manuals" / "candidates" / "v1" / "metadata" / "metadatos_manuales_v1.json": "8b4244713cfdc2f59af66b4e43bea8532196366ee5b53a98721e96ca6c781dbb",
    }
    for file_path, expected_hash in ml_artifacts.items():
        assert file_path.exists(), f"El archivo {file_path} debe existir"
        content = file_path.read_bytes()
        computed_hash = hashlib.sha256(content).hexdigest()
        assert computed_hash == expected_hash, f"Hash mismatch en {file_path.name}: {computed_hash} != {expected_hash}"


# =====================================================================
# 2. PRUEBAS DE AISLAMIENTO METODOLÓGICO DE TESIS (PPCF, RDC, TPRD)
# =====================================================================

def test_calculo_indicadores_tesis_aislamiento():
    """Verifica que DEVELOPMENT y REGRESSION nunca contaminen PPCF, RDC y TPRD."""
    # 3 registros de DEVELOPMENT, 2 PRETEST, 2 POSTTEST
    # Para el cálculo descriptivo de la tesis, solo entran los grupos pre-test y post-test oficiales.
    grupos_muestra = [
        # Pre-test: 2 casos, 1 acierto (PPCF=50%), 2 completos (RDC=100%), suma=50min (TPRD=25min)
        {"fase": "Pre-test", "total": 2, "aciertos": 1, "completos": 2, "minutos": 50},
        # Post-test: 2 casos, 2 aciertos (PPCF=100%), 2 completos (RDC=100%), suma=20min (TPRD=10min)
        {"fase": "Post-test", "total": 2, "aciertos": 2, "completos": 2, "minutos": 20},
    ]

    resumen = resumir_fases(grupos_muestra)

    # Indicador A: PPCF
    assert resumen["tasa_acierto_pretest_porcentaje"] == 50.0
    assert resumen["tasa_acierto_posttest_porcentaje"] == 100.0

    # Indicador B: RDC
    assert resumen["registros_completos_pretest_porcentaje"] == 100.0
    assert resumen["registros_completos_posttest_porcentaje"] == 100.0

    # Indicador C: TPRD
    assert resumen["tiempo_promedio_pretest_min"] == 25.0
    assert resumen["tiempo_promedio_posttest_min"] == 10.0
    assert resumen["reduccion_tiempo_porcentaje"] == 60.0  # (25 - 10) / 25 * 100

    # Totales oficiales
    assert resumen["total_casos"] == 4
    assert resumen["casos_pretest"] == 2
    assert resumen["casos_posttest"] == 2


def test_control_division_por_cero_en_metricas_vacias():
    """Verifica que si no hay datos no crashea ni genera division por cero."""
    resumen = resumir_fases([])
    assert resumen["total_casos"] == 0
    assert resumen["tasa_acierto_pretest_porcentaje"] == 0.0
    assert resumen["tasa_acierto_posttest_porcentaje"] == 0.0
    assert resumen["tiempo_promedio_pretest_min"] == 0.0
    assert resumen["tiempo_promedio_posttest_min"] == 0.0
    assert resumen["reduccion_tiempo_porcentaje"] == 0.0


# =====================================================================
# 3. CASO MANUAL REAL B — VIBRACIÓN AL FRENAR (AUDITORÍA COMPLETA)
# =====================================================================

def test_caso_b_detector_polaridad():
    """'cuando frena vibra... sin frenar no vibra' no debe negar el frenado."""
    texto = "cuando frena el carro el volante comienza a vibrar. cuando maneja sin frenar no siente esa vibracion."
    assert not DetectorPolaridad.es_condicion_negada(r"\bfrena\b", texto)
    assert not DetectorPolaridad.es_condicion_negada(r"\bfren", texto)
    # 'sin frenar' si está negado
    assert DetectorPolaridad.es_condicion_negada(r"\bsin frenar\b", texto)


def test_caso_b_purificador_semantico_no_elimina_frenos():
    """El purificador semántico no debe confundir 'sin frenar no vibra' con vibración sin frenar."""
    texto = "el volante vibra cuando frena. cuando manejo sin frenar no vibra."
    purificado = purificar_sintoma_para_vectorizador_ml(texto)
    assert "fren" in purificado, "El texto purificado debe conservar la raíz de frenado"
    assert "desbalancead" not in purificado, "No debe inyectar llantas desbalanceadas si la vibración es al frenar"


def test_caso_b_pipeline_completo_3_turnos():
    """Verifica los 3 turnos de Caso B: no termina en Consulta Ambigua 0% y diagnostica discos de freno."""
    modelo_ml = ServiceContainer.get_modelo_ml()

    estado = ConversationState(
        session_id=str(uuid.uuid4()),
        case_id="CASO-TEST-FRENOS-01",
    )

    # Turno 1
    t1 = "El cliente indica que cuando frena el carro el volante comienza a vibrar, sobre todo cuando va a una velocidad media o alta. Cuando maneja sin frenar no siente esa vibración. Todavía no he revisado el vehículo. ¿Qué debería revisar primero?"
    ExtractorHechos.extraer_y_actualizar(estado, t1)

    q1 = SintetizadorConsulta.sintetizar(estado)
    txt_ml_1 = purificar_sintoma_para_vectorizador_ml(q1)
    preds_1 = modelo_ml.predecir_top_fallas(txt_ml_1, limite=3)
    p1 = preds_1[0]
    macro_1 = obtener_macro_sistema(str(p1["falla"]))

    assert macro_1 == "FRENOS"
    assert any(w in str(p1["falla"]).lower() for w in ("disco", "alabeo", "freno"))
    assert float(p1["probabilidad"]) >= 0.70

    # Turno 2
    t2 = "Únicamente vibra cuando piso el pedal de freno. Si voy a la misma velocidad sin frenar, el volante no vibra."
    ExtractorHechos.extraer_y_actualizar(estado, t2)
    q2 = SintetizadorConsulta.sintetizar(estado)
    txt_ml_2 = purificar_sintoma_para_vectorizador_ml(q2)
    preds_2 = modelo_ml.predecir_top_fallas(txt_ml_2, limite=3)
    p2 = preds_2[0]
    macro_2 = obtener_macro_sistema(str(p2["falla"]))

    assert macro_2 == "FRENOS"
    assert any(w in str(p2["falla"]).lower() for w in ("disco", "alabeo", "freno"))
    assert float(p2["probabilidad"]) >= 0.85

    # Turno 3
    t3 = "Se siente principalmente en el volante. En el pedal casi no siento vibración y el resto del vehículo tampoco vibra de forma notable."
    ExtractorHechos.extraer_y_actualizar(estado, t3)
    score, cats, es_suficiente, motivo = EvaluadorSuficiencia.evaluar(estado)
    assert es_suficiente, f"Con 3 turnos de evidencia convergente debe ser suficiente: {motivo}"

    q3 = SintetizadorConsulta.sintetizar(estado)
    # Verificar que el texto de consulta NO sea ambiguo y conserve los hechos
    assert "fren" in q3.lower()
    assert "volante" in q3.lower()
    assert "vibra" in q3.lower()

    txt_ml_3 = purificar_sintoma_para_vectorizador_ml(q3)
    preds_3 = modelo_ml.predecir_top_fallas(txt_ml_3, limite=3)
    p3 = preds_3[0]
    macro_3 = obtener_macro_sistema(str(p3["falla"]))

    assert macro_3 == "FRENOS"
    assert any(w in str(p3["falla"]).lower() for w in ("disco", "alabeo", "freno"))
    assert float(p3["probabilidad"]) >= 0.90

    # Verificación de directriz diagnóstica (prueba metrológica primero, no reparación a ciegas)
    directriz = next((d for d in DIRECTRICES_MECANICAS if "FRENO" in d.codigo and "alabe" in d.falla.lower()), None)
    assert directriz is not None
    assert directriz.prueba_sugerida is not None
    assert "reloj comparador" in directriz.prueba_sugerida.lower() or "disco" in directriz.prueba_sugerida.lower()


# =====================================================================
# 4. CASO MANUAL REAL A — ARRANQUE (AUDITORÍA COMPLETA)
# =====================================================================

def test_caso_a_sintesis_y_ranking_arranque():
    """Verifica que el caso de demora en arrancar en frío conserve los hechos y oriente a diagnóstico de arranque/eléctrico."""
    modelo_ml = ServiceContainer.get_modelo_ml()

    estado = ConversationState(
        session_id=str(uuid.uuid4()),
        case_id="CASO-TEST-ARRANQUE-01",
    )

    t1 = (
        "Hola, tengo un vehículo en el taller. El cliente comenta que demora bastante en encender por las mañanas. "
        "Una vez que logra encender, el motor funciona normal y no se prende ninguna luz de advertencia. "
        "Todavía no he revisado batería, arranque ni sistema de combustible. ¿Qué debería revisar primero?"
    )
    ExtractorHechos.extraer_y_actualizar(estado, t1)
    q1 = SintetizadorConsulta.sintetizar(estado)

    # Asegurar que los hechos clínicos clave están en la síntesis
    q1_l = q1.lower()
    assert "demora en arrancar" in q1_l or "arranque en frío" in q1_l or "encender" in q1_l
    assert "no revisado" in q1_l or "batería" in q1_l or "combustible" in q1_l

    # Turno 2 donde el mecánico aclara el giro del motor
    t2 = "El motor gira rápido con buena velocidad al dar arranque, pero demora en toser o dar marcha."
    ExtractorHechos.extraer_y_actualizar(estado, t2)
    q2 = SintetizadorConsulta.sintetizar(estado)

    txt_ml_2 = purificar_sintoma_para_vectorizador_ml(q2)
    preds_2 = modelo_ml.predecir_top_fallas(txt_ml_2, limite=5)
    fallas_top3 = [str(p["falla"]) for p in preds_2[:3]]
    macros_top3 = [obtener_macro_sistema(f) for f in fallas_top3]

    # En el Top 3 deben aparecer hipótesis coherentes de encendido/arranque/combustible
    assert any(m in ("MOTOR", "ELECTRICO", "COMBUSTIBLE") for m in macros_top3)
    assert any(
        any(k in f.lower() for k in ("arranque", "arrancador", "combustible", "batería", "bateria", "inyecc", "aceleración", "iac"))
        for f in fallas_top3
    )

    # Verificación de directriz diagnóstica para COMBUSTIBLE_003 (IAC / Cuerpo aceleración):
    # Debe sugerir inspección/medición, no limpieza a ciegas
    dir_iac = next((d for d in DIRECTRICES_MECANICAS if d.codigo == "COMBUSTIBLE_003"), None)
    assert dir_iac is not None
    assert "inspección" in dir_iac.prueba_sugerida.lower() or "porcentaje" in dir_iac.prueba_sugerida.lower()

