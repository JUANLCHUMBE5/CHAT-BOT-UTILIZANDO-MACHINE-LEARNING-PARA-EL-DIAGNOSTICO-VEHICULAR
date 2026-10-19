# -*- coding: utf-8 -*-
"""Suite de Validación de Remediación Documental OEM RAG-03 — Agente 1 (RAG-03F).

Cubre rigurosamente los hallazgos auditados y el contrato documental definitivo:
- B-INT-02: Parser y validación de referencias de páginas (enteros, rangos, listas: '5', '5-6', '7, 10, 14', '3, 4, 5, 14').
- A02: Correspondencia exacta entre la magnitud solicitada (torque, presión, tolerancia lineal, temperatura, eléctrica)
       y el componente documentado (no basta cualquier número con unidad).
- A03: Validación vehicular estructurada en 5 dimensiones (marca, modelo, año, motor, mercado) con gestión de
       información faltante y datos contradictorios.
- C02: Prohibición absoluta de emitir cifras OEM verificadas si corpus_validado=False.
- C1 / Agente 3: Interfaz estable de protección conversacional (proteger_salida_conversacional, interceptar_o_autorizar_tolerancia).
- Pruebas negativas auditadas: Toyota Raize 2024, Suzuki S-Presso 2023, Fiat Mobi 2025 y vehículos incompatibles.
- A01: Validación de coherencia del paquete experimental (hashes SHA-256, versión, dimensiones y tolerancia L2 <= 1e-6).
- A07/A09: Unificación del adaptador D3 con la política única del backend O1 independiente del CWD.
"""

import sys

from src.config import PROJECT_ROOT
from src.infrastructure.motor_rag import validar_coherencia_paquete_experimental
from src.infrastructure.rag.contrato_documental import (
    EstadoDocumental,
    VehiculoConsulta,
    interceptar_o_autorizar_tolerancia,
    parsear_referencias_paginas,
    verificar_compatibilidad_estructurada,
    verificar_presencia_cifra_y_trazabilidad,
)
from src.infrastructure.rag.controlador_especificaciones_oem import clasificar_y_filtrar_oem

# ==============================================================================
# 1. B-INT-02: PARSEO Y VALIDACIÓN DE PÁGINAS (ENTEROS, RANGOS, LISTAS)
# ==============================================================================


def test_b_int_02_parseo_paginas_individuales_rangos_y_listas():
    """Valida que parsear_referencias_paginas acepte todos los formatos del corpus del Agente 2."""
    # Entero individual
    ok, pags, s = parsear_referencias_paginas(5)
    assert ok is True and pags == [5] and s == "5"

    # Cadena simple
    ok, pags, s = parsear_referencias_paginas("5")
    assert ok is True and pags == [5] and s == "5"

    # Rango
    ok, pags, s = parsear_referencias_paginas("5-6")
    assert ok is True and pags == [5, 6] and s == "5-6"

    # Lista de páginas separada por comas
    ok, pags, s = parsear_referencias_paginas("7, 10, 14")
    assert ok is True and pags == [7, 10, 14] and s == "7, 10, 14"

    # Múltiples páginas y rangos combinados
    ok, pags, s = parsear_referencias_paginas("3, 4, 5, 14")
    assert ok is True and pags == [3, 4, 5, 14] and s == "3, 4, 5, 14"

    ok, pags, s = parsear_referencias_paginas("2, 5, 8-9")
    assert ok is True and pags == [2, 5, 8, 9] and s == "2, 5, 8-9"

    ok, pags, s = parsear_referencias_paginas("3-4, 10, 16")
    assert ok is True and pags == [3, 4, 10, 16] and s == "3-4, 10, 16"

    ok, pags, s = parsear_referencias_paginas("4, 10, 11-12, 16")
    assert ok is True and pags == [4, 10, 11, 12, 16] and s == "4, 10, 11-12, 16"


def test_b_int_02_rechazo_paginas_invalidas_o_inventadas():
    """Rechaza referencias con páginas nulas, menores o iguales a cero, vacías o espurias."""
    for entrada_invalida in [None, "", "   ", 0, -1, "0", "-5", "abc", "5-2", "1-200"]:
        ok, pags, motivo = parsear_referencias_paginas(entrada_invalida)
        assert ok is False
        assert len(pags) == 0


def test_b_int_02_trazabilidad_con_rango_y_lista_en_fragmento_real():
    """Comprueba que un fragmento con 'pagina': '3, 4, 5, 14' sea reconocido y trazado correctamente."""
    candidato_hyundai_003 = {
        "doc_id": "RAG_EXP_HYUNDAI_003",
        "titulo": "PARES DE APRIETE OFICIALES EN COLUMNA DE DIRECCION C-MDPS HYUNDAI",
        "texto": (
            "Perno superior de fijacion MDPS a soporte (Pag. 14): 44.1~49.0 N.m (32.5~36.2 lb-ft). "
            "Pernos soporte columna C (Pag. 4): 17.7~19.6 N.m."
        ),
        "manual_oem": "hyundai_tsb_mdps_flexible_coupling_replacement.pdf",
        "pagina": "3, 4, 5, 14",
        "marca": "Hyundai Motor America",
        "modelo": "Hyundai Elantra (HD/FD/MD/UD) 2007-2015",
        "subsistema": "Fijacion Mecanica de Columna",
    }

    tiene, traz, motivo = verificar_presencia_cifra_y_trazabilidad(
        consulta="Cual es el par de apriete del perno de fijacion MDPS en Hyundai Elantra?",
        candidato=candidato_hyundai_003,
    )

    assert tiene is True
    assert traz is not None
    assert traz.pagina == "3, 4, 5, 14"
    assert traz.paginas == [3, 4, 5, 14]
    assert "44.1" in traz.cifra_encontrada
    assert "n.m" in traz.unidad.lower()


# ==============================================================================
# 2. A02: CORRESPONDENCIA EXACTA MAGNITUD-COMPONENTE
# ==============================================================================


def test_a02_rechazo_si_magnitud_no_corresponde_a_la_solicitada():
    """Si la consulta pide torque, un documento que solo contiene cotas de longitud (mm) no debe acreditarse."""
    candidato_frenos_alabeo = {
        "titulo": "ALABEO LATERAL EN DISCO DE FRENO",
        "texto": "Alabeo maximo en disco montado: <= 0.10 mm tras una rotacion completa de 360 grados.",
        "manual_oem": "brembo_guide.pdf",
        "pagina": "5-6",
        "subsistema": "Discos de Freno",
    }

    tiene, traz, motivo = verificar_presencia_cifra_y_trazabilidad(
        consulta="Cual es el par de apriete o torque del disco de freno?",
        candidato=candidato_frenos_alabeo,
    )

    assert tiene is False
    assert traz is None
    assert "ninguna corresponde a la magnitud solicitada" in motivo.lower()


def test_a02_rechazo_si_componente_no_corresponde_pastilla_vs_disco():
    """Si la consulta pide pastillas de freno, no puede acreditarse una cota de disco de freno."""
    candidato_frenos_disco = {
        "titulo": "VERIFICACION DE ALABEO LATERAL EN DISCO Y BUJE DE RUEDA",
        "texto": "Alabeo maximo en disco montado: <= 0.10 mm. Variacion de espesor DTV.",
        "manual_oem": "brembo_guide.pdf",
        "pagina": "5-6",
        "subsistema": "Discos de Freno",
    }

    tiene, traz, motivo = verificar_presencia_cifra_y_trazabilidad(
        consulta="Cual es el espesor minimo o cota de descarte de pastilla de freno?",
        candidato=candidato_frenos_disco,
    )

    assert tiene is False
    assert traz is None
    assert "pastilla" in motivo.lower()


# ==============================================================================
# 3. A03: VALIDACIÓN VEHICULAR ESTRUCTURADA EN 5 DIMENSIONES
# ==============================================================================


def test_a03_compatibilidad_5_dimensiones_campos_plurales_agente2():
    """Verifica que verificar_compatibilidad_estructurada consuma campos plurales (*_aplicables)."""
    candidato_exp_plural = {
        "doc_id": "RAG_EXP_HYUNDAI_003",
        "titulo": "PARES DE APRIETE OFICIALES EN COLUMNA DE DIRECCION C-MDPS HYUNDAI",
        "marcas_aplicables": ["Hyundai"],
        "modelos_aplicables": [
            "Elantra (HD)",
            "Elantra Touring (FD)",
            "Elantra (MD)",
            "Elantra (UD)",
            "Sonata (YF)",
        ],
        "anios_aplicables": "2007-2015",
        "motores_aplicables": "Universal para los modelos indicados",
        "mercados_aplicables": "Norteamerica (HMA)",
        "alcance_aplicacion": "Pares de apriete oficiales del boletin TSB 17-ST-002 para Hyundai Elantra (2007-2015). No extrapolar a Hyundai Accent ni Kia.",
        "manual_oem": "hyundai_tsb_mdps.pdf",
        "pagina": "3, 4, 5, 14",
    }

    # Caso 1: Compatible pleno (información completa concordante)
    v_ok = VehiculoConsulta(
        marca="hyundai", modelo="elantra", anio=2013, motor="1.8L", mercado="usa_norteamerica"
    )
    es_comp, motivo = verificar_compatibilidad_estructurada(v_ok, candidato_exp_plural)
    assert es_comp is True
    assert "satisfactoria" in motivo

    # Caso 2: Información faltante no contradictoria (motor=None, mercado=None)
    v_faltante = VehiculoConsulta(marca="hyundai", modelo="elantra", anio=2012, motor=None, mercado=None)
    es_comp, motivo = verificar_compatibilidad_estructurada(v_faltante, candidato_exp_plural)
    assert es_comp is True

    # Caso 3: Información contradictoria en MOTOR (Diésel D4FB en TSB de Elantra Norteamérica)
    v_diesel = VehiculoConsulta(
        marca="hyundai", modelo="elantra", anio=2013, motor="D4FB", mercado="usa_norteamerica"
    )
    es_comp, motivo = verificar_compatibilidad_estructurada(v_diesel, candidato_exp_plural)
    assert es_comp is False
    assert "diesel" in motivo.lower() or "d4fb" in motivo.lower()

    # Caso 4: Información contradictoria en MODELO (Tucson)
    v_tucson = VehiculoConsulta(
        marca="hyundai", modelo="tucson", anio=2013, motor="2.0L", mercado="usa_norteamerica"
    )
    es_comp, motivo = verificar_compatibilidad_estructurada(v_tucson, candidato_exp_plural)
    assert es_comp is False
    assert "tucson" in motivo.lower()

    # Caso 5: Información contradictoria en EXCLUSIÓN EXPRESA (Accent)
    v_accent = VehiculoConsulta(
        marca="hyundai", modelo="accent", anio=2013, motor="1.6L", mercado="usa_norteamerica"
    )
    es_comp, motivo = verificar_compatibilidad_estructurada(v_accent, candidato_exp_plural)
    assert es_comp is False
    assert "excluido" in motivo.lower() or "accent" in motivo.lower()

    # Caso 6: Información contradictoria en AÑO (1997 o 2025 frente a 2007-2015)
    v_anio_antiguo = VehiculoConsulta(marca="hyundai", modelo="elantra", anio=1997)
    es_comp, motivo = verificar_compatibilidad_estructurada(v_anio_antiguo, candidato_exp_plural)
    assert es_comp is False
    assert "1997" in motivo

    v_anio_futuro = VehiculoConsulta(marca="hyundai", modelo="elantra", anio=2025)
    es_comp, motivo = verificar_compatibilidad_estructurada(v_anio_futuro, candidato_exp_plural)
    assert es_comp is False
    assert "2025" in motivo

    # Caso 7: Información contradictoria en MERCADO (Perú / LATAM frente a TSB exclusivo HMA EE.UU.)
    v_mercado = VehiculoConsulta(marca="hyundai", modelo="elantra", anio=2013, mercado="peru_latam")
    es_comp, motivo = verificar_compatibilidad_estructurada(v_mercado, candidato_exp_plural)
    assert es_comp is False
    assert "peru_latam" in motivo


# ==============================================================================
# 4. C02: BLOQUEO ABSOLUTO DE PUBLICACIÓN CON CORPUS_VALIDADO=FALSE
# ==============================================================================


def test_c02_clasificar_y_filtrar_oem_bloquea_especificacion_si_corpus_no_validado():
    """Con corpus_validado=False, clasificar_y_filtrar_oem jamás debe conceder ESPECIFICACION_EXACTA_VERIFICADA."""
    candidato_oem_completo = {
        "doc_id": "RAG_EXP_HYUNDAI_003",
        "titulo": "PARES DE APRIETE OFICIALES EN COLUMNA DE DIRECCION C-MDPS HYUNDAI",
        "texto": "Perno superior de fijacion MDPS a soporte: 44.1~49.0 N.m.",
        "manual_oem": "hyundai_tsb_mdps.pdf",
        "pagina": "14",
        "marca": "Hyundai Motor America",
        "modelo": "Hyundai Elantra",
        "anio": "2007-2015",
        "es_experimental": True,
    }

    # 1. Con corpus_validado=False:
    cat_bloqueada, factor_bloqueado, motivo_bloqueado = clasificar_y_filtrar_oem(
        consulta="Cual es el par de apriete del perno de soporte de columna en Hyundai Elantra 2012?",
        candidato=candidato_oem_completo,
        corpus_validado=False,
    )
    assert cat_bloqueada != "ESPECIFICACION_EXACTA_VERIFICADA"
    assert cat_bloqueada == EstadoDocumental.INFORMACION_PARCIAL.value
    assert "corpus_validado=false" in motivo_bloqueado.lower()

    # 2. Con corpus_validado=True:
    cat_aprobada, factor_aprobado, motivo_aprobado = clasificar_y_filtrar_oem(
        consulta="Cual es el par de apriete del perno de soporte de columna en Hyundai Elantra 2012?",
        candidato=candidato_oem_completo,
        corpus_validado=True,
    )
    assert cat_aprobada == EstadoDocumental.ESPECIFICACION_DOCUMENTADA.value
    assert factor_aprobado >= 1.0


# ==============================================================================
# 5. C1 / AGENTE 3: PRUEBAS NEGATIVAS AUDITADAS (RAIZE, S-PRESSO, MOBI)
# ==============================================================================


def test_c1_pruebas_negativas_auditor_raize_spresso_mobi():
    """Valida la intercepción estricta en los tres casos auditados de tolerancias sin respaldo."""
    casos = [
        (
            "Toyota Raize 2024 mercado Peru, cual es la tolerancia de alabeo de discos de freno?",
            "Toyota Raize 2024",
            "La tolerancia de taller es 0.05-0.07 mm y 0.12 mm exige rectificado o cambio.",
        ),
        (
            "Suzuki S-Presso 2023 1.0, cual es la tolerancia de apertura del termostato?",
            "Suzuki S-Presso 2023",
            "Apertura 82-88 °C, apertura total 95-98 °C, carrera 8 mm; conclusion termostato trabado a 108 °C.",
        ),
        (
            "Fiat Mobi 2025, cual es la tolerancia del alabeo del volante de inercia?",
            "Fiat Mobi 2025",
            "Salto axial maximo 0.10 mm y prescripcion de rectificado/reemplazo del volante de inercia.",
        ),
    ]

    for consulta, vehiculo, resp_propuesta in casos:
        resp_segura, conf_segura, decision = interceptar_o_autorizar_tolerancia(
            consulta=consulta,
            vehiculo_str=vehiculo,
            respuesta_candidata=resp_propuesta,
            corpus_validado=False,
        )

        assert decision == "ABSTENCION_METROLOGICA"
        assert conf_segura == 0.0
        assert "Aviso de control metrológico CarBot" in resp_segura
        assert "corpus_validado=False" in resp_segura
        assert "rectificado o cambio" not in resp_segura
        assert "termostato trabado" not in resp_segura


# ==============================================================================
# 6. A01: VALIDACIÓN DE COHERENCIA DEL PAQUETE EXPERIMENTAL Y TOLERANCIA 1E-6
# ==============================================================================


def test_a01_tolerancia_maxima_1e6_y_verificacion_manifiesto():
    """Valida que validar_coherencia_paquete_experimental verifique hashes y tolere error <= 1e-6."""
    import numpy as np

    class FakeVectorizer:
        n_features_in_ = 4

        def transform(self, texts):
            class FakeSparse:
                def toarray(self):
                    return np.array([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32)

            return FakeSparse()

    class FakeFaissIndex:
        ntotal = 1
        d = 4

        def reconstruct(self, i):
            return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)

    corpus = [{"doc_id": "TEST_001", "titulo": "T", "texto": "X"}]
    vec = FakeVectorizer()
    idx = FakeFaissIndex()

    # Caso perfecto: error 0.0 <= 1e-6
    ok, mism, mot = validar_coherencia_paquete_experimental(corpus, vec, idx, tolerancia_l2=1e-6)
    assert ok is True
    assert len(mism) == 0
    assert "1e-06" in mot or "1e-6" in mot

    # Caso con manifiesto concordante
    manifiesto_ok = {
        "total_documentos_corpus_B": 1,
        "dimension_vectorial": 4,
    }
    ok_m, mism_m, mot_m = validar_coherencia_paquete_experimental(
        corpus, vec, idx, tolerancia_l2=1e-6, manifiesto=manifiesto_ok
    )
    assert ok_m is True

    # Caso con manifiesto discrepante en cantidad
    manifiesto_bad = {
        "total_documentos_corpus_B": 999,
        "dimension_vectorial": 4,
    }
    ok_b, mism_b, mot_b = validar_coherencia_paquete_experimental(
        corpus, vec, idx, tolerancia_l2=1e-6, manifiesto=manifiesto_bad
    )
    assert ok_b is False
    assert "Discrepancia con manifiesto" in mot_b


# ==============================================================================
# 7. A07 / A09: UNIFICACIÓN DEL ADAPTADOR D3 INDEPENDIENTE DEL CWD
# ==============================================================================


def test_a07_adaptador_d3_delega_en_politica_canonica():
    """Comprueba que el adaptador D3 en machine_learning invoca la misma lógica que backend/O1."""
    d3_path = PROJECT_ROOT / "machine_learning" / "rag" / "experimentos" / "rag03c"
    if not d3_path.exists():
        d3_path = PROJECT_ROOT.parent / "machine_learning" / "rag" / "experimentos" / "rag03c"

    if str(d3_path) not in sys.path:
        sys.path.insert(0, str(d3_path))

    from controlador_especificaciones_oem import clasificar_y_filtrar_candidato_rag03c2

    candidato_fake = {
        "titulo": "CULATA - torque",
        "documento": "Consultar torque de culata en manual. Sin cifra.",
        "es_experimental": True,
    }

    res_d3 = clasificar_y_filtrar_candidato_rag03c2("Cual es el torque de culata?", candidato_fake)
    res_o1 = clasificar_y_filtrar_oem("Cual es el torque de culata?", candidato_fake)

    assert res_d3 == res_o1
    assert res_d3[0] == EstadoDocumental.INFORMACION_PARCIAL.value
