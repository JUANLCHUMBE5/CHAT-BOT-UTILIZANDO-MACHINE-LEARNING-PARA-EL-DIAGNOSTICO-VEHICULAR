"""Pruebas de regresión para las observaciones finales del PR #22.

Verifica:
1. Escenario Volkswagen Amarok (INEDITA_02):
   - Retención de filtro_descartado.
   - Retención de retorno_anomalo_inyector3.
   - No mezcla de mediciones entre inyectores (inyector 3: 65 ml vs otros inyectores: 15 ml).
2. Prevención de sobreescritura errónea del modelo vehicular por palabras adyacentes ("Toyota especifica").
3. Casos fuera de distribución (OOD) y falsa confianza:
   - CASO_21 (GLP): No propone bomba de gasolina cuando opera normal a gasolina.
   - CASO_25 (Suspensión): No propone motor de arranque ante ruidos en rompemuelles/baches.
   - CASO_07 (Inmovilizador): No propone batería descargada cuando el motor gira con fuerza.
   - Descarte de falsa alarma de incendio cuando el mecánico reporta explícitamente ausencia de fugas.
"""

from src.core.conversacion.extraccion_hechos.actualizador_estado import extraer_y_actualizar
from src.core.conversacion.models import ConversationState, FactState
from src.core.conversacion.validador_compatibilidad import ValidadorCompatibilidad
from src.core.diagnostico.politica_seguridad import PoliticaSeguridad, SeveridadSeguridad


def test_amarok_filtro_descartado_y_retorno_inyector_aislado():
    estado = ConversationState(session_id="test_amarok_01")
    
    # Turno 1: Filtro de combustible nuevo recién cambiado
    msg_filtro = "El filtro de combustible es nuevo original recién cambiado hace 3 días"
    extraer_y_actualizar(estado, msg_filtro)
    
    assert "filtro_descartado" in estado.hechos
    assert estado.hechos["filtro_descartado"].estado == FactState.DESCARTADO
    assert any("filtro" in d for d in estado.hipotesis_descartadas)

    # Turno 2: Prueba de retorno de probetas con inyector 3 anómalo
    msg_retorno = "Puse las 4 probetas de retorno y en 2 minutos de ralentí el inyector 3 llenó 65 ml mientras los otros tres marcaron 15 ml"
    extraer_y_actualizar(estado, msg_retorno)

    assert "retorno_anomalo_inyector3" in estado.hechos
    # Verificar aislamiento metrológico: inyector 3 no debe mezclarse con otros
    assert "medicion_retorno_inyector_3" in estado.hechos or any("inyector_3" in m.get("contexto", "") for m in estado.measurements.values())


def test_no_sobreescribir_modelo_con_palabras_adyacentes():
    estado = ConversationState(session_id="test_modelo_01")
    # Inicialmente se conoce Toyota Hilux
    extraer_y_actualizar(estado, "Tengo una Toyota Hilux 2018")
    assert estado.marca == "Toyota"
    assert estado.modelo == "Hilux"

    # Usuario cita el manual técnico
    extraer_y_actualizar(estado, "El manual de Toyota especifica una presión mínima de 30 PSI")
    # El modelo no debe cambiarse a 'Especifica'
    assert estado.modelo == "Hilux"


def test_ood_glp_no_propone_bomba_gasolina():
    estado = ConversationState(session_id="test_glp_01")
    estado.combustible = "Dual GLP"
    estado.historial_mensajes_usuario.append(
        "Toyota Corolla 2015 dual GLP a gasolina anda perfecto pero cuando conmuta a gas empieza a cabecear feo"
    )

    falla_bomba = "Bomba de gasolina quemada o con baja presion"
    es_comp, motivo = ValidadorCompatibilidad.validar_compatibilidad_hipotesis(falla_bomba, estado)
    
    assert es_comp is False
    assert "El vehículo opera correctamente en gasolina" in (motivo or "")


def test_ood_suspension_no_propone_motor_arranque():
    estado = ConversationState(session_id="test_susp_01")
    estado.historial_mensajes_usuario.append(
        "Kia Rio 2017 suena un clac clac seco en la rueda delantera izquierda al pasar rompemuelles o pistas rotas"
    )

    falla_arranque = "Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)"
    es_comp, motivo = ValidadorCompatibilidad.validar_compatibilidad_hipotesis(falla_arranque, estado)

    assert es_comp is False
    assert "ruido en rodamiento/suspensión" in (motivo or "")


def test_ood_gira_con_fuerza_no_propone_bateria_descargada():
    estado = ConversationState(session_id="test_immo_01")
    estado.historial_mensajes_usuario.append(
        "Ford Fiesta 2015 gira motor con fuerza pero no arranca nada"
    )

    falla_bateria = "Bateria descargada o bornes sulfatados"
    es_comp, motivo = ValidadorCompatibilidad.validar_compatibilidad_hipotesis(falla_bateria, estado)

    assert es_comp is False
    assert "gira con fuerza" in (motivo or "")


def test_seguridad_no_dispara_incendio_si_se_niega_fuga():
    msg = "Abrí la llave del tanque, rocié agua jabonosa en todas las uniones y no hay ninguna fuga de combustible"
    sev, banner = PoliticaSeguridad.evaluar_severidad(msg, "Aclaración técnica")

    assert sev != SeveridadSeguridad.CRITICAL_STOP
    assert banner is None or "INCENDIO" not in banner
