import ast
from pathlib import Path

DOMAIN_ROOT = Path(__file__).resolve().parents[1] / "src" / "domain"


def test_dominio_no_depende_de_interfaces_ni_infraestructura():
    infracciones: list[str] = []
    for archivo in DOMAIN_ROOT.rglob("*.py"):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=str(archivo))
        for nodo in ast.walk(arbol):
            modulos: list[str] = []
            if isinstance(nodo, ast.Import):
                modulos = [alias.name for alias in nodo.names]
            elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                modulos = [nodo.module]
            for modulo in modulos:
                if modulo.startswith(("src.infrastructure", "src.interfaces")):
                    infracciones.append(f"{archivo.name}: {modulo}")

    assert not infracciones, "El dominio depende de capas externas: " + ", ".join(infracciones)
