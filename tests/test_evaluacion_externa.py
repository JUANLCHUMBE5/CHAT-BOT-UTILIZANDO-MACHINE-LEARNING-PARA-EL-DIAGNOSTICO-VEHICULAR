"""Pruebas de las barreras de proveniencia para evaluacion externa."""

import pandas as pd
from training.evaluar_modelo_externo import validar_proveniencia


def _casos_base() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "tipo_vehiculo": "sedan 2020",
                "metodo_confirmacion": "inspeccion y prueba electrica",
                "mecanico_validador": "MEC-01",
                "fecha": "2026-08-01",
                "codigo_falla": "CARROCERIA_001",
                "id_evidencia": "EV-001",
                "archivo_evidencia": "EV-001.pdf",
                "estado_validacion": "validado",
            },
            {
                "tipo_vehiculo": "hatchback 2019",
                "metodo_confirmacion": "desmontaje y comprobacion",
                "mecanico_validador": "MEC-02",
                "fecha": "2026-08-02",
                "codigo_falla": "CARROCERIA_002",
                "id_evidencia": "EV-002",
                "archivo_evidencia": "EV-002.pdf",
                "estado_validacion": "aprobado",
            },
        ]
    )


def test_columnas_sin_archivos_no_son_evidencia(tmp_path):
    valido, problemas = validar_proveniencia(_casos_base(), tmp_path)
    assert not valido
    assert any("respaldos no encontrados" in problema for problema in problemas)


def test_evidencias_reales_y_dos_validadores_superan_barrera(tmp_path):
    (tmp_path / "EV-001.pdf").write_bytes(b"evidencia de prueba 1")
    (tmp_path / "EV-002.pdf").write_bytes(b"evidencia de prueba 2")

    valido, problemas = validar_proveniencia(_casos_base(), tmp_path)

    assert valido
    assert problemas == []
