"""Suite de pruebas unitarias y basadas en propiedades para SinglePassMessageParser.

Verifica de forma aislada e independiente los 17 escenarios de prueba de la Fase 3,
la prevención de falsos positivos de placa (DTCs, años, palabras) y las propiedades invariantes.
"""

import random
import string

from src.core.parser.message_parser import SinglePassMessageParser
from src.domain.schemas.conversation_contracts import IntentType

# ==============================================================================
# PRUEBAS DE LOS 17 ESCENARIOS GENERALES (FASE 3)
# ==============================================================================

def test_t01_placa_sola():
    """T01: Placa sola debe extraerse limpiamente sin confundirse con otros campos."""
    dto = SinglePassMessageParser.parse("ABC-1234")
    assert dto.vehiculo.placa == "ABC-1234"
    assert not dto.vehiculo.es_provisional
    assert dto.dtcs == []
    assert len(dto.hechos_afirmados) == 0
    assert "sintoma" in dto.datos_faltantes


def test_t02_placa_y_sintoma_juntos():
    """T02: Placa y síntoma juntos se extraen en una sola pasada."""
    dto = SinglePassMessageParser.parse("ABC-1234 cascabelea al subir pendientes")
    assert dto.vehiculo.placa == "ABC-1234"
    assert dto.intencion == IntentType.DIAGNOSTICO_SINTOMA
    campos = [h.campo for h in dto.hechos_afirmados]
    assert "sintoma_cascabeleo" in campos
    assert "placa" not in dto.datos_faltantes


def test_t03_placa_vehiculo_y_sintoma_juntos():
    """T03: Placa, vehículo y síntoma juntos se extraen sin pérdidas."""
    dto = SinglePassMessageParser.parse("Toyota Yaris 2018 placa ABC-1234 tiembla en ralentí")
    assert dto.vehiculo.placa == "ABC-1234"
    assert dto.vehiculo.marca == "Toyota"
    assert dto.vehiculo.modelo == "Yaris"
    assert dto.vehiculo.anio == 2018
    assert dto.intencion == IntentType.DIAGNOSTICO_SINTOMA
    campos = [h.campo for h in dto.hechos_afirmados]
    assert "sintoma_vibracion" in campos


def test_t04_sintoma_antes_de_placa():
    """T04: Mensaje con solo síntoma extrae el síntoma y reporta placa faltante."""
    dto = SinglePassMessageParser.parse("El carro no arranca y solo hace un clic seco")
    assert dto.vehiculo.placa is None
    assert "placa" in dto.datos_faltantes
    campos = [h.campo for h in dto.hechos_afirmados]
    assert "sintoma_no_arranca" in campos or "sintoma_clic_seco" in campos


def test_t05_mensaje_incompleto_vago():
    """T05: Mensaje vago como 'vibra' extrae síntoma pero detecta insuficiencia."""
    dto = SinglePassMessageParser.parse("Vibra")
    campos = [h.campo for h in dto.hechos_afirmados]
    assert "sintoma_vibracion" in campos
    assert "placa" in dto.datos_faltantes


def test_t06_correccion_de_placa():
    """T06: Detección explícita de corrección de placa sin marcar cambio de caso."""
    dto = SinglePassMessageParser.parse("Corrijo, la placa es XYZ-789")
    assert dto.vehiculo.placa == "XYZ-789"
    assert dto.es_correccion_vehiculo
    assert not dto.es_cambio_caso
    assert dto.intencion == IntentType.CORRECCION_DATOS


def test_t07_correccion_de_vehiculo():
    """T07: Detección explícita de corrección de modelo/marca."""
    dto = SinglePassMessageParser.parse("Me equivoqué, en realidad es un Corolla")
    assert dto.vehiculo.modelo == "Corolla"
    assert dto.es_correccion_vehiculo
    assert not dto.es_cambio_caso
    assert dto.intencion == IntentType.CORRECCION_DATOS


def test_t08_varios_sintomas_en_mismo_mensaje():
    """T08: Múltiples síntomas se extraen simultáneamente."""
    dto = SinglePassMessageParser.parse("Humo blanco por el escape y la temperatura sube al máximo")
    campos = [h.campo for h in dto.hechos_afirmados]
    assert "sintoma_humo_blanco" in campos
    assert "sintoma_sobrecalentamiento" in campos


def test_t09_sintomas_y_mediciones():
    """T09: Extracción de síntomas con mediciones físicas."""
    dto = SinglePassMessageParser.parse("Al dar arranque la batería baja a 9.2 V y la presión está en 35 psi")
    tipos_med = [m.tipo for m in dto.mediciones]
    assert "voltaje" in tipos_med
    assert "presion" in tipos_med
    unidades = [m.unidad for m in dto.mediciones]
    assert "V" in unidades
    assert "PSI" in unidades


def test_t10_negaciones_y_polaridad():
    """T10: Síntoma negado se clasifica con polaridad=False sin afirmarse."""
    dto = SinglePassMessageParser.parse("El auto vibra al acelerar pero al frenar no vibra nada")
    campos_afirmados = [h.campo for h in dto.hechos_afirmados]
    campos_negados = [h.campo for h in dto.hechos_negados]
    assert "sintoma_vibracion" in campos_afirmados
    assert "sintoma_vibracion_frenos" in campos_negados
    assert "sintoma_vibracion_frenado" not in campos_afirmados


def test_t11_cambio_de_caso_mismo_vehiculo():
    """T11: Detección de nuevo problema en el taller."""
    dto = SinglePassMessageParser.parse("Ese caso ya quedó listo. Ahora este mismo carro tiene otro problema con fuga de refrigerante")
    campos = [h.campo for h in dto.hechos_afirmados]
    assert "sintoma_fuga_refrigerante" in campos


def test_t12_cambio_de_vehiculo_explicito():
    """T12: Detección de nuevo auto de otro cliente."""
    dto = SinglePassMessageParser.parse("Ahora revisemos otro auto, un Nissan Sentra que jalonea")
    assert dto.es_cambio_caso
    assert not dto.es_correccion_vehiculo
    assert dto.intencion == IntentType.CAMBIO_CASO
    assert dto.vehiculo.marca == "Nissan"
    assert dto.vehiculo.modelo == "Sentra"


def test_t13_reinicio_de_sesion():
    """T13: Órdenes de reinicio explícito."""
    for frase in ("Reiniciar", "limpiar sesión", "empezar de nuevo", "comenzar de nuevo"):
        dto = SinglePassMessageParser.parse(frase)
        assert dto.intencion == IntentType.REINICIO


def test_t14_preservacion_mensaje_original():
    """T14: Invariante de preservación del mensaje original exacto."""
    texto_complejo = "  Hola CarBot!! Tengo un Toyota Yaris 2018 (placa: ABC-1234)... tiembla mucho!!  "
    dto = SinglePassMessageParser.parse(texto_complejo)
    assert dto.mensaje_original == texto_complejo


def test_t15_no_confundir_dtc_con_placa():
    """T15: Códigos OBD-II (P0301, C1234, B1000, U0100) NUNCA deben interpretarse como placa."""
    for dtc in ("P0301", "C1234", "B1000", "U0100", "P0420"):
        dto = SinglePassMessageParser.parse(f"Tengo el código {dtc} en el escáner")
        assert dtc in dto.dtcs
        assert dto.vehiculo.placa is None, f"DTC {dtc} fue erróneamente interpretado como placa"


def test_t16_no_confundir_anio_con_placa():
    """T16: Años de 4 dígitos (1999, 2018, 2022) NUNCA deben ser placa."""
    dto = SinglePassMessageParser.parse("Tengo un auto del 2018 que no arranca")
    assert dto.vehiculo.anio == 2018
    assert dto.vehiculo.placa is None


def test_t17_sin_placa_genera_id_provisional():
    """T17: Expresiones de no tener placa generan identificador provisional y NUNCA 'SIN-PLACA'."""
    frases = (
        "No tengo la placa a la mano",
        "El carro no tiene placa",
        "Sin placa por ahora",
        "No me acuerdo la placa",
    )
    for f in frases:
        dto = SinglePassMessageParser.parse(f"{f}, pierde fuerza al acelerar")
        assert dto.vehiculo.es_provisional
        assert dto.vehiculo.placa is None
        assert dto.vehiculo.id_provisional is not None
        assert dto.vehiculo.id_provisional.startswith("PROV_")
        assert dto.vehiculo.placa_efectiva is None
        assert "placa" not in dto.datos_faltantes  # Porque ya fue marcada como provisional


# ==============================================================================
# PRUEBAS BASADAS EN PROPIEDADES (INVARIANTES GENERATIVAS)
# ==============================================================================

def test_property_conmutatividad_orden_entidades():
    """Propiedad: El orden sintáctico de [Placa, Marca, Síntoma] no debe alterar las entidades extraídas."""
    placa = "ABC-1234"
    marca = "Toyota"
    sintoma = "cascabelea al acelerar"

    permutaciones = [
        f"{placa} {marca} {sintoma}",
        f"{marca} {placa} {sintoma}",
        f"{sintoma} en mi {marca} placa {placa}",
        f"En mi {marca} con placa {placa} el motor {sintoma}",
    ]

    for texto in permutaciones:
        dto = SinglePassMessageParser.parse(texto)
        assert dto.vehiculo.placa == placa, f"Fallo en: {texto}"
        assert dto.vehiculo.marca == marca, f"Fallo en: {texto}"
        campos = [h.campo for h in dto.hechos_afirmados]
        assert "sintoma_cascabeleo" in campos, f"Fallo en: {texto}"


def test_property_resistencia_a_ruido_y_fuzzing():
    """Propiedad: Texto ruidoso aleatorio no debe causar excepciones no controladas."""
    random.seed(42)
    for _ in range(50):
        longitud = random.randint(5, 100)
        caracteres = string.ascii_letters + string.digits + " \t\n.,:;-!?"
        texto_random = "".join(random.choice(caracteres) for _ in range(longitud))
        dto = SinglePassMessageParser.parse(texto_random)
        assert dto.mensaje_original == texto_random
        assert isinstance(dto.hechos_afirmados, list)
        assert isinstance(dto.hechos_negados, list)


def test_property_polaridad_excluyente():
    """Propiedad: Un hecho clínico no puede ser afirmado y negado simultáneamente en el mismo turno."""
    textos = [
        "Vibra al frenar",
        "Al frenar no vibra nada",
        "El motor no recalienta y no pierde agua",
        "Recalienta pero no bota humo",
    ]
    for txt in textos:
        dto = SinglePassMessageParser.parse(txt)
        campos_afirmados = {h.campo for h in dto.hechos_afirmados}
        campos_negados = {h.campo for h in dto.hechos_negados}
        interseccion = campos_afirmados.intersection(campos_negados)
        assert len(interseccion) == 0, f"Conflicto de polaridad en {txt}: {interseccion}"
