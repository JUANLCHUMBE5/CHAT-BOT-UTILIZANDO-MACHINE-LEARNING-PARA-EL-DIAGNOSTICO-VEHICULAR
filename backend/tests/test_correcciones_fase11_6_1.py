"""
Batería de Pruebas Unitarias de Fase 11.6.1: Correcciones Dirigidas Pre-Campo.
Verifica los 10 comportamientos críticos requeridos (A - J) para prevenir regresiones.
"""

import pytest

from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.fixture(scope="module")
def gestor():
    return GestorDiagnostico()


def test_a_dar_arranque_no_es_motor_de_arranque(gestor):
    """Test A: 'le doy arranque pero no prende' debe interpretarse como acción del chofer y no como motor de arranque.

    En diagnóstico progresivo (Fase 14-16), ante la frase ambigua breve, CarBot emite
    una auto-pregunta de descarte para precisar la causa (bomba, encendido, CKP), sin culpar
    al motor de arranque. Al confirmar el giro del motor en el siguiente turno, diagnostica
    sistema de combustible o encendido.
    """
    txt = "le doy arranque pero no prende"
    res = gestor.procesar_consulta_texto(txt, session_id="test_a", proveedor="web")
    # 1. No debe culpar al motor de arranque en el diagnóstico ni en la respuesta
    assert "motor de arranque" not in res.diagnostico_ml.lower()
    assert "motor de arranque" not in res.respuesta_texto.lower()

    # 2. Si emite auto-pregunta técnica de descarte, debe orientarse a combustible/encendido/sensores
    if "auto-pregunta" in res.diagnostico_ml.lower():
        assert any(c in res.respuesta_texto.lower() for c in ("bomba", "gasolina", "combustible", "bujia", "encendido", "sensor", "ckp"))
        # Turno 2: el mecánico aclara que el motor gira normalmente
        res_t2 = gestor.procesar_consulta_texto("el motor si gira normalmente pero no enciende", session_id="test_a", proveedor="web")
        assert "motor de arranque" not in res_t2.diagnostico_ml.lower()
        assert any(c in res_t2.diagnostico_ml.lower() for c in ("bomba", "gasolina", "combustible", "bujia", "encendido"))
    else:
        assert any(c in res.diagnostico_ml.lower() for c in ("bomba", "gasolina", "combustible", "bujia", "encendido"))


def test_b_motor_gira_al_dar_arranque(gestor):
    """Test B: 'el motor gira normalmente al dar arranque pero no enciende' debe descartar arrancador."""
    txt = "el motor gira normalmente al dar arranque pero no enciende"
    res = gestor.procesar_consulta_texto(txt, session_id="test_b", proveedor="web")
    assert "motor de arranque" not in res.diagnostico_ml.lower()
    assert any(c in res.diagnostico_ml.lower() for c in ("bomba", "gasolina", "combustible", "bujia", "encendido"))


def test_c_vehiculo_en_movimiento_no_arrancador(gestor):
    """Test C: 'voy a 90 km/h y vibra' ocurre en marcha, no puede ser motor de arranque."""
    txt = "voy a 90 km/h y vibra"
    res = gestor.procesar_consulta_texto(txt, session_id="test_c", proveedor="web")
    assert "motor de arranque" not in res.diagnostico_ml.lower()
    assert any(c in res.diagnostico_ml.lower() for c in ("llanta", "desbalanceada", "suspension", "disco", "rodaje", "maza"))


def test_d_subiendo_pendiente_rpm_suben_embrague(gestor):
    """Test D: 'subiendo una pendiente las RPM suben pero el carro no avanza' es embrague patinando."""
    txt = "subiendo una pendiente las RPM suben pero el carro no avanza"
    res = gestor.procesar_consulta_texto(txt, session_id="test_d", proveedor="web")
    assert "Disco de embrague desgastado o patinando" == res.diagnostico_ml
    assert "motor de arranque" not in res.diagnostico_ml.lower()


def test_e_volante_vibra_pero_al_frenar_no_vibra(gestor):
    """Test E: 'el volante vibra pero al frenar no vibra' debe descartar discos alabeados y favorecer llantas."""
    txt = "el volante vibra pero al frenar no vibra"
    res = gestor.procesar_consulta_texto(txt, session_id="test_e", proveedor="web")
    assert "Discos de freno alabeados" not in res.diagnostico_ml
    assert "Llantas desbalanceadas o desalineadas" == res.diagnostico_ml


def test_f_bujias_nuevas_pero_bobina_falla(gestor):
    """Test F: 'las bujías son nuevas pero una bobina no genera chispa' mantiene la clase de bujías/bobinas."""
    txt = "las bujías son nuevas pero una bobina no genera chispa"
    res = gestor.procesar_consulta_texto(txt, session_id="test_f", proveedor="web")
    assert "Falla en bujias o bobinas de encendido (misfire)" == res.diagnostico_ml
    assert "Perdida de compresion" not in res.diagnostico_ml


def test_g_dtc_p0171_ralenti_inestable(gestor):
    """Test G: P0171 + ralentí inestable no debe ser cuerpo de aceleración, debe orientar a mezcla pobre."""
    txt = "Se detectó código DTC P0171 sistema demasiado pobre en banco 1. El motor tiene ralentí inestable y consumo elevado."
    res = gestor.procesar_consulta_texto(txt, session_id="test_g", proveedor="web")
    assert "Cuerpo de aceleracion" not in res.diagnostico_ml
    assert any(c in res.diagnostico_ml.lower() for c in ("oxigeno", "mezcla", "servofreno", "booster", "bomba de gasolina", "regulador"))


def test_h_dtc_p0172_consumo_elevado(gestor):
    """Test H: P0172 + consumo elevado debe orientar a mezcla rica / sensor O2 / regulador."""
    txt = "Código DTC P0172 sistema demasiado rico en banco 1 con fuerte olor a nafta y consumo elevado."
    res = gestor.procesar_consulta_texto(txt, session_id="test_h", proveedor="web")
    assert any(c in res.diagnostico_ml.lower() for c in ("oxigeno", "mezcla rica", "regulador", "inyector"))


def test_i_caso_ambiguo_sobrecalentamiento(gestor):
    """Test I: caso ambiguo de sobrecalentamiento debe manejar incertidumbre sin afirmar certeza única absoluta."""
    txt = "El carro empieza a levantar temperatura cuando estoy detenido en el tráfico."
    res = gestor.procesar_consulta_texto(txt, session_id="test_i", proveedor="web")
    # Debe tener alternativas diferenciales claras o solicitar clarificación
    assert res.predicciones_ml and len(res.predicciones_ml) >= 2
    # El macro sistema debe ser MOTOR
    from src.core.diagnostico.taxonomia_sistemas import obtener_macro_sistema
    assert obtener_macro_sistema(res.diagnostico_ml) == "MOTOR"


def test_j_caso_ambiguo_no_arranque(gestor):
    """Test J: caso ambiguo de no-arranque debe considerar batería, alternador o motor de arranque."""
    txt = "El carro no arranca por las mañanas cuando hace frío."
    res = gestor.procesar_consulta_texto(txt, session_id="test_j", proveedor="web")
    assert res.predicciones_ml and len(res.predicciones_ml) >= 2
    from src.core.diagnostico.taxonomia_sistemas import obtener_macro_sistema
    macro = obtener_macro_sistema(res.diagnostico_ml)
    assert macro in ("ELECTRICO", "MOTOR")
