"""Pruebas unitarias para el catálogo de directrices técnicas de taller y el dataset complementario."""

from __future__ import annotations

import csv
from pathlib import Path

from src.core.taxonomy.catalogo_fallas import CATALOGO_TAXONOMIA
from src.core.taxonomy.catalogo_pruebas_taller import (
    es_falla_mecanica_pura,
    listar_todas_las_directrices,
    obtener_directriz_taller,
    obtener_prueba_taller,
)

ROOT = Path(__file__).resolve().parents[2]
DATASET_TALLER_PATH = ROOT / "machine_learning" / "data" / "dataset_sintomas_aumento_taller.csv"


def test_catalogo_cubre_todas_las_48_clases_canonica():
    """Verifica que cada una de las 48 fallas canónicas de la taxonomía tenga directriz técnica."""
    directrices = listar_todas_las_directrices()
    assert len(directrices) == 48

    for codigo, falla_estandar in CATALOGO_TAXONOMIA.items():
        directriz = obtener_directriz_taller(codigo)
        assert directriz is not None, f"Falta directriz de taller para el código: {codigo}"
        assert directriz.codigo == codigo
        assert directriz.falla == falla_estandar.falla_principal
        assert len(directriz.prueba_sugerida) > 20
        assert isinstance(directriz.requiere_escaner, bool)


def test_averias_mecanicas_puras_no_requieren_escaner():
    """Comprueba que las averías mecánicas no dependan de escáner electrónico y sugieran prueba física."""
    fallas_mecanicas_clave = [
        "Llantas desbalanceadas o desalineadas",
        "Discos de freno alabeados o desgastados",
        "Desgaste de pastillas y zapatas de freno",
        "Disco de embrague desgastado o patinando",
        "Amortiguadores reventados o bujes de suspension gastados",
        "Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado",
        "Consumo de aceite por desgaste de anillos o retenes",
        "Empaque de culata soplado o danado",
        "Baja presion de aceite o bomba de aceite defectuosa",
    ]

    for nombre_falla in fallas_mecanicas_clave:
        assert es_falla_mecanica_pura(nombre_falla) is True, f"Debe ser mecánica pura: {nombre_falla}"
        directriz = obtener_directriz_taller(nombre_falla)
        assert directriz is not None
        assert directriz.requiere_escaner is False
        assert "escaner" not in directriz.prueba_sugerida.lower()
        assert "escáner" not in directriz.prueba_sugerida.lower()


def test_averias_electronicas_requieren_escaner_y_dtc():
    """Comprueba que las averías de sensores o actuadores requieran escáner y tengan DTC asociado."""
    fallas_electronicas_clave = [
        "Falla en bujias o bobinas de encendido (misfire)",
        "Falla en sensor de velocidad de rueda ABS",
        "Falla en sensor de oxigeno o mezcla rica",
        "Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
        "Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)",
    ]

    for nombre_falla in fallas_electronicas_clave:
        directriz = obtener_directriz_taller(nombre_falla)
        assert directriz is not None, f"Debe existir directriz para {nombre_falla}"
        assert directriz.requiere_escaner is True
        assert directriz.es_mecanica_pura is False
        assert directriz.dtc_frecuente != "N/A"


def test_obtener_prueba_taller_soporta_codigos_y_nombres():
    """Verifica que la función de consulta resuelva tanto por código como por nombre."""
    prueba_codigo = obtener_prueba_taller("SUSPENSION_004")
    assert prueba_codigo is not None
    assert "balanceo" in prueba_codigo.lower()

    prueba_nombre = obtener_prueba_taller("Llantas desbalanceadas o desalineadas")
    assert prueba_nombre == prueba_codigo


def test_dataset_aumento_taller_integridad_y_consistencia():
    """Comprueba la estructura, unicidad y consistencia del archivo CSV de aumento de taller."""
    assert DATASET_TALLER_PATH.exists(), "El dataset de taller debe existir"

    with open(DATASET_TALLER_PATH, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        filas = list(reader)

    assert len(filas) >= 3000, f"Debe contener al menos 3,000 registros, encontrados: {len(filas)}"

    columnas_esperadas = {
        "id",
        "sintoma",
        "falla",
        "codigo_falla",
        "sistema",
        "subcomponente",
        "requiere_escaner",
        "prueba_sugerida",
        "codigo_dtc",
    }
    assert columnas_esperadas.issubset(set(filas[0].keys()))

    codigos_validos = set(CATALOGO_TAXONOMIA.keys())
    fallas_validas = {item.falla_principal for item in CATALOGO_TAXONOMIA.values()}

    for fila in filas:
        assert fila["codigo_falla"] in codigos_validos, f"Código inválido: {fila['codigo_falla']}"
        assert fila["falla"] in fallas_validas, f"Falla inválida: {fila['falla']}"
        assert fila["requiere_escaner"] in ("SI", "NO")
        assert len(fila["sintoma"].strip()) > 10
        assert len(fila["prueba_sugerida"].strip()) > 15
