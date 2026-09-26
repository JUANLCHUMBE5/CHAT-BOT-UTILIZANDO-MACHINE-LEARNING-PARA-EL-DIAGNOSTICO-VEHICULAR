"""SIMULACION_POST_V2: conversaciones locales aisladas, nunca datos de tesis."""
from __future__ import annotations

import csv
import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
from src.core.gestor_diagnostico import GestorDiagnostico

V1 = Path(__file__).with_name("ejecutar_simulacion_post_local.py")
spec = importlib.util.spec_from_file_location("v1", V1)
v1 = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(v1)
SALIDA = ROOT / "docs" / "simulaciones_tecnicas" / "simulacion_post_v2_202609"
RESPUESTAS = [
    "Falla detenido, mejora acelerando y no prende check.", "Las luces bajan, gira lento y mejora tras cargar batería.",
    "Tironea en subida, consume más y no bota humo negro.", "Tiembla detenido, pierde fuerza y parece fallar un cilindro.",
    "Huele incluso parado, consume más y sale humo oscuro leve.", "Solo ocurre en mínimo, acelerando mejora y no se calienta.",
    "Baja el refrigerante, hay ruido adelante y no veo charco grande.", "Solo en tráfico, el ventilador no prende y en carretera baja.",
    "Suena con el aire, la correa está rajada y la dirección normal.", "Solo frenando, más fuerte a velocidad y pedal firme.",
    "Pedal esponjoso, mejora bombeando y depósito parece normal.", "Aumenta con velocidad, cambia al girar y no golpea baches.",
    "Suena solo en baches, no vibra en carretera y es adelante.", "Golpeó un hueco, gasta por dentro y se va a un lado.",
    "Rebota varias veces, motor normal y no pierde fuerza.", "Consume más, check prendido y no humea negro fuerte.",
    "Pierde fuerza, filtro de aire sucio y no veo manguera suelta.", "Velocímetro se cae, odómetro falla y cambios normales.",
    "Revoluciona sin avanzar, huele quemado y pasa en subida.", "Pedal se queda abajo, líquido bajo y apagado entra mejor.",
    "Solo hace clic, luces débiles y bornes se ven normales.", "Luz prende andando, carga baja y correa está puesta.",
    "Empeora con baches, borne negativo sulfatado y batería nueva.", "Después de cargar falla, huele gasolina y no mantiene presión.",
    "Solo acelerando fuerte, mejora soltando y mínimo normal.", "Pasa caliente, tiembla bastante y check prendido.",
    "Mínimo muy bajo, acelerando no se apaga y no recalienta.", "Ruido cerca de bomba, baja refrigerante y sube andando.",
    "Una rueda queda caliente, queda frenado y se va a un lado.", "Volante tiene juego, golpea baches y llanta gasta irregular.",
]

def serializar(resultado):
    return [p.model_dump() for p in (resultado.predicciones_ml or [])]

def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    gestor = GestorDiagnostico(); gestor._registrar_en_tracker = lambda **_: None
    filas = []
    for i, (sintoma, _) in enumerate(v1.CASOS, 1):
        placa, sesion = f"SIMPOSTV2-{i:03d}", f"sim-post-v2-{i:03d}"
        conversacion, inicio = [], time.perf_counter()
        texto, respuesta = sintoma, RESPUESTAS[i - 1]
        for turno in range(1, 5):
            r = gestor.procesar_consulta_texto(texto, placa=placa, marca_modelo="Vehículo de simulación", session_id=sesion, proveedor="simulacion_post_v2")
            conversacion.append({"turno": turno, "entrada": texto, "respuesta_carbot": r.respuesta_texto, "modo": r.modo_diagnostico})
            if r.modo_diagnostico != "esperando_clarificacion": break
            texto = respuesta if turno == 1 else "No se cuenta con ese dato en esta simulación."
        filas.append({
            "id_caso": f"SIMULACION_POST_V2_{i:03d}", "estado": "SIMULACION_POST_V2", "tipo_registro": "DEVELOPMENT",
            "fecha_hora": datetime.now(timezone.utc).isoformat(), "placa_simulada": placa, "sintoma_inicial": sintoma,
            "referencia_congelada": v1.REFERENCIAS_ESPECIFICAS[i - 1], "respuestas_permitidas": respuesta,
            "conversacion": json.dumps(conversacion, ensure_ascii=False), "preguntas_carbot": json.dumps([x["respuesta_carbot"] for x in conversacion[:-1]], ensure_ascii=False),
            "respuestas_proporcionadas": json.dumps([x["entrada"] for x in conversacion[1:]], ensure_ascii=False), "interacciones": len(conversacion),
            "diagnostico_final_carbot": r.diagnostico_ml, "top3": json.dumps(serializar(r), ensure_ascii=False), "confianza": r.confianza_ml,
            "estado_final": r.modo_diagnostico, "solicitud_id": r.solicitud_id or "", "tiempo_tecnico_total_ms": round((time.perf_counter()-inicio)*1000,2),
            "igualdad_exacta": v1.normalizar(r.diagnostico_ml) == v1.normalizar(v1.REFERENCIAS_ESPECIFICAS[i-1]), "error": "",
        })
        print(f"[{i:02d}/30] {r.modo_diagnostico}")
    campos = list(filas[0]);
    with (SALIDA / "SIMULACION_POST_V2_30_CONVERSACIONES.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w=csv.DictWriter(f, fieldnames=campos); w.writeheader(); w.writerows(filas)
    print(SALIDA)

if __name__ == "__main__": main()
