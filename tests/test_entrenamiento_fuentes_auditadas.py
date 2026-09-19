from __future__ import annotations

import pandas as pd
import pytest
from training.entrenar_fuentes_auditadas import (
    ajustar,
    bloqueos_produccion,
    cumple_mejora,
    entrenar,
    normalizar_grupo,
    particiones,
    sin_solapamientos,
    validar_datos,
)


def datos_fuente():
    base = pd.DataFrame([{"sintoma": "ruido motor", "falla": "motor", "codigo_falla": "M1"}])
    externo = base.assign(
        origen="ZENODO_ACADEMICO", doi="10.5281/zenodo.15626055", licencia="CC BY 4.0",
        estado_validacion="AUDITADO_TAXONOMIA_NO_CASO_TALLER",
    )
    return base, externo


def test_admite_solo_fuente_con_licencia_y_taxonomia_conocidas():
    base, externo = datos_fuente()
    validar_datos(base, externo)
    externo.loc[0, "licencia"] = "Unknown"
    with pytest.raises(ValueError, match="Fuente externa no admitida"):
        validar_datos(base, externo)


def test_rechaza_etiqueta_inventada_y_sintoma_vacio():
    base, externo = datos_fuente()
    with pytest.raises(ValueError, match="taxonomia"):
        validar_datos(base, externo.assign(falla="otra falla"))
    with pytest.raises(ValueError, match="vacio"):
        validar_datos(base, externo.assign(sintoma=" "))


def test_excluye_familias_reservadas_duplicados_y_etiquetas_en_conflicto():
    reservado = pd.DataFrame({"sintoma": ["ruido metálico"]})
    externo = pd.DataFrame({
        "sintoma": ["Ruido metalico!", "freno duro", "freno duro", "motor lento", "motor lento"],
        "falla": ["A", "B", "B", "C", "D"],
    })
    resultado = sin_solapamientos(externo, reservado)
    assert resultado.to_dict("records") == [{"sintoma": "freno duro", "falla": "B"}]


def test_calibracion_agrupa_familias_y_aprende_vocabulario_solo_en_ajuste():
    datos = pd.DataFrame([
        {"sintoma": f"{prefijo} {sistema} averia variante {numero}", "falla": sistema}
        for sistema in ("freno", "motor")
        for numero in range(9)
        for prefijo in ("", "maestro una consulta")
    ])
    for ajuste, validacion in particiones(datos, 3, 44):
        assert not (
            set(datos.iloc[ajuste].sintoma.map(normalizar_grupo))
            & set(datos.iloc[validacion].sintoma.map(normalizar_grupo))
        )
    modelo = ajustar(datos, caracteres=True)
    assert modelo.predict_proba(["freno averia"]).shape == (1, 2)
    for calibrado in modelo.calibrated_classifiers_:
        assert "texto" in calibrado.estimator.named_steps


def test_no_acepta_mejora_global_que_empeora_una_clase():
    base = {"f1_macro": 0.8, "exactitud": 0.8, "ece": 0.05,
            "por_clase": {"freno": {"f1-score": 0.9}}}
    candidato = {"f1_macro": 0.85, "exactitud": 0.85, "ece": 0.05,
                 "por_clase": {"freno": {"f1-score": 0.7}}}
    assert not cumple_mejora(base, candidato)
    candidato["por_clase"]["freno"]["f1-score"] = 0.9
    assert cumple_mejora(base, candidato)


def test_no_permite_escribir_fuera_de_experimentos(tmp_path):
    with pytest.raises(ValueError, match="subcarpeta nueva"):
        entrenar(tmp_path / "models")


def test_bloquea_calibracion_deficiente_y_falta_de_confirmacion_real():
    bloqueos = bloqueos_produccion({
        "ece": 0.12, "por_clase": {"freno": {"support": 3, "f1-score": 0.5}},
    })
    assert any("ECE" in razon for razon in bloqueos)
    assert any("menos de 5" in razon for razon in bloqueos)
    assert any("F1" in razon for razon in bloqueos)
    assert any("mecanicos" in razon for razon in bloqueos)
