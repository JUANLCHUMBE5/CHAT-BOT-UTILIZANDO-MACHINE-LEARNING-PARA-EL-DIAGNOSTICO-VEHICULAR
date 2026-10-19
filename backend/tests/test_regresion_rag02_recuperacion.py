"""
Pruebas de regresion y validacion tecnica para Fase RAG-02.
Verifica que las mejoras en query_expansion, query_builder y relevance_filter
resuelvan la sobreexpansion lexica y los conflictos de marca,
preservando la recuperacion valida en todos los sistemas.
"""

import pytest

from src.infrastructure.motor_rag import MotorRAG


@pytest.fixture(scope="module")
def motor_rag():
    return MotorRAG()


class TestCasosInformeRAG02:
    """Los 10 casos evaluados en el informe RAG-02."""

    def test_caso1_recalienta_humo_blanco_culata(self, motor_rag):
        consulta = "humo blanco por el escape y consume refrigerante se recalienta"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="MOTOR",
        )
        assert meta.get("doc_id") == "RAG_PROC_012"
        assert "culata" in titulo.lower() or "empaquetadura" in titulo.lower()
        assert "ckp" not in titulo.lower()

    def test_caso2_slang_soplo_empaque(self, motor_rag):
        consulta = "soplo empaque bota humo blanco por el escape y hierve el agua en el tacho"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="MOTOR",
        )
        assert meta.get("doc_id") == "RAG_PROC_012"
        assert "culata" in titulo.lower()

    def test_caso3_frenos_nissan_versa_multimarca(self, motor_rag):
        consulta = "cambio de pastillas de freno delanteras"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="FRENOS",
            marca="Nissan",
            modelo="Versa",
        )
        assert meta.get("doc_id") != "RAG_PROC_055"
        assert meta.get("vehicle_scope") == "UNIVERSAL"

    def test_caso4_ckp_falla_termica_genuina(self, motor_rag):
        consulta = "el motor enciende bien en frio pero al calentar se apaga y no arranca hasta que enfria"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="MOTOR",
        )
        assert meta.get("doc_id") == "RAG_PROC_176"
        assert "ckp" in titulo.lower() or "cigueñal" in titulo.lower()

    def test_caso5_eps_columna_generico(self, motor_rag):
        consulta = "ruido y golpeteo en la columna de direccion asistida electrica eps"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="SUSPENSION_CHASIS",
        )
        assert meta.get("doc_id") == "RAG_PROC_070"

    def test_caso6_eps_columna_hyundai(self, motor_rag):
        consulta = "ruido y golpeteo en la columna de direccion asistida electrica eps"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="SUSPENSION_CHASIS",
            marca="Hyundai",
            modelo="Accent",
        )
        assert meta.get("doc_id") == "RAG_PROC_070"
        assert meta.get("vehicle_scope") == "UNIVERSAL"

    def test_caso7_frenos_purga_c0040(self, motor_rag):
        consulta = "pedal de freno se va al fondo y esta esponjoso posible aire en cañerias"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="FRENOS",
            codigos_dtc=["C0040"],
        )
        assert meta.get("doc_id") == "RAG_PROC_001"

    def test_caso8_mezcla_pobre_p0171(self, motor_rag):
        consulta = "motor tironea en baja codigo p0171 sensor oxigeno mezcla pobre"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="MOTOR",
            codigos_dtc=["P0171"],
        )
        assert meta.get("doc_id") == "RAG_PROC_018"

    def test_caso9_cvt_nissan_sentra_especifico(self, motor_rag):
        consulta = "transmision zumba y desliza en aceleracion aceite cvt degradado"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="TRANSMISION",
            codigos_dtc=["P0700"],
            marca="Nissan",
            modelo="Sentra",
        )
        assert meta.get("doc_id") == "RAG_PROC_050"
        assert meta.get("make") == "Nissan"

    def test_caso10_arranque_clac_caida_tension(self, motor_rag):
        consulta = "le doy arranque hace clac seco y no gira el motor"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="ELECTRICO",
        )
        assert meta.get("doc_id") == "RAG_PROC_216"


class TestBateriaIndependienteNoVista:
    """Consultas independientes no utilizadas durante el diseno de las reglas."""

    def test_humo_azul_aceite(self, motor_rag):
        consulta = "humo azul constante por el escape al acelerar y consumo de aceite"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="MOTOR",
        )
        assert "ckp" not in titulo.lower()
        assert sim >= 0.20

    def test_fuga_refrigerante_radiador_goteo(self, motor_rag):
        consulta = "fuga de refrigerante visible en radiador y goteo constante al suelo"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="MOTOR",
        )
        assert "ckp" not in titulo.lower()
        assert "fuga" in titulo.lower() or "radiador" in titulo.lower() or "refrigeracion" in titulo.lower()

    def test_bateria_descarga_parasita_nocturna(self, motor_rag):
        consulta = "bateria nueva se descarga al cabo de una noche consumo parasito apagado"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="ELECTRICO",
        )
        assert meta.get("doc_id") in ("RAG_PROC_087", "RAG_PROC_217", "RAG_PROC_200")
        assert any(k in titulo.lower() for k in ("batería", "bateria", "voltaje", "parásito", "parasito"))

    def test_freno_tambor_trasero_freno_mano_alto(self, motor_rag):
        consulta = "freno de mano queda demasiado alto y no frena zapatas de tambor trasero"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="FRENOS",
        )
        assert meta.get("doc_id") == "RAG_PROC_002"

    def test_servofreno_booster_pedal_duro(self, motor_rag):
        consulta = "pedal de freno duro silbido de vacio al pisar booster con fuga"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="FRENOS",
        )
        assert "booster" in titulo.lower() or "servofreno" in titulo.lower()

    def test_caja_automatica_golpe_valvulas(self, motor_rag):
        consulta = "caja automatica golpea fuerte al cambiar de marcha fluido degradado"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="TRANSMISION",
        )
        assert "transmision" in titulo.lower() or "caja" in titulo.lower() or "cvt" in titulo.lower()

    def test_toyota_yaris_asigna_procedimiento_toyota(self, motor_rag):
        # Cuando el vehiculo SI es Toyota Yaris, SI debe recuperar el manual especifico de Toyota
        consulta = "cambio de pastillas de freno delanteras"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="FRENOS",
            marca="Toyota",
            modelo="Yaris",
        )
        assert meta.get("doc_id") == "RAG_PROC_055"
        assert meta.get("make") == "Toyota"

    def test_chevrolet_spark_no_asigna_procedimiento_toyota(self, motor_rag):
        # Cuando el vehiculo es Chevrolet, debe recuperar el universal y NO el de Toyota Yaris
        consulta = "cambio de pastillas de freno delanteras"
        doc, titulo, sim, meta = motor_rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="FRENOS",
            marca="Chevrolet",
            modelo="Spark",
        )
        assert meta.get("doc_id") != "RAG_PROC_055"
        assert meta.get("vehicle_scope") == "UNIVERSAL"
