"""Pruebas exhaustivas del normalizador de jerga técnica automotriz peruana y latinoamericana."""

from __future__ import annotations

from src.core.traductor_jerga import normalizar_jerga_peruana


def test_traduccion_balatas_a_pastillas():
    texto = "Las balatas delanteras chillan al frenar"
    resultado = normalizar_jerga_peruana(texto)
    assert "pastillas de freno" in resultado
    assert "balatas" not in resultado


def test_traduccion_clutch_y_cloche_a_embrague():
    casos = [
        "El clutch patina en tercera subiendo cerro",
        "El cloche se fue hasta el fondo del piso",
    ]
    for c in casos:
        resultado = normalizar_jerga_peruana(c)
        assert "embrague" in resultado
        assert "clutch" not in resultado
        assert "cloche" not in resultado


def test_traduccion_burro_de_arranque_a_motor_de_arranque():
    texto = "Giro la llave y el burro de arranque no gira nada"
    resultado = normalizar_jerga_peruana(texto)
    assert "motor de arranque" in resultado
    assert "burro de arranque" not in resultado


def test_traduccion_anticongelante_a_refrigerante():
    texto = "Bota todo el anticongelante por una manguera rota"
    resultado = normalizar_jerga_peruana(texto)
    assert "refrigerante" in resultado
    assert "anticongelante" not in resultado


def test_traduccion_banda_de_tiempo_a_faja_de_distribucion():
    texto = "Se rompió la banda de tiempo en plena carretera"
    resultado = normalizar_jerga_peruana(texto)
    assert "faja de distribucion" in resultado
    assert "banda de tiempo" not in resultado


def test_traduccion_mofle_exosto_a_silenciador_de_escape():
    for m in ["Suena ronco el mofle al acelerar", "El exosto está picado abajo"]:
        resultado = normalizar_jerga_peruana(m)
        assert "silenciador de escape" in resultado


def test_traduccion_cabezote_y_empacadura_a_culata_y_empaque():
    texto = "Se quemó la empacadura de culata del cabezote"
    resultado = normalizar_jerga_peruana(texto)
    assert "empaque de culata" in resultado
    assert "culata" in resultado


def test_traduccion_shock_absorber_a_amortiguador():
    texto = "El shock absorber izquierdo está chorreando aceite"
    resultado = normalizar_jerga_peruana(texto)
    assert "amortiguador" in resultado
    assert "shock absorber" not in resultado


def test_traduccion_volante_de_direccion_a_timon():
    texto = "El volante de direccion tiembla a 80 por hora"
    resultado = normalizar_jerga_peruana(texto)
    assert "timon" in resultado


def test_traduccion_planchado_y_pintura():
    casos = [
        "Necesito presupuesto de latoneria y pintura para un choque",
        "Taller de hojalateria y pintura",
    ]
    for c in casos:
        resultado = normalizar_jerga_peruana(c)
        assert "planchado y pintura" in resultado


def test_traduccion_plumillas_a_plumas_limpiaparabrisas():
    texto = "No limpian bien las plumillas del limpiaparabrisas"
    resultado = normalizar_jerga_peruana(texto)
    assert "plumas de limpiaparabrisas" in resultado


def test_normalizacion_cafe_con_leche_o_mayonesa_empaque_culata():
    casos = [
        "El aceite parece cafe con leche al sacar la varilla",
        "Hay una pasta como mayonesa en la tapa de aceite",
        "El aceite lechoso emulsionado con agua",
    ]
    for c in casos:
        resultado = normalizar_jerga_peruana(c)
        assert "se mezcla el agua con el aceite" in resultado or "chocolatada" in resultado


def test_normalizacion_burbujeo_en_radiador():
    texto = "Veo burbujas en el deposito de refrigerante con el motor prendido"
    resultado = normalizar_jerga_peruana(texto)
    assert "radiador bota burbujas" in resultado


def test_normalizacion_se_achancha():
    texto = "Al pisar el acelerador el carro se chanchea y no responde"
    resultado = normalizar_jerga_peruana(texto)
    assert "pierde potencia y presenta tirones" in resultado


def test_preserva_siglas_gnv_glp():
    casos = [
        ("Falla en g.n.v. cuando acelero", "gnv"),
        ("Tironea en g-l-p", "glp"),
        ("Cambia de gasolina a autogas", "glp"),
    ]
    for entrada, esperada in casos:
        resultado = normalizar_jerga_peruana(entrada)
        assert esperada in resultado
