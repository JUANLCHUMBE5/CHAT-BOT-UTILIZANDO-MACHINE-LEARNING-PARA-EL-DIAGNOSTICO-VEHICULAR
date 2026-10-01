"""Pruebas focalizadas para el hotfix de acción prioritaria en WhatsApp.

Verifica:
1. TEST 1 - Caso actual: 'Cuerpo de aceleracion o valvula IAC sucia' con RAG_PROC_057.
   La acción prioritaria debe priorizar la directriz diagnóstica oficial de taller
   (inspección de carbonilla, IAC, TPS) y NUNCA 'desconectar el borne negativo'.
2. TEST 2 - Fallback RAG: Procedimiento donde el paso 1 es preparatorio/de seguridad
   ('Desconectar el borne negativo...') y el paso 2 es de comprobación ('Inspeccionar...').
   El paso preparatorio no debe ser presentado como 'Primero revisa'.
3. TEST 3 - Regresiones de seguridad y preservación de reglas de taller:
   - batería/bornes
   - alternador / carga
   - radiador / refrigeración
   - bujías / bobinas (con y sin prueba de chispa completada)
   - pastillas y discos de freno
4. TEST 4 - Integridad criptográfica de los artefactos congelados (C1, TF-IDF, MACRO, FAISS).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from src.core.conversacion.formateador_compacto import (
    FormateadorCompacto,
    _es_paso_preparatorio,
    _extraer_accion_prioritaria,
)


def test_caso_actual_cuerpo_aceleracion_prioriza_directriz_sobre_rag():
    """TEST 1: Verifica que para 'Cuerpo de aceleracion o valvula IAC sucia' con RAG_PROC_057

    se presente la directriz técnica de taller y NO la desconexión del borne.
    """
    contexto_rag_057 = (
        "Código de Falla Asociado: DTC P0505 (Válvula IAC) / DTC P2119 (Control Mariposa Acelerador)\n"
        "Modelos Compatibles Frecuentes en Perú: Toyota Yaris, Hyundai Accent/i10, Kia Rio/Picanto\n"
        "Instrucciones paso a paso:\n"
        "1. Desconectar el borne negativo (-) de la batería de 12V.\n"
        "2. Retirar el ducto de aire de admisión aflojando las abrazaderas.\n"
        "3. Desconectar el conector eléctrico del servo motor de la mariposa o de la válvula IAC.\n"
        "4. Desmontar los 4 pernos del cuerpo de aceleración del múltiple de admisión.\n"
        "5. Limpiar los depósitos de carbonilla alrededor de la mariposa y del ducto de aire con aerosol Carburaclean."
    )

    falla = "Cuerpo de aceleracion o valvula IAC sucia"
    accion = _extraer_accion_prioritaria(falla=falla, contexto_rag=contexto_rag_057)

    # NO debe ser la desconexión de batería
    assert "borne negativo" not in accion.lower()
    assert "desconectar" not in accion.lower()

    # Debe contener la directriz diagnóstica oficial de taller
    assert any(k in accion.lower() for k in ("carbonilla", "mariposa", "aceleración", "iac", "tps"))

    # Formateo completo de WhatsApp
    top_hipotesis = [
        {"falla": "Cuerpo de aceleracion o valvula IAC sucia", "probabilidad": 0.801},
        {"falla": "Falla en bujias o bobinas de encendido (misfire)", "probabilidad": 0.129},
        {"falla": "Falla en termostato o motoventilador de radiador", "probabilidad": 0.070},
    ]
    salida = FormateadorCompacto.formatear_respuesta_diagnostico(
        top_hipotesis=top_hipotesis,
        sintoma_original="cuando estoy parado en el semaforo el motor tiembla",
        contexto_rag=contexto_rag_057,
    )

    assert "🛠️ *Primero revisa:*" in salida
    assert "desconectar el borne negativo" not in salida.lower()
    assert "carbonilla" in salida.lower() or "mariposa" in salida.lower()


def test_fallback_rag_omite_paso_preparatorio():
    """TEST 2: Verifica que ante una falla sin directriz específica, si el manual RAG

    comienza con un paso preparatorio/seguridad ('desconectar borne'), el formateador
    lo omita y seleccione el siguiente paso diagnóstico.
    """
    contexto_controlado = (
        "Procedimiento de comprobación de actuador:\n"
        "1. Desconectar el borne negativo (-) de la batería de 12V por seguridad.\n"
        "2. Inspeccionar la resistencia y estado de los conectores eléctricos.\n"
        "3. Medir la señal de control con multímetro o punta lógica."
    )

    # Falla sintética que no tiene regla dura ni directriz taxonómica
    falla_desconocida = "Actuador auxiliar especial no catalogado"

    accion = _extraer_accion_prioritaria(falla=falla_desconocida, contexto_rag=contexto_controlado)

    # No debe seleccionar el paso 1 preparatorio
    assert "borne" not in accion.lower()
    assert "batería" not in accion.lower()
    assert "por seguridad" not in accion.lower()

    # Debe seleccionar el paso 2 diagnóstico
    assert "inspeccionar" in accion.lower()
    assert "conectores" in accion.lower()


def test_deteccion_pasos_preparatorios_variaciones():
    """Verifica que _es_paso_preparatorio reconozca distintas redacciones de seguridad."""
    assert _es_paso_preparatorio("Desconectar el borne negativo (-) de la batería de 12V.")
    assert _es_paso_preparatorio("Desconecte el cable negativo de la batería.")
    assert _es_paso_preparatorio("Desconectar la batería antes de intervenir el mazo.")
    assert _es_paso_preparatorio("Retirar la alimentación eléctrica por seguridad.")
    assert _es_paso_preparatorio("Elevar el vehículo en un elevador hidráulico.")
    assert _es_paso_preparatorio("Apagar el motor y esperar a que enfríe.")

    # Acciones diagnósticas reales NO deben ser detectadas como preparatorias
    assert not _es_paso_preparatorio("Inspeccionar visualmente sedimentos o carbonilla en la mariposa.")
    assert not _es_paso_preparatorio("Medir voltaje en reposo y caída durante el arranque.")
    assert not _es_paso_preparatorio("Verificar presión en el riel con manómetro automotriz.")
    assert not _es_paso_preparatorio("Escanear códigos de falla DTC en el módulo ECM.")


def test_regresion_acciones_existentes_y_protecciones():
    """TEST 3: Verifica que las reglas prioritarias y protecciones preexistentes se mantengan intactas."""

    # 1. Batería / bornes
    accion_bat = _extraer_accion_prioritaria("Bateria descargada o bornes sulfatados")
    assert "voltaje en reposo" in accion_bat
    assert "caída en arranque" in accion_bat or "caida en arranque" in accion_bat

    # 2. Alternador
    accion_alt = _extraer_accion_prioritaria("Alternador defectuoso o placa de diodos en cortocircuito")
    assert "voltaje de carga en ralentí" in accion_alt or "13.8" in accion_alt

    # 3. Termostato / ventilador / refrigeración
    accion_ref = _extraer_accion_prioritaria("Falla en termostato o motoventilador de radiador")
    assert "temperatura en ambas mangueras del radiador" in accion_ref
    assert "electroventilador" in accion_ref

    # 4. Bujías / bobinas sin prueba de chispa completada
    accion_buj = _extraer_accion_prioritaria("Falla en bujias o bobinas de encendido (misfire)")
    assert "salto de chispa" in accion_buj

    # 5. Bujías / bobinas CON prueba de chispa completada (protección contra bucle)
    from src.core.conversacion.models import ConversationState

    estado_chispa = ConversationState(session_id="test_chispa")
    estado_chispa.completed_tests = {"prueba_chispa": {"resultado": "chispa_correcta"}}

    accion_buj_comp = _extraer_accion_prioritaria(
        "Falla en bujias o bobinas de encendido (misfire)",
        estado=estado_chispa,
    )
    assert "salto de chispa" not in accion_buj_comp
    assert "calibración del electrodo" in accion_buj_comp or "estado físico" in accion_buj_comp

    # 6. Pastillas y frenos
    accion_past = _extraer_accion_prioritaria("Desgaste de pastillas y zapatas de freno")
    assert "espesor de las pastillas" in accion_past

    # 7. Discos de freno
    accion_disc = _extraer_accion_prioritaria("Discos de freno alabeados o desgastados")
    assert "alabeo" in accion_disc
    assert "reloj comparador" in accion_disc


@pytest.mark.requires_frozen_ml_artifacts
def test_integridad_hashes_componentes_congelados():
    """TEST 4: Verifica que los hashes de los artefactos congelados no hayan sufrido alteración."""
    root = Path(__file__).resolve().parent.parent.parent

    artefactos = {
        "C1": (
            root / "machine_learning" / "models" / "c1_fase10_final" / "modelo_diagnostico_c1.pkl",
            "24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c",
        ),
        "TF-IDF": (
            root / "machine_learning" / "models" / "c1_fase10_final" / "vectorizador_c1.pkl",
            "060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7",
        ),
        "MACRO": (
            root / "machine_learning" / "models" / "c1_fase10_final" / "modelo_sistema_c1_macrofix.pkl",
            "dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c",
        ),
        "FAISS": (
            root / "machine_learning" / "manuals" / "candidates" / "v1" / "indexes" / "indice_faiss_v1.index",
                "a2a081ffded23d4d727b57780aec26da9167e90f044101e77adbb33cbaa79b40",
        ),
    }

    for nombre, (ruta, hash_esperado) in artefactos.items():
        assert ruta.exists(), f"Artefacto {nombre} no encontrado en {ruta}"
        hash_calc = hashlib.sha256(ruta.read_bytes()).hexdigest()
        assert hash_calc == hash_esperado, (
            f"Hash alterado para {nombre}: esperado {hash_esperado}, calculado {hash_calc}"
        )
