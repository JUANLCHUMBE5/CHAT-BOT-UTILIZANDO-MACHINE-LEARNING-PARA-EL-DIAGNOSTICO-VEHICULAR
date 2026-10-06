"""Regresiones aisladas: filtrado eléctrico y discriminantes de suspensión."""

from src.core.diagnostico.enrutador_sistema import detectar_sistema_ruteo, filtrar_causas


def test_alternador_conserva_hipotesis_electricas_sin_cruzar_a_refrigeracion():
    evidencia = "el alternador no carga y la bateria se descarga rapido"
    assert detectar_sistema_ruteo(evidencia, usar_modelo=False) == "electrico_ecu"
    causas = ["Batería descargada o bornes sulfatados", "Falla de alternador", "Radiador picado"]
    assert filtrar_causas("electrico_ecu", causas, evidencia) == causas[:2]


def test_culata_requiere_evidencia_de_humo_blanco_y_refrigerante():
    causas = ["Junta de culata dañada", "Batería EV sobrecalentada", "Sensor O2"]
    assert filtrar_causas("refrigeracion", causas, "el motor recalienta") == []
    assert filtrar_causas(
        "refrigeracion", causas, "humo blanco por el escape y consume refrigerante",
    ) == causas[:1]
