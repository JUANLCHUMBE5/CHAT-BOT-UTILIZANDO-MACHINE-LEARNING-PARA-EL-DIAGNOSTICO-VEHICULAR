import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from src.core.gestor_diagnostico import GestorDiagnostico

gestor = GestorDiagnostico()
t = "Tracker 2018 batería amanece descargada a 11.2V tras 3 días parqueado. Se midió corriente de fuga con multímetro en serie con borne negativo y marca 180 mA continuos tras apagado de módulos."

res = gestor.procesar_consulta_texto(t, session_id="test_trace_dev53")
print("Diagnostico ML:", res.diagnostico_ml)
print("Modo diagnostico:", res.modo_diagnostico)
print("Tipo consulta:", res.tipo_consulta)
print("Respuesta texto:", res.respuesta_texto[:150])
