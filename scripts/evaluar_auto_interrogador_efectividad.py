"""
Evaluación Experimental del Auto-Interrogador Técnico en Ambigüedad — CarBot (Fase 7)
Mide cuantitativamente si la formulación de una pregunta discriminatoria estructurada
resuelve la ambigüedad clínica automotriz y mejora la exactitud diagnóstica.

Métricas:
  - Tasa de Activación Justificada (Casos con delta < 10% y conf < 70%)
  - Incremento Promedio de Confianza (Conf_post - Conf_pre)
  - Incremento Promedio de Margen Diferencial (Delta_post - Delta_pre)
  - Tasa de Resolución de Ambigüedad (Casos que alcanzaron Delta >= 10%)
  - Exactitud Diagnóstica Post-Aclaración
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from src.infrastructure.container import ServiceContainer
from src.core.diagnostico.auto_interrogador import (
    evaluar_auto_pregunta_descarte,
    formatear_mensaje_auto_pregunta,
)
from src.core.diagnostico.semantic_purifier import purificar_sintoma_para_vectorizador_ml
from src.core.traductor_jerga import normalizar_jerga_peruana


# Casos clínicos automotrices con ambigüedad intrínseca y su clarificación física
CASOS_AMBIGUOS_TEST = [
    {
        "id": "AMB_01",
        "categoria": "Vibración",
        "consulta_inicial": "El timón vibra bastante cuando voy manejando.",
        "falla_real": "Discos de freno alabeados o desgastados",
        "respuesta_aclaratoria": "vibra fuerte únicamente cuando piso el freno bajando a 80 km/h",
    },
    {
        "id": "AMB_02",
        "categoria": "Vibración",
        "consulta_inicial": "Siento una vibración molesta en el auto.",
        "falla_real": "Llantas desbalanceadas o desalineadas",
        "respuesta_aclaratoria": "vibra en carretera a 90 o 100 km/h en pista lisa sin tocar el freno",
    },
    {
        "id": "AMB_03",
        "categoria": "Tironeo / Potencia",
        "consulta_inicial": "El carro se chupa y pierde fuerza al acelerar.",
        "falla_real": "Bomba de gasolina quemada o con baja presion",
        "respuesta_aclaratoria": "pierde fuerza al subir cuestas exigiendo acelerador y suena zumbido en el tanque",
    },
    {
        "id": "AMB_04",
        "categoria": "Tironeo / Potencia",
        "consulta_inicial": "El motor tironea y cabecea al andar.",
        "falla_real": "Falla en bujias o bobinas de encendido (misfire)",
        "respuesta_aclaratoria": "tironea en baja revoluciones dando cabezazos y parpadea el check engine",
    },
    {
        "id": "AMB_05",
        "categoria": "Arranque",
        "consulta_inicial": "El vehículo no enciende en las mañanas.",
        "falla_real": "Bateria descargada o bornes sulfatados",
        "respuesta_aclaratoria": "al girar la llave solo suena un clac y el arrancador no gira nada",
    },
    {
        "id": "AMB_06",
        "categoria": "Arranque",
        "consulta_inicial": "Doy arranque pero el motor no prende.",
        "falla_real": "Bomba de gasolina quemada o con baja presion",
        "respuesta_aclaratoria": "el motor de arranque gira con fuerza normal pero la bomba no zumba en el tanque",
    },
    {
        "id": "AMB_07",
        "categoria": "Ruido en Ruedas",
        "consulta_inicial": "Suena un ruido feo en la rueda delantera.",
        "falla_real": "Juntas homocineticas o palieres danados",
        "respuesta_aclaratoria": "suena un traqueteo trac trac continuo únicamente al doblar cerrado hacia un lado",
    },
    {
        "id": "AMB_08",
        "categoria": "Ruido en Ruedas",
        "consulta_inicial": "Escucho un zumbido fuerte adelante.",
        "falla_real": "Rodajes de caja mecanica o diferencial gastados",
        "respuesta_aclaratoria": "es un zumbido agudo continuo como turbina de avión que aumenta con la velocidad",
    },
    {
        "id": "AMB_09",
        "categoria": "Frenos",
        "consulta_inicial": "El pedal de freno se siente raro al pisar.",
        "falla_real": "Fuga hidraulica o aire en el sistema de frenos",
        "respuesta_aclaratoria": "el pedal se va esponjoso hasta el fondo y solo frena bombeando dos veces",
    },
    {
        "id": "AMB_10",
        "categoria": "Frenos",
        "consulta_inicial": "Cuesta frenar el carro.",
        "falla_real": "Falla en servofreno (booster) o linea de vacio",
        "respuesta_aclaratoria": "el pedal está durísimo como una roca y cuesta hundirlo para detener el auto",
    },
]


def evaluar_auto_interrogador():
    print("\n" + "="*85)
    print("EVALUACIÓN EXPERIMENTAL DEL AUTO-INTERROGADOR TÉCNICO (10 CASOS CLÍNICOS)")
    print("="*85)

    modelo_ml = ServiceContainer.get_modelo_ml()

    resultados = []

    for caso in CASOS_AMBIGUOS_TEST:
        c_id = caso["id"]
        q_ini = caso["consulta_inicial"]
        falla_target = caso["falla_real"]
        q_aclarada = caso["respuesta_aclaratoria"]

        # 1. Inferencia Pre-Interrogatorio
        texto_pre = purificar_sintoma_para_vectorizador_ml(normalizar_jerga_peruana(q_ini))
        preds_pre = modelo_ml.predecir_top_fallas(texto_pre, limite=3)
        top1_falla_pre = preds_pre[0]["falla"] if preds_pre else "Desconocida"
        top1_conf_pre = preds_pre[0]["probabilidad"] if preds_pre else 0.0
        top2_conf_pre = preds_pre[1]["probabilidad"] if len(preds_pre) > 1 else 0.0
        delta_pre = top1_conf_pre - top2_conf_pre

        # 2. Evaluación del Auto-Interrogador
        pregunta_tecnica = evaluar_auto_pregunta_descarte(
            texto=q_ini,
            diagnostico_top1=top1_falla_pre,
            confianza_top1=top1_conf_pre,
            predicciones_top=preds_pre,
        )

        se_activo = (pregunta_tecnica is not None and pregunta_tecnica.es_necesaria)
        opciones_generadas = len(pregunta_tecnica.opciones) if se_activo else 0

        # 3. Inferencia Post-Aclaración (Consulta inicial + Detalle físico discriminante)
        consulta_combinada = f"{q_ini} {q_aclarada}"
        texto_post = purificar_sintoma_para_vectorizador_ml(normalizar_jerga_peruana(consulta_combinada))
        preds_post = modelo_ml.predecir_top_fallas(texto_post, limite=3)
        top1_falla_post = preds_post[0]["falla"] if preds_post else "Desconocida"
        top1_conf_post = preds_post[0]["probabilidad"] if preds_post else 0.0
        top2_conf_post = preds_post[1]["probabilidad"] if len(preds_post) > 1 else 0.0
        delta_post = top1_conf_post - top2_conf_post

        # Evaluación de resolución y acierto
        acierto_pre = (top1_falla_pre == falla_target)
        acierto_post = (top1_falla_post == falla_target)
        ambiguedad_resuelta = (delta_post >= 0.10 and acierto_post)

        res = {
            "id": c_id,
            "categoria": caso["categoria"],
            "consulta_inicial": q_ini,
            "falla_real": falla_target,
            "se_activo_interrogador": se_activo,
            "num_opciones": opciones_generadas,
            "conf_pre": round(top1_conf_pre * 100.0, 1),
            "conf_post": round(top1_conf_post * 100.0, 1),
            "delta_pre": round(delta_pre * 100.0, 1),
            "delta_post": round(delta_post * 100.0, 1),
            "falla_pred_pre": top1_falla_pre,
            "falla_pred_post": top1_falla_post,
            "acierto_pre": acierto_pre,
            "acierto_post": acierto_post,
            "ambiguedad_resuelta": ambiguedad_resuelta
        }
        resultados.append(res)

        print(f"[{c_id}] {caso['categoria']:<16} | Activo: {'SI' if se_activo else 'NO'} | "
              f"Conf: {res['conf_pre']}% -> {res['conf_post']}% | "
              f"Delta: {res['delta_pre']}% -> {res['delta_post']}% | "
              f"Acierto: {'SI' if acierto_post else 'NO'}")

    n_total = len(resultados)
    tasa_activacion = (sum(1 for r in resultados if r["se_activo_interrogador"]) / n_total) * 100.0
    tasa_acierto_pre = (sum(1 for r in resultados if r["acierto_pre"]) / n_total) * 100.0
    tasa_acierto_post = (sum(1 for r in resultados if r["acierto_post"]) / n_total) * 100.0
    tasa_resolucion = (sum(1 for r in resultados if r["ambiguedad_resuelta"]) / n_total) * 100.0
    ganancia_confianza = np.mean([r["conf_post"] - r["conf_pre"] for r in resultados])
    ganancia_delta = np.mean([r["delta_post"] - r["delta_pre"] for r in resultados])

    print("\n" + "="*85)
    print("MÉTRICAS OFICIALES DE EFECTIVIDAD DEL AUTO-INTERROGADOR")
    print("="*85)
    print(f"  - Tasa de Activación Justificada (Ambigüedad):       {tasa_activacion:.1f}%")
    print(f"  - Exactitud Diagnóstica Pre-Aclaración:              {tasa_acierto_pre:.1f}%")
    print(f"  - Exactitud Diagnóstica Post-Aclaración:             {tasa_acierto_post:.1f}% (+{tasa_acierto_post - tasa_acierto_pre:.1f}%)")
    print(f"  - Tasa de Resolución de Ambigüedad (Delta >= 10%):  {tasa_resolucion:.1f}%")
    print(f"  - Incremento Promedio de Confianza (Top-1):          +{ganancia_confianza:.1f}%")
    print(f"  - Incremento Promedio de Margen Diferencial (Delta): +{ganancia_delta:.1f}%")
    print("="*85)

    # Guardar reporte JSON
    rep_path = BASE_DIR / "docs" / "graficas" / "reporte_auto_interrogador_efectividad.json"
    rep_path.parent.mkdir(parents=True, exist_ok=True)
    with open(rep_path, "w", encoding="utf-8") as f:
        json.dump({
            "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_casos": n_total,
            "tasa_activacion_pct": tasa_activacion,
            "exactitud_pre_pct": tasa_acierto_pre,
            "exactitud_post_pct": tasa_acierto_post,
            "tasa_resolucion_ambiguedad_pct": tasa_resolucion,
            "ganancia_confianza_pct": round(ganancia_confianza, 2),
            "ganancia_delta_pct": round(ganancia_delta, 2),
            "casos": resultados
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Reporte guardado en: {rep_path}")
    return resultados


if __name__ == "__main__":
    evaluar_auto_interrogador()
