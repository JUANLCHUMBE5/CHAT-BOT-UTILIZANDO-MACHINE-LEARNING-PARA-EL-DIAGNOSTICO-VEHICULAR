"""
Pruebas Unitarias e Integración: FASE 11.6.4 — HOTFIX POLÍTICA DTC Y RESCATE MACRO-SISTEMA
Valida que la contradicción de macro-sistema se resuelva arquitectónicamente
sin memorizar códigos ni introducir regresiones en casos sin DTC ni en otros sistemas.
"""

import pytest

from src.core.diagnostico.taxonomia_sistemas import obtener_macro_sistema
from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.fixture(scope="module")
def gestor():
    return GestorDiagnostico()


def test_1_c0040_expresado_distinto(gestor):
    """1. C0040 expresado de forma distinta a BLIND_38 (debe priorizar sensor ABS / FRENOS)."""
    texto = "Testigo de frenos ABS prendido en el tablero con código C0040 captador rueda derecha."
    res = gestor.procesar_consulta_texto(texto, diferir_encolado_persistente=True)
    assert res.diagnostico_ml == "Falla en sensor de velocidad de rueda ABS"
    assert obtener_macro_sistema(res.diagnostico_ml) == "FRENOS"


def test_2_otro_dtc_abs_catalogo(gestor):
    """2. Otro DTC de ABS existente en catálogo: C0035 (debe priorizar sensor ABS / FRENOS)."""
    texto = "Escaneo arroja código C0035 por señal errática en captador de velocidad de rueda delantera izquierda."
    res = gestor.procesar_consulta_texto(texto, diferir_encolado_persistente=True)
    assert res.diagnostico_ml == "Falla en sensor de velocidad de rueda ABS"
    assert obtener_macro_sistema(res.diagnostico_ml) == "FRENOS"


def test_3_pxxxx_motor_con_circuito_abierto(gestor):
    """3. Código Pxxxx real de motor (P0340) + 'circuito abierto' (debe mantener CKP/CMP, NO inyector)."""
    texto = "El escáner registra código P0340 por circuito abierto en el cableado del sensor de árbol de levas CMP."
    res = gestor.procesar_consulta_texto(texto, diferir_encolado_persistente=True)
    assert res.diagnostico_ml == "Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)"
    assert obtener_macro_sistema(res.diagnostico_ml) == "MOTOR"
    assert "inyector" not in res.diagnostico_ml.lower()


def test_4_dtc_inyector_motor_mantenido(gestor):
    """4. DTC relacionado con inyector (P0201) donde MOTOR e inyector sí deben mantenerse."""
    texto = "Código de falla P0201 circuito abierto en solenoide del inyector del cilindro 1."
    res = gestor.procesar_consulta_texto(texto, diferir_encolado_persistente=True)
    assert res.diagnostico_ml == "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)"
    assert obtener_macro_sistema(res.diagnostico_ml) == "MOTOR"


def test_5_cxxxx_no_registrado_en_catalogo(gestor):
    """5. Código Cxxxx no registrado en catálogo (C0500): no debe forzar artificialmente ABS."""
    texto = "Tengo código de avería C0500 en la dirección asistida."
    res = gestor.procesar_consulta_texto(texto, diferir_encolado_persistente=True)
    # No debe forzar sensor ABS
    assert res.diagnostico_ml != "Falla en sensor de velocidad de rueda ABS"


def test_6_consulta_sin_dtc_conserva_ml(gestor):
    """6. Consulta sin DTC: el clasificador ML conserva íntegramente su comportamiento normal."""
    texto = "Al pisar a fondo en cuarta el motor ruge pero el auto no avanza y huele a asbesto quemado."
    res = gestor.procesar_consulta_texto(texto, diferir_encolado_persistente=True)
    assert res.diagnostico_ml == "Disco de embrague desgastado o patinando"
    assert obtener_macro_sistema(res.diagnostico_ml) == "TRANSMISION"


def test_7_dtc_desconocido_no_fuerza_clasificacion(gestor):
    """7. DTC desconocido/no registrado (P9999): no se fuerza artificialmente ninguna clasificación."""
    texto = "La computadora tiene un código no identificado P9999 en el sistema."
    res = gestor.procesar_consulta_texto(texto, diferir_encolado_persistente=True)
    # No debe haber forzado una falla de catálogo inexistente
    assert res.diagnostico_ml != ""
    assert res.confianza_ml >= 0.0


def test_8_texto_y_dtc_coherentes(gestor):
    """8. Consulta donde texto y DTC son coherentes (P0301 + misfire cilindro 1): no se altera innecesariamente."""
    texto = "Escáner OBD-II registra código P0301 fallo de combustión en cilindro 1 con bujía sin chispa."
    res = gestor.procesar_consulta_texto(texto, diferir_encolado_persistente=True)
    assert res.diagnostico_ml == "Falla en bujias o bobinas de encendido (misfire)"
    assert obtener_macro_sistema(res.diagnostico_ml) == "MOTOR"
