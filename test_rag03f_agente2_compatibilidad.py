# -*- coding: utf-8 -*-
"""Suite de Pruebas y Validación Exhaustiva RAG-03F (Agente 2).

Objetivo:
- Adaptar los 17 fragmentos y el paquete experimental de 256 documentos al contrato
  documental aprobado por el Agente 1 (contrato_documental.py).
- Probar la normalización de metadatos (página int, paginas lista, fuente, fabricante,
  modelo, año, motor, mercado, componente).
- Comprobar la trazabilidad exacta de cifras, unidades y folios de origen.
- Ejecutar pruebas de documentación incompatible, datos OEM ausentes y fuentes multi-página.
- Validar la correspondencia matemática vector a vector <= 1e-6 en los 256 documentos.
- Generar el manifiesto reproducible con hashes SHA-256 y rutas relativas.
"""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import unicodedata

import faiss
import joblib
import numpy as np
import pytest

# Configurar rutas del worktree
WORKTREE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = WORKTREE_DIR

# Importar módulos del Agente 2
EXP_DIR = WORKTREE_DIR / "machine_learning/rag/experimentos/rag03c"
sys.path.insert(0, str(EXP_DIR))
from fragmentos_data import FRAGMENTOS_5PDFS

# Importar contrato documental del Agente 1 (read-only) de forma segura vía importlib
CONTRATO_PATH = PROJECT_ROOT / "backend/src/infrastructure/rag/contrato_documental.py"
spec = importlib.util.spec_from_file_location("contrato_documental", CONTRATO_PATH)
cdoc = importlib.util.module_from_spec(spec)
sys.modules["contrato_documental"] = cdoc
spec.loader.exec_module(cdoc)

DictamenDocumental = cdoc.DictamenDocumental
EstadoDocumental = cdoc.EstadoDocumental
TrazabilidadDocumental = cdoc.TrazabilidadDocumental
VehiculoConsulta = cdoc.VehiculoConsulta
dictaminar_candidato_documental = cdoc.dictaminar_candidato_documental
normalizar_texto = cdoc.normalizar_texto
parsear_rango_anios = cdoc.parsear_rango_anios
verificar_compatibilidad_estructurada = cdoc.verificar_compatibilidad_estructurada
verificar_presencia_cifra_y_trazabilidad = cdoc.verificar_presencia_cifra_y_trazabilidad

PDFS_AUTORIZADOS_DIR = WORKTREE_DIR / "machine_learning/rag/fuentes_documentales/pdfs_autorizados"
CORPUS_DIR = EXP_DIR / "corpus_experimental"
INDICES_DIR = EXP_DIR / "indices_temporales"

HASHES_OFICIALES_PDFS = {
    "brembo_guide_brake_disc_diagnostics.pdf": "ae78db3748db9d2c62a5a885d84056d880a2018a00d90074d637c5b060bab9a1",
    "hyundai_tsb_mdps_flexible_coupling_replacement.pdf": "3b051b41ae128a2a971f103d8908bc99f1be9720b1d4df5b2699ab8a3967d282",
    "kia_tsb_cmdps_steering_column_repair.pdf": "deded09b3e1ecfea115faf2f2c0171a087056c1873f2cd187b2928b3ffa8d0b9",
    "laser_5524_instrucciones_es.pdf": "513d6c527cc661e92503c7c35fb3c85c981e4af6726ec3bfb56a99e66840b63d",
    "pico_wps500x_pressure_transducer_manual.pdf": "3de1537817f51acb803cc77a79ed85a2bb044d2438a6dd4cd12fcb28227af678",
}


def calcular_sha256(ruta_archivo: Path) -> str:
    sha = hashlib.sha256()
    with open(ruta_archivo, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


# ==============================================================================
# FASE 1: INTEGRIDAD DE FUENTES Y HASHES CRIPTOGRÁFICOS DE LOS 5 PDFS
# ==============================================================================

def test_fase1_integridad_hashes_5_pdfs():
    """Comprueba que los 5 PDFs originales estén físicamente presentes y coincidan al 100% con sus SHA-256."""
    for nombre_pdf, hash_esperado in HASHES_OFICIALES_PDFS.items():
        ruta = PDFS_AUTORIZADOS_DIR / nombre_pdf
        assert ruta.exists(), f"PDF no encontrado: {ruta}"
        hash_calculado = calcular_sha256(ruta)
        assert hash_calculado == hash_esperado, f"Hash incorrecto en {nombre_pdf}: {hash_calculado} vs {hash_esperado}"


# ==============================================================================
# FASE 2: NORMALIZACIÓN METADATOS Y TRAZABILIDAD EXACTA DE 17 FRAGMENTOS
# ==============================================================================

def test_fase2_normalizacion_metadatos_17_fragmentos():
    """Valida la normalización de página como entero positivo y metadatos vehiculares en los 17 fragmentos."""
    assert len(FRAGMENTOS_5PDFS) == 17, f"Se esperaban 17 fragmentos, hay {len(FRAGMENTOS_5PDFS)}"

    for f in FRAGMENTOS_5PDFS:
        doc_id = f["doc_id"]
        # 1. Página debe ser un entero positivo
        assert isinstance(f["pagina"], int), f"El campo pagina en {doc_id} debe ser int, no {type(f['pagina'])}"
        assert f["pagina"] > 0, f"El número de página en {doc_id} debe ser > 0, obtenido {f['pagina']}"

        # 2. Lista de páginas y rango
        assert isinstance(f["paginas"], list), f"El campo paginas en {doc_id} debe ser una lista"
        assert len(f["paginas"]) >= 1, f"El fragmento {doc_id} debe tener al menos una página en paginas"
        for p in f["paginas"]:
            assert isinstance(p, int) and p > 0, f"Página inválida en {doc_id}: {p}"
        assert f["pagina"] in f["paginas"], f"La página principal {f['pagina']} debe pertenecer a paginas {f['paginas']}"
        assert isinstance(f["rango_paginas"], str) and len(f["rango_paginas"]) > 0

        # 3. Metadatos de procedencia y trazabilidad vehicular
        assert f["fabricante"] and len(f["fabricante"]) > 2
        assert f["vehiculo"] and len(f["vehiculo"]) > 2
        assert f["sistema"] in ("FRENOS", "DIRECCIÓN", "INSTRUMENTAL", "MOTOR", "REFRIGERACIÓN")
        assert f["subsistema"] and len(f["subsistema"]) > 2
        assert f["componente"] and len(f["componente"]) > 2
        assert f["pdf_origen"] in HASHES_OFICIALES_PDFS
        assert f["sha256_pdf"] == HASHES_OFICIALES_PDFS[f["pdf_origen"]]

        # 4. Matriz de cifras trazadas
        assert isinstance(f["cifras_trazadas"], list)
        assert len(f["cifras_trazadas"]) >= 1, f"El fragmento {doc_id} carece de matriz cifras_trazadas"
        for ct in f["cifras_trazadas"]:
            assert "parametro" in ct and ct["parametro"]
            assert "cifra" in ct and ct["cifra"]
            assert "unidad" in ct and ct["unidad"]
            assert "pagina" in ct and isinstance(ct["pagina"], int) and ct["pagina"] > 0
            assert "condicion" in ct and ct["condicion"]


def test_fase2_verificacion_remediacion_c01_y_a08():
    """Comprueba las correcciones específicas de C01 (Laser) y A08 (cero invención de cotas)."""
    # C01: Laser Tools 5524
    laser_001 = next(f for f in FRAGMENTOS_5PDFS if f["doc_id"] == "RAG_EXP_LASER_001")
    texto_laser_norm = normalizar_texto(f"{laser_001['procedimiento']} {laser_001['advertencias_seguridad']}")
    assert "abrir con extrema precaucion la tapa de radiador en caliente" not in texto_laser_norm
    assert "retire el tapon del deposito o radiador unicamente con el motor frio" in texto_laser_norm or "vehiculo debe estar frio" in texto_laser_norm
    assert "terminantemente prohibido" in texto_laser_norm

    # A08: Brembo sin cotas inventadas de 0.015 mm ni 100-120 N.m
    brembo_002 = next(f for f in FRAGMENTOS_5PDFS if f["doc_id"] == "RAG_EXP_BREMBO_002")
    assert "0.015" not in brembo_002["tolerancias_unidades"]
    assert "8 puntos" not in brembo_002["tolerancias_unidades"]
    assert brembo_002["cifras_trazadas"][0]["cifra"] == "0.05"
    assert brembo_002["cifras_trazadas"][0]["unidad"] == "mm"

    brembo_003 = next(f for f in FRAGMENTOS_5PDFS if f["doc_id"] == "RAG_EXP_BREMBO_003")
    assert "100-120" not in brembo_003["tolerancias_unidades"]
    assert brembo_003["requiere_confirmacion_oem"] is True

    # A08: Hyundai delimitado estrictamente a Elantra y Sonata
    hyundai_001 = next(f for f in FRAGMENTOS_5PDFS if f["doc_id"] == "RAG_EXP_HYUNDAI_001")
    assert "Accent" not in hyundai_001["modelos_aplicables"]
    assert "Kia" not in hyundai_001["marcas_aplicables"]
    assert "Elantra" in str(hyundai_001["modelos_aplicables"])
    assert "Sonata" in str(hyundai_001["modelos_aplicables"])

    # A08: Kia sin voltajes ni impedancias óhmicas ficticias
    kia_003 = next(f for f in FRAGMENTOS_5PDFS if f["doc_id"] == "RAG_EXP_KIA_003")
    assert "2.5v" not in kia_003["tolerancias_unidades"].lower()
    assert "5.0v" not in kia_003["tolerancias_unidades"].lower()
    assert "ohmios" not in kia_003["tolerancias_unidades"].lower()

    # A08: Pico sin presiones apócrifas de 4-6 bar
    pico_002 = next(f for f in FRAGMENTOS_5PDFS if f["doc_id"] == "RAG_EXP_PICO_002")
    assert "4-6 bar" not in pico_002["tolerancias_unidades"]
    assert "4 a 6 bar" not in pico_002["tolerancias_unidades"]


# ==============================================================================
# FASE 3: COMPATIBILIDAD CON EL CONTRATO DOCUMENTAL DEL AGENTE 1
# ==============================================================================

def test_fase3_compatibilidad_contrato_agente1_todos_los_fragmentos():
    """Evalúa que los 17 fragmentos pasen la verificación de trazabilidad sin rechazos por parseo de páginas."""
    corpus_b_path = CORPUS_DIR / "corpus_B_experimental.json"
    assert corpus_b_path.exists(), f"Corpus B no encontrado en {corpus_b_path}"
    corpus_b = json.loads(corpus_b_path.read_text(encoding="utf-8"))

    fragmentos_b_candidatos = [doc for doc in corpus_b if doc.get("es_experimental") is True]
    assert len(fragmentos_b_candidatos) == 17

    rechazos_por_pagina = []
    con_cifras_aprobadas = []
    procedimientos_cualitativos = []

    for cand in fragmentos_b_candidatos:
        doc_id = cand["doc_id"]
        # Ejecutar función del Agente 1
        tiene_cifra, trazabilidad, motivo = verificar_presencia_cifra_y_trazabilidad(cand["titulo"], cand)

        if "sin número de página" in motivo.lower() or "sin numero de pagina" in motivo.lower():
            rechazos_por_pagina.append((doc_id, motivo))

        if tiene_cifra:
            con_cifras_aprobadas.append(doc_id)
            assert trazabilidad is not None
            assert int(trazabilidad.pagina) > 0
            assert all(isinstance(p, int) and p > 0 for p in trazabilidad.paginas)
            assert trazabilidad.fuente in HASHES_OFICIALES_PDFS
            assert trazabilidad.cifra_encontrada is not None
            assert trazabilidad.unidad is not None
        else:
            procedimientos_cualitativos.append(doc_id)

    # REGLA FUNDAMENTAL DE RAG-03F: 0 rechazos por parseo de páginas (B-INT-02 superado al 100%)
    assert len(rechazos_por_pagina) == 0, f"Hubo fragmentos rechazados por formato de página: {rechazos_por_pagina}"

    # Comprobar que los fragmentos cuantitativos (Brembo 001/002, Hyundai 003, Pico 001/002/003) se reconocen
    esperados_cuantitativos = {
        "RAG_EXP_BREMBO_001", "RAG_EXP_BREMBO_002",
        "RAG_EXP_HYUNDAI_003", "RAG_EXP_PICO_001", "RAG_EXP_PICO_002", "RAG_EXP_PICO_003"
    }
    for doc_id in esperados_cuantitativos:
        assert doc_id in con_cifras_aprobadas, f"Fragmento cuantitativo {doc_id} no fue reconocido con cifra"


def test_fase3_dictaminar_candidatos_con_corpus_no_validado():
    """Comprueba que con corpus_validado=False ninguna cifra sea autorizada a publicación (C02/A02)."""
    corpus_b = json.loads((CORPUS_DIR / "corpus_B_experimental.json").read_text(encoding="utf-8"))
    candidatos_exp = [doc for doc in corpus_b if doc.get("es_experimental") is True]

    for cand in candidatos_exp:
        dictamen = dictaminar_candidato_documental(
            consulta="Consulta de diagnóstico general de taller",
            candidato=cand,
            corpus_validado=False,
        )
        assert dictamen.autorizado_publicar_cifra is False, f"Cifra autorizada indebidamente para {cand['doc_id']}"
        # Si tiene cifra metrológica en este título/texto, debe quedar retenida por C02
        tiene_cifra, _, _ = verificar_presencia_cifra_y_trazabilidad("Consulta general", cand)
        if tiene_cifra:
            assert "corpus_validado=False" in dictamen.motivo or "retenida" in dictamen.motivo


# ==============================================================================
# FASE 4: DOCUMENTACIÓN INCOMPATIBLE, DATOS AUSENTES Y MULTI-PÁGINA
# ==============================================================================

def test_fase4_casos_documentacion_incompatible():
    """Comprueba el bloqueo de consultas incompatibles y de marcas opuestas (A03)."""
    corpus_b = json.loads((CORPUS_DIR / "corpus_B_experimental.json").read_text(encoding="utf-8"))
    cand_hyundai = next(doc for doc in corpus_b if doc["doc_id"] == "RAG_EXP_HYUNDAI_003")

    # 1. Incompatibilidad de Marca Opuesta: Toyota Raize, Suzuki S-Presso, Fiat Mobi frente a Hyundai OEM
    consultas_incompatibles_marca = [
        "Torque de apriete pernos columna direccion Toyota Raize 2024",
        "Calibracion columna direccion Suzuki S-Presso 2023",
        "Par de pernos columna direccion Fiat Mobi 2025",
    ]
    for q in consultas_incompatibles_marca:
        dictamen = dictaminar_candidato_documental(q, cand_hyundai, corpus_validado=True)
        assert dictamen.estado == EstadoDocumental.INFORMACION_PARCIAL
        assert dictamen.autorizado_publicar_cifra is False
        assert dictamen.factor_relevancia <= 0.05
        assert "incompatib" in dictamen.motivo.lower() or "marca" in dictamen.motivo.lower()

    # 2. Incompatibilidad de Modelo: Hyundai Tucson vs Elantra/Sonata
    dictamen_tucson = dictaminar_candidato_documental(
        consulta="Torque de tornillos de columna de direccion Hyundai Tucson 2022",
        candidato=cand_hyundai,
        corpus_validado=True,
    )
    assert dictamen_tucson.estado == EstadoDocumental.INFORMACION_PARCIAL
    assert dictamen_tucson.autorizado_publicar_cifra is False
    assert "tucson" in dictamen_tucson.motivo.lower()

    # 3. Incompatibilidad de Año: Hyundai Accent/Elantra 1997 vs Rango TSB (2007-2015)
    dictamen_anio = dictaminar_candidato_documental(
        consulta="Torque de columna de direccion Hyundai Elantra 1997",
        candidato=cand_hyundai,
        corpus_validado=True,
    )
    assert dictamen_anio.estado == EstadoDocumental.INFORMACION_PARCIAL
    assert dictamen_anio.autorizado_publicar_cifra is False
    assert "1997" in dictamen_anio.motivo


def test_fase4_datos_oem_ausentes_no_inventan_cifras():
    """Comprueba que consultas sobre parámetros ausentes en el corpus no reciban cifras inventadas."""
    corpus_b = json.loads((CORPUS_DIR / "corpus_B_experimental.json").read_text(encoding="utf-8"))
    cand_hyundai_dtc = next(doc for doc in corpus_b if doc["doc_id"] == "RAG_EXP_HYUNDAI_004")

    # Consulta sobre torque de culata a un fragmento que solo trata calibración ASP
    dictamen = dictaminar_candidato_documental(
        consulta="Cual es el torque de apriete de pernos de culata de Hyundai Elantra?",
        candidato=cand_hyundai_dtc,
        corpus_validado=True,
    )
    assert dictamen.estado != EstadoDocumental.ESPECIFICACION_DOCUMENTADA
    assert dictamen.autorizado_publicar_cifra is False


def test_fase4_fuentes_con_varias_paginas():
    """Comprueba que documentos con respaldo en múltiples páginas conserven todas sus referencias de folio."""
    corpus_b = json.loads((CORPUS_DIR / "corpus_B_experimental.json").read_text(encoding="utf-8"))
    cand_hyundai_003 = next(doc for doc in corpus_b if doc["doc_id"] == "RAG_EXP_HYUNDAI_003")

    # Tiene 4 páginas de respaldo en el TSB
    assert cand_hyundai_003["pagina"] == 3
    assert cand_hyundai_003["paginas"] == [3, 4, 5, 14]
    assert cand_hyundai_003["rango_paginas"] == "3, 4, 5, 14"
    assert len(cand_hyundai_003["cifras_trazadas"]) == 6

    # Cada cota tiene su página exacta
    paginas_cifras = {ct["pagina"] for ct in cand_hyundai_003["cifras_trazadas"]}
    assert paginas_cifras == {3, 4, 5, 14}


# ==============================================================================
# FASE 5: COHERENCIA MATEMÁTICA Y CORRESPONDENCIA VECTOR A VECTOR (<= 1e-6)
# ==============================================================================

def test_fase5_coherencia_vectorial_faiss_vs_tfidf():
    """Comprueba que los 256 vectores de Corpus B tengan error absoluto <= 1e-6 entre TF-IDF y FAISS."""
    corpus_b = json.loads((CORPUS_DIR / "corpus_B_experimental.json").read_text(encoding="utf-8"))
    assert len(corpus_b) == 256

    vec_path = INDICES_DIR / "vectorizador_test_B.joblib"
    idx_path = INDICES_DIR / "indice_faiss_test_B.index"
    assert vec_path.exists() and idx_path.exists()

    vec = joblib.load(vec_path)
    index = faiss.read_index(str(idx_path))

    assert index.ntotal == 256
    assert index.d == len(vec.vocabulary_)

    # Recalcular matriz TF-IDF
    textos = [f"{doc['titulo']}\n{doc['texto']}" for doc in corpus_b]
    matriz_tfidf = vec.transform(textos).toarray().astype(np.float32)
    faiss.normalize_L2(matriz_tfidf)

    max_err = 0.0
    for i in range(index.ntotal):
        vec_faiss = index.reconstruct(i)
        vec_tfidf = matriz_tfidf[i]
        diff = float(np.max(np.abs(vec_faiss - vec_tfidf)))
        if diff > max_err:
            max_err = diff

    print(f"\n[FASE 5] Error absoluto máximo observado: {max_err:.2e}")
    assert max_err <= 1.0e-6, f"Error vectorial {max_err} excede tolerancia de 1e-6"


# ==============================================================================
# FASE 6: PRESERVACIÓN DE ARTEFACTOS CANÓNICOS CONGELADOS DE PRODUCCIÓN (v1)
# ==============================================================================

def test_fase6_preservacion_modelos_canonicos_v1():
    """Comprueba que los modelos canónicos congelados v1 permanezcan estrictamente intactos."""
    manifest_audit_path = PROJECT_ROOT / "docs/auditorias/rag03_preintegracion_20261018/integrity_manifest.json"
    if not manifest_audit_path.exists():
        pytest.skip("Manifiesto canónico no disponible para verificación cruzada.")

    manifest = json.loads(manifest_audit_path.read_text(encoding="utf-8"))
    for rel_path, data in manifest.get("frozen_v1_artifacts", {}).items():
        full_path = WORKTREE_DIR / rel_path
        assert full_path.exists(), f"Artefacto congelado faltante: {rel_path}"
        # Normalizar CRLF para archivos textuales
        is_text = data.get("is_text", False)
        if is_text:
            content = full_path.read_bytes().replace(b"\r\n", b"\n")
            calc_hash = hashlib.sha256(content).hexdigest()
        else:
            calc_hash = calcular_sha256(full_path)
        assert calc_hash == data["sha256"], f"Artefacto congelado alterado: {rel_path}"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
