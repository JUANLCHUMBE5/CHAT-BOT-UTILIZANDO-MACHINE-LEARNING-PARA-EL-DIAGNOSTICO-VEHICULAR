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


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("El equipo es gnb", "gnv"),
        ("Funciona con G.N.B.", "gnv"),
        ("Tiene glb", "glp"),
        ("Cuando acelera se chanchea", "pierde potencia"),
        ("En subida se vuelve chancho", "pierde potencia"),
        ("A velocidad se achancha", "pierde potencia"),
        ("Tiene vibraciones al menjar", "vibracion al manejar"),
        (
            "Sale humo blanco por el escape y consume refrigerante",
            "vapor blanco consume refrigerante posible empaque de culata",
        ),
        (
            "El scanner indica P0300 misfire en cilindros",
            "codigo p0300 de falla de encendido multiple",
        ),
    ],
)
def test_normaliza_variantes_de_dictado_y_escritura(entrada, esperado):
    assert esperado in normalizar_jerga_peruana(entrada)
