"""Prueba automatizada de recuperación RAG multimarca y metadatos técnicos."""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ / "backend") not in sys.path:
    sys.path.insert(0, str(RAIZ / "backend"))

from src.infrastructure.motor_rag import MotorRAG  # noqa: E402


def probar_recuperacion():
    print("=" * 80)
    print("EVALUACIÓN DE RECUPERACIÓN RAG MULTIMARCA Y FRAGMENTOS DEL CORPUS PRELIMINAR")
    print("=" * 80)

    motor = MotorRAG()
    print(f"Total procedimientos indexados en FAISS: {len(motor.documentos)}")
    assert len(motor.documentos) >= 50, f"Se esperaban >= 50 procedimientos, hay {len(motor.documentos)}"

    casos_prueba = [
        {
            "query": "Toyota Prius bateria de alto voltaje inversor error p0a80",
            "marca_esperada": "Toyota",
            "modelo_esperado": "Prius HEV",
        },
        {
            "query": "Toyota Yaris pedal de embrague no desembraga bombin hidraulico",
            "marca_esperada": "Toyota",
            "modelo_esperado": "Yaris",
        },
        {
            "query": "Nissan Sentra transmision automatica CVT sobrecalentamiento solenoide p0700",
            "marca_esperada": "Nissan",
            "modelo_esperado": "Sentra",
        },
        {
            "query": "Sistema de conversion a GNV GLP 5ta generacion calibracion rampa",
            "marca_esperada": "Multimarca GNV/GLP",
            "modelo_esperado": "Sistemas 5ta Generación",
        },
        {
            "query": "Frenos de aire neumaticos camiones Scania Volvo perdida de presion",
            "marca_esperada": "Universal / Multimarca",
        }
    ]

    aciertos = 0
    for i, caso in enumerate(casos_prueba, start=1):
        q = caso["query"]
        cuerpo, titulo, sim, meta = motor.recuperar_procedimiento_con_metadatos(q, umbral=0.05)
        print(f"\n[Caso {i}] Consulta: '{q}'")
        print(f"   -> Título Recuperado: {titulo[:70]}...")
        print(f"   -> Similitud Coseno FAISS: {sim:.4f}")
        print(f"   -> Marca: {meta.get('marca')} | Modelo: {meta.get('modelo')} | Fuente: {meta.get('manual_oem')}")
        print(f"   -> Edición: {meta.get('edicion')} | Página: {meta.get('pagina')}")

        valido = sim > 0.05 and meta.get("marca") == caso["marca_esperada"]
        if "modelo_esperado" in caso:
            valido = valido and meta.get("modelo") == caso["modelo_esperado"]

        if valido:
            aciertos += 1
            print("   [OK] Recuperacion RAG consistente (fragmento relevante del corpus preliminar)")
        else:
            print("   [WARN] Coincidencia generica")

    print("\n" + "=" * 80)
    print(f"RESULTADO FINAL: {aciertos}/{len(casos_prueba)} pruebas RAG superadas con éxito.")
    print("=" * 80)
    assert aciertos == len(casos_prueba), "No todos los casos RAG alcanzaron la recuperación esperada"

if __name__ == "__main__":
    probar_recuperacion()
