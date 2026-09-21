import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend"))
from src.infrastructure.motor_rag import MotorRAG
from src.config import settings

rag = MotorRAG(settings.paths.manual_file)
print(f"Total procedimientos indexados en FAISS: {len(rag.documentos)}")

codigos_test = ["P0301", "P0171", "P0420", "P0562", "P0087", "P0505", "P0016"]
print("\n=== PRUEBAS DE RECUPERACIÓN RAG PARA CÓDIGOS DTC ===")
for c in codigos_test:
    doc, tit, sim, meta = rag.recuperar_procedimiento_con_metadatos(f"Tengo el codigo {c}")
    print(f"Consulta: '{c}' -> Titulo: '{tit}' (Similitud: {sim:.2f})")
