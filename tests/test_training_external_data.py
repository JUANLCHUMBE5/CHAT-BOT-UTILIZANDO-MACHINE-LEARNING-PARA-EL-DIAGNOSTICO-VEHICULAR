import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ML = ROOT / "machine_learning"
EXTERNAL = ML / "data" / "dataset_externo_auditado.csv"
BASE = ML / "data" / "dataset_sintomas_limpio.csv"
METRICS = ML / "models" / "metricas_modelo.json"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def test_external_dataset_has_traceable_and_unique_cases():
    rows = _rows(EXTERNAL)

    assert len(rows) == 33
    assert len({(row["sintoma"], row["codigo_falla"]) for row in rows}) == len(rows)
    assert all(row["doi"] == "10.5281/zenodo.15626055" for row in rows)
    assert all(row["licencia"] == "CC BY 4.0" for row in rows)
    assert all(
        row["estado_validacion"] == "AUDITADO_TAXONOMIA_NO_CASO_TALLER"
        for row in rows
    )
    assert all(row["sintoma"] and row["falla"] and row["codigo_falla"] for row in rows)


def test_external_labels_are_consistent_with_base_taxonomy():
    base_rows = _rows(BASE)
    external_rows = _rows(EXTERNAL)
    failures_by_code: dict[str, set[str]] = {}
    for row in base_rows:
        failures_by_code.setdefault(row["codigo_falla"], set()).add(row["falla"])

    for row in external_rows:
        assert failures_by_code[row["codigo_falla"]] == {row["falla"]}


def test_metrics_prove_external_data_never_entered_holdout():
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    comparison = metrics["comparacion_enriquecimiento_externo"]

    assert metrics["registros_externos_disponibles"] == 33
    assert comparison["peor_variacion_f1_clase"] >= -0.10
    if metrics["dataset_externo_seleccionado"]:
        assert metrics["registros_externos_incorporados"] == 33
        assert comparison["enriquecido"]["f1_macro"] > comparison["base"]["f1_macro"]
    else:
        assert metrics["registros_externos_incorporados"] == 0
        assert comparison["enriquecido"]["f1_macro"] <= comparison["base"]["f1_macro"]
