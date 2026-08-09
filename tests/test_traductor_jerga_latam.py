import pytest

from src.core.traductor_jerga import normalizar_jerga_peruana


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("Las balatas chillan al frenar", "pastillas de freno"),
        ("El cloche patina en subida", "embrague"),
        ("El burro de arranque solo hace clic", "motor de arranque"),
        ("Pierde coolant por una manga", "refrigerante"),
        ("Suena el rulemán delantero", "rodamiento"),
        ("El mofle bota humo negro", "silenciador de escape"),
        ("La cajuela no abre", "maletera"),
        ("El elevalunas no sube", "elevador de vidrio"),
    ],
)
def test_normaliza_variantes_latam_a_vocabulario_peruano(entrada, esperado):
    assert esperado in normalizar_jerga_peruana(entrada)


def test_no_convierte_cardan_en_palier_por_ser_ambiguo():
    normalizado = normalizar_jerga_peruana("El cardán vibra en carretera")
    assert "cardán" in normalizado
    assert "palier" not in normalizado
