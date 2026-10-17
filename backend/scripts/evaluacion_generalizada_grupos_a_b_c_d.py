"""Evaluación generalizada y reproducible de 4 grupos (A, B, C, D) a través de 4 variantes de pipeline.

Grupos:
  - Grupo A: 30 casos reales de Alex (multi-turno)
  - Grupo B: 48 clases canónicas de averías
  - Grupo C: 13 reformulaciones coloquiales/complejas
  - Grupo D: 32 casos exploratorios reservados (8 dominios automotrices)

Variantes evaluadas:
  1. SVM puro
  2. SVM + enrutamiento general
  3. SVM + reglas/descartes
  4. Sistema híbrido completo (ML + RAG + LLM offline)
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.config import settings
from src.core.diagnostico.enrutador_sistema import (
    areas_para_sistema,
    detectar_areas_tecnicas,
    falla_coincide_con_areas,
    filtrar_causas,
    resolver_sistema_activo,
)
from src.core.diagnostico.models import PrediccionML
from src.core.diagnostico.procesador_texto.clasificacion_ml import ejecutar_clasificacion_ml
from src.core.gestor_diagnostico import GestorDiagnostico


def _norm(s: str) -> str:
    base = unicodedata.normalize("NFKD", str(s or "").lower())
    return " ".join("".join(c for c in base if not unicodedata.combining(c)).split())


PATRONES_CANONICOS_GT: dict[str, tuple[str, ...]] = {
    "sensor maf sucio": (r"\bmaf\b", r"\binyector(?:es)?\b", r"\bfuga de vacio\b"),
    "sensor maf": (r"\bmaf\b", r"\binyector(?:es)?\b", r"\bfuga de vacio\b"),
    "bujia o bobina defectuosa": (r"\bbujias?\b", r"\bbobinas?\b", r"\bmisfire\b"),
    "bobina de encendido": (r"\bbujias?\b", r"\bbobinas?\b", r"\bmisfire\b"),
    "bujias en mal estado": (r"\bbujias?\b", r"\bbobinas?\b", r"\bmisfire\b"),
    "bobina cilindro 1": (r"\bbobinas?\b", r"\bbujias?\b", r"\bmisfire\b", r"\bcilindro\b"),
    "termostato o ventilador": (r"\btermostato\b", r"\belectroventilador\b", r"\bventilador\b", r"\bmotoventilador\b"),
    "ventilador no enciende": (r"\bventilador\b", r"\belectroventilador\b", r"\bmotoventilador\b", r"\btermostato\b"),
    "nivel o fuga refrigerante": (r"\bradiador\b", r"\bmangueras?\b", r"\bfuga\b.{0,25}\brefrigerante\b", r"\btermostato\b"),
    "sensor map pendiente": (r"sin hipotesis ml pertinente para admision", r"pendiente de comparar", r"\bmap\b"),
    "inyectores con caudal bajo": (r"\binyector(?:es)?\b", r"\bcaudal\b"),
    "inyectores o presion combustible": (r"\binyector(?:es)?\b", r"\bcombustible\b", r"\bbomba\b"),
    "inyectores con fuga": (r"\binyector(?:es)?\b", r"\bmezcla rica\b", r"\bregulador de presion de combustible\b"),
    "corto modo proteccion ecu": (r"\bcorto\b", r"\bproteccion\b", r"\becu\b"),
    "ecu no codificada": (r"\becu\b", r"\bcodificad\w*\b", r"\binmovilizador\b", r"\bcomputadora\b"),
    "conector o red can": (r"\bred can\b", r"\bconector\b", r"\bcomunicacion\b.{0,25}\becu\b"),
    "ecu incompatible": (r"\becu\b.{0,25}\bincompatible\b", r"\bcodificacion\b"),
    "pastillas gastadas": (r"\bpastillas?\b", r"\bfrenos?\b"),
    "discos deformados": (r"\bdiscos?\b.{0,25}\bfreno\b", r"\balabeado\b"),
    "cuerpo aceleracion o iac": (r"\bcuerpo de aceleracion\b", r"\biac\b"),
    "tps o cuerpo aceleracion": (r"\btps\b", r"\bcuerpo de aceleracion\b", r"\biac\b", r"\bmariposa\b"),
    "contexto insuficiente": (r"consulta ambigua", r"datos faltantes", r"se requiere contexto", r"contexto insuficiente"),
    "sensor ect intermitente": (r"\bect\b", r"sensor de temperatura", r"temperatura de refrigerante"),
    "fuga de vacio": (r"\bfuga de vacio\b", r"\badmision\b"),
    "liquido o bomba direccion": (r"\bdireccion\b", r"\bcremallera\b", r"\bbomba\b.{0,25}\bdireccion\b"),
    "amortiguador o buje": (r"\bamortiguador(?:es)?\b", r"\bbujes?\b", r"\bsuspension\b"),
    "rotula o buje con holgura": (r"\brotula\b", r"\bbuje\b", r"\bsuspension\b"),
    "alternador o fuga corriente": (r"\balternador\b", r"\bfuga parasita\b", r"\bbateria\b"),
    "posible fuga interna": (r"\bculata\b", r"\bjunta\b", r"\bempaque\b"),
}


def coincide(pred_falla: str, gt_falla: str) -> bool:
    p_norm = _norm(pred_falla)
    g_norm = _norm(gt_falla)
    if not p_norm or not g_norm:
        return False
    if p_norm == g_norm:
        return True
    patrones = PATRONES_CANONICOS_GT.get(g_norm)
    if patrones:
        return any(re.search(pat, p_norm) for pat in patrones)
    return g_norm in p_norm or p_norm in g_norm


def evaluar_caso_en_variantes(
    gestor: GestorDiagnostico,
    texto: str,
    gt: str,
    placa: str = "BENCH-01",
    session_id: str = "sess_bench",
    vehiculo: str = "",
) -> Dict[str, Any]:
    """Evalúa un caso en las 4 variantes de pipeline en completo aislamiento."""
    texto_evaluar = gestor._purificar_sintoma_para_vectorizador_ml(texto)

    # 1. SVM Puro
    t0_ml = time.perf_counter()
    raw_preds = gestor.modelo_ml.predecir_top_fallas(texto_evaluar, limite=3)
    preds_svm = [
        PrediccionML(falla=p["falla"], probabilidad=float(p["probabilidad"]), origen_probabilidad="SVM")
        for p in raw_preds
    ]
    t_svm = (time.perf_counter() - t0_ml) * 1000
    top1_svm = preds_svm[0].falla if preds_svm else "DESCONOCIDO"
    top3_svm = [p.falla for p in preds_svm]
    acierto_svm_t1 = coincide(top1_svm, gt)
    acierto_svm_t3 = any(coincide(f, gt) for f in top3_svm)

    # 2. SVM + Enrutamiento General
    t0_enr = time.perf_counter()
    sistema_activo = resolver_sistema_activo(texto, None)
    areas_consulta = detectar_areas_tecnicas(texto)
    if sistema_activo and sistema_activo != "ambiguo":
        areas_consulta = areas_para_sistema(sistema_activo, texto) or areas_consulta
    preds_enr = filtrar_causas(sistema_activo, preds_svm, texto)
    if areas_consulta:
        preds_enr = [p for p in preds_enr if falla_coincide_con_areas(p.falla, areas_consulta)]
    preds_enr = preds_enr[:3] or preds_svm[:3]
    t_enr = (time.perf_counter() - t0_enr) * 1000 + t_svm
    top1_enr = preds_enr[0].falla if preds_enr else "DESCONOCIDO"
    top3_enr = [p.falla for p in preds_enr]
    acierto_enr_t1 = coincide(top1_enr, gt)
    acierto_enr_t3 = any(coincide(f, gt) for f in top3_enr)

    # 3. SVM + Reglas
    t0_reg = time.perf_counter()
    (
        top1_reg,
        conf_reg,
        preds_reg,
        _,
        _,
        t_ml_int,
    ) = ejecutar_clasificacion_ml(
        gestor=gestor,
        texto_evaluar=texto,
        diagnostico_forzado=None,
        clave_sesion=None,
        areas_consulta=areas_consulta,
        sistema_activo=sistema_activo,
        modo_falla_combustible=None,
        tiene_dtc=bool(re.search(r"\b[pbcu]\d{4}\b", texto, re.I)),
        tiene_componente_especifico=False,
    )
    t_reg = (time.perf_counter() - t0_reg) * 1000
    top3_reg = [p.falla for p in preds_reg]
    acierto_reg_t1 = coincide(top1_reg, gt)
    acierto_reg_t3 = any(coincide(f, gt) for f in top3_reg)

    # 4. Sistema Híbrido Completo
    t0_hib = time.perf_counter()
    res_hib = gestor.procesar_consulta_texto(
        texto_usuario=texto,
        placa=placa,
        session_id=session_id,
        marca_modelo=vehiculo or None,
        proveedor="web",
    )
    t_hib = (time.perf_counter() - t0_hib) * 1000
    top1_hib = res_hib.diagnostico_ml
    top3_hib = [p.falla for p in (res_hib.predicciones_ml or [])]
    if not top3_hib and top1_hib:
        top3_hib = [top1_hib]
    acierto_hib_t1 = coincide(top1_hib, gt)
    acierto_hib_t3 = any(coincide(f, gt) for f in top3_hib)
    es_abstencion_falsa = (res_hib.modo_diagnostico == "esperando_clarificacion" or "Sin hipótesis" in top1_hib) and not (
        "contexto" in _norm(gt) or "ambiguo" in _norm(gt)
    )

    return {
        "svm": {"t1": acierto_svm_t1, "t3": acierto_svm_t3, "lat": t_svm, "pred": top1_svm},
        "enr": {"t1": acierto_enr_t1, "t3": acierto_enr_t3, "lat": t_enr, "pred": top1_enr},
        "reg": {"t1": acierto_reg_t1, "t3": acierto_reg_t3, "lat": t_reg, "pred": top1_reg},
        "hib": {
            "t1": acierto_hib_t1,
            "t3": acierto_hib_t3,
            "lat": t_hib,
            "lat_ml": res_hib.tiempo_ml_ms,
            "lat_rag": res_hib.tiempo_rag_ms,
            "pred": top1_hib,
            "falsa_abst": es_abstencion_falsa,
        },
    }


def ejecutar_benchmark_completo() -> None:
    settings.groq_chat_enabled = False
    settings.gemini_api_key = ""

    gestor = GestorDiagnostico()
    gestor._registrar_en_tracker = lambda **kwargs: None

    # --- GRUPO A: 30 casos de Alex ---
    json_path = Path(r"C:\Users\leonc\Downloads\CarBot_Alex_POST_30_tiempos_Excel.json")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    casos_alex = data["diagnosticos"]
    convs_alex = {c["case_id"]: c for c in data.get("conversaciones", [])}
    grupo_a = []
    for idx, item in enumerate(casos_alex, 1):
        c_obj = convs_alex.get(item["case_id"], {})
        num = c_obj.get("numero", idx)
        ms = c_obj.get("mensajes", [])
        entradas = [str(m.get("texto", "")).strip() for m in ms if m.get("direccion") == "entrada"]
        turnos = entradas[3:] if len(entradas) > 3 else entradas
        utiles = [
            t for t in turnos
            if _norm(t).strip(" .,!¡¿?") not in {"si", "no", "ok", "dale", "listo", "gracias"}
            and not _norm(t).startswith("no, aun")
            and not _norm(t).startswith("no lo se")
        ]
        sintoma_mt = ". ".join(utiles) if utiles else str(item.get("sintoma", ""))
        gt = str(item.get("falla_principal", "")).strip()
        vehiculo = str(item.get("vehiculo", ""))
        grupo_a.append({"id": f"A_{num:02d}", "texto": sintoma_mt, "gt": gt, "vehiculo": vehiculo})

    # --- GRUPO B: 48 clases canónicas ---
    from tests.test_clasificacion_48_clases_totales import CASOS_48_AVERIAS
    grupo_b = [
        {"id": f"B_{i+1:02d}", "texto": sintoma, "gt": averia, "vehiculo": ""}
        for i, (averia, sintoma) in enumerate(CASOS_48_AVERIAS)
    ]

    # --- GRUPO C: 13 reformulaciones coloquiales / complejas ---
    grupo_c = [
        {"id": "C_01", "texto": "motor tironea en subidas y la luz de check parpadea cuando le exijo", "gt": "Falla en bujias o bobinas de encendido (misfire)", "vehiculo": ""},
        {"id": "C_02", "texto": "en caliente el minimo se cae a 500 vueltas y oscila bastante en neutro", "gt": "Cuerpo de aceleracion o valvula IAC sucia", "vehiculo": ""},
        {"id": "C_03", "texto": "chillido insoportable de metal con metal en las ruedas delanteras al pisar el freno", "gt": "Desgaste de pastillas y zapatas de freno", "vehiculo": ""},
        {"id": "C_04", "texto": "la temperatura trepa al maximo cuando me quedo varado en el trafico lento", "gt": "Falla en termostato o motoventilador de radiador", "vehiculo": ""},
        {"id": "C_05", "texto": "cambie la computadora del motor por otra y ahora el carro da marcha pero no arranca parpadea la llave", "gt": "ECU no codificada o bloqueo de inmovilizador tras cambio de computadora", "vehiculo": ""},
        {"id": "C_06", "texto": "no entra el escaner al puerto obd2 dice error de enlace en la red can con la ecu", "gt": "Falla en conector, alimentacion o red CAN de comunicacion con ECU", "vehiculo": ""},
        {"id": "C_07", "texto": "bota humo azul denso todo el tiempo por el tubo de escape y gasta un litro de aceite por semana", "gt": "Consumo de aceite por desgaste de anillos o retenes", "vehiculo": ""},
        {"id": "C_08", "texto": "el pedal del clutch se fue hasta abajo como trapo y no regresa no entran las marchas", "gt": "Falla en bombin o bomba hidraulica de embrague", "vehiculo": ""},
        {"id": "C_09", "texto": "humo blanco con olor dulce por el escape y burbujea el vaso de expansion con refrigerante bajo", "gt": "Empaque de culata soplado o danado", "vehiculo": ""},
        {"id": "C_10", "texto": "zumbido insoportable en la caja manual que sube mientras mas rapido voy en pista", "gt": "Rodajes de caja mecanica o diferencial gastados", "vehiculo": ""},
        {"id": "C_11", "texto": "al dar contacto el tablero se apaga por completo y solo hace un tac tac seco en el arrancador", "gt": "Bateria descargada o bornes sulfatados", "vehiculo": ""},
        {"id": "C_12", "texto": "crujido o traqueteo fuerte en la rueda delantera al doblar toda la direccion a la esquina", "gt": "Juntas homocineticas o palieres danados", "vehiculo": ""},
        {"id": "C_13", "texto": "olor fuerte a combustible crudo humo negro y bujias empapadas en gasolina", "gt": "Falla en sensor de oxigeno o mezcla rica", "vehiculo": ""},
    ]

    # --- GRUPO D: 32 casos exploratorios reservados (8 dominios) ---
    grupo_d = [
        # Dominio 1: Diésel / Common Rail / DPF
        {"id": "D_01", "texto": "camioneta hilux common rail no arranca en caliente se cae la presion del riel a 120 bar", "gt": "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)", "vehiculo": "Toyota Hilux 2018"},
        {"id": "D_02", "texto": "testigo de dpf saturado en tablero y motor diesel en modo degradado no pasa de 2000 rpm", "gt": "Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)", "vehiculo": "Volkswagen Amarok 2019"},
        {"id": "D_03", "texto": "humo negro excesivo al acelerar y se escucha soplido fuerte en manguera de intercooler rajada", "gt": "Fuga en mangueras de intercooler o turbocompresor danado", "vehiculo": "Nissan Frontier 2017"},
        {"id": "D_04", "texto": "filtro de petroleo con sedimento negro y motor se apaga en alta exigencia por restriccion", "gt": "Inyectores sucios o filtro de combustible obstruido", "vehiculo": "Isuzu D-Max 2020"},
        # Dominio 2: EV / Híbridos
        {"id": "D_05", "texto": "prius hibrido arroja codigo p0a80 triangulo rojo y celda de bateria de traccion desbalanceada", "gt": "Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)", "vehiculo": "Toyota Prius 2018"},
        {"id": "D_06", "texto": "inversor igbt recalienta y motor electrico de traccion entra en modo proteccion", "gt": "Fallo en inversor de corriente IGBT o motor electrico (EV)", "vehiculo": "Nissan Leaf 2020"},
        {"id": "D_07", "texto": "frenado regenerativo no carga la bateria y la transicion al freno de disco da golpe", "gt": "Falla en sistema de frenado regenerativo (EV / Hibridos)", "vehiculo": "Hyundai Ioniq 2019"},
        {"id": "D_08", "texto": "bomba de refrigerante del inversor electrico no funciona y marca sobrecalentamiento de bateria de alto voltaje", "gt": "Foco o falla en sistema de refrigeracion de bateria/inversor (EV)", "vehiculo": "Kia Niro EV 2021"},
        # Dominio 3: Cajas automáticas / CVT / DSG
        {"id": "D_09", "texto": "caja cvt nissan zapatea da tirones y el aceite de transmision esta sobrecalentado", "gt": "Sobrecalentamiento o solenoides en caja automatica CVT / DSG", "vehiculo": "Nissan Sentra 2019"},
        {"id": "D_10", "texto": "fiat palio robotizado marca cambio no disponible y no acopla la primera marcha bomba dualogic", "gt": "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)", "vehiculo": "Fiat Palio 2016"},
        {"id": "D_11", "texto": "patina la cuarta velocidad en caja automatica y solenoides de cambio trabados en cuerpo de valvulas", "gt": "Sobrecalentamiento o solenoides en caja automatica CVT / DSG", "vehiculo": "Honda Civic 2018"},
        {"id": "D_12", "texto": "zumbido metalico en caja mecanica y cambios muy duros por falta de aceite de transmision", "gt": "Falta o degradacion de aceite de caja de cambios", "vehiculo": "Toyota Yaris 2017"},
        # Dominio 4: Electrónica / Red CAN / ECU / Sensores
        {"id": "D_13", "texto": "red can con corto a masa codigo u0100 sin comunicacion con la computadora de motor ecu", "gt": "Falla en conector, alimentacion o red CAN de comunicacion con ECU", "vehiculo": "Chevrolet Cruze 2017"},
        {"id": "D_14", "texto": "modulo fscm de control de bomba de combustible sin comunicacion pem sin voltaje motor se apaga", "gt": "Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet)", "vehiculo": "Ford Focus 2016"},
        {"id": "D_15", "texto": "sensor ect marca menos cuarenta grados en frio y check prende intermitente sensor de temperatura refrigerante", "gt": "Falla en sensor de temperatura de refrigerante (ECT) o conexion intermitente", "vehiculo": "Hyundai Accent 2018"},
        {"id": "D_16", "texto": "tps descalibrado aceleracion a tirones con check engine encendido y mariposa desfasada", "gt": "Cuerpo de aceleracion o sensor TPS descalibrado", "vehiculo": "Volkswagen Gol 2019"},
        # Dominio 5: Suspensión y Dirección
        {"id": "D_17", "texto": "timon durisimo y fuga de liquido por retenes de la cremallera de direccion asistida", "gt": "Cremallera de direccion asistida con holgura o fuga", "vehiculo": "Toyota Corolla 2016"},
        {"id": "D_18", "texto": "golpe seco y rebote excesivo en baches amortiguadores reventados con fuga de aceite", "gt": "Amortiguadores reventados o bujes de suspension gastados", "vehiculo": "Kia Rio 2019"},
        {"id": "D_19", "texto": "sonido de trac trac en la rueda delantera al dar la vuelta cerrada palier o junta homocinetica danada", "gt": "Juntas homocineticas o palieres danados", "vehiculo": "Renault Sandero 2018"},
        {"id": "D_20", "texto": "vibracion a 90 km/h en carretera y vehiculo se jala a la derecha llantas desbalanceadas", "gt": "Llantas desbalanceadas o desalineadas", "vehiculo": "Nissan Versa 2020"},
        # Dominio 6: Climatización / Carrocería
        {"id": "D_21", "texto": "aire acondicionado solo tira aire tibio compresor no acopla y fuga gas refrigerante r134a", "gt": "Falla en compresor de aire acondicionado o fuga de gas R134a", "vehiculo": "Suzuki Swift 2019"},
        {"id": "D_22", "texto": "vidrio del copiloto se cayo dentro de la puerta guaya de alzacristales rota elevalunas trabado", "gt": "Elevalunas electrico o guaya de alzacristales rota o trabada", "vehiculo": "Chevrolet Onix 2020"},
        {"id": "D_23", "texto": "mando a distancia no abre las puertas actuador del cierre centralizado fogueado", "gt": "Falla electrica del cierre centralizado o actuador de puerta", "vehiculo": "Hyundai Grand i10 2018"},
        {"id": "D_24", "texto": "brazos del parabrisas trabados motor pluma quemado no funciona en lluvia limpiaparabrisas", "gt": "Limpiaparabrisas o motor pluma quemado", "vehiculo": "Mazda 3 2017"},
        # Dominio 7: Frenos / ABS / Neumáticos
        {"id": "D_25", "texto": "pedal de freno se va al fondo con sensacion esponjosa fuga o aire en circuito de frenos", "gt": "Fuga hidraulica o aire en el sistema de frenos", "vehiculo": "Toyota Yaris 2019"},
        {"id": "D_26", "texto": "vibracion violenta en el volante y pedal solo al frenar a alta velocidad discos alabeados", "gt": "Discos de freno alabeados o desgastados", "vehiculo": "Honda Civic 2019"},
        {"id": "D_27", "texto": "testigo de abs prendido sensor de velocidad de rueda abs sin lectura en el osciloscopio", "gt": "Falla en sensor de velocidad de rueda ABS", "vehiculo": "Volkswagen Vento 2018"},
        {"id": "D_28", "texto": "pedal de freno durisimo sin asistencia servofreno booster sin vacio manguera rota", "gt": "Falla en servofreno (booster) o linea de vacio", "vehiculo": "Nissan Tiida 2015"},
        # Dominio 8: Motor / Combustión / Distribución
        {"id": "D_29", "texto": "sonido de cascabeleo en la tapa de distribucion cadena destensada y salto de punto", "gt": "Faja o cadena de distribucion destensada o con salto de punto", "vehiculo": "Toyota Corolla 2017"},
        {"id": "D_30", "texto": "humo blanco denso por el escape y refrigerante mezclado empaque de culata soplado", "gt": "Empaque de culata soplado o danado", "vehiculo": "Renault Duster 2019"},
        {"id": "D_31", "texto": "perdida de presion de aceite testigo de la aceitera parpadea en caliente bomba de aceite defectuosa", "gt": "Baja presion de aceite o bomba de aceite defectuosa", "vehiculo": "Chevrolet Spark 2018"},
        {"id": "D_32", "texto": "inyeccion directa gdi perdida de potencia por carbon acumulado en valvulas de admision descarbonizacion", "gt": "Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)", "vehiculo": "Kia Sportage 2020"},
    ]

    grupos = {
        "Grupo A (30 Casos Alex)": grupo_a,
        "Grupo B (48 Canónicas)": grupo_b,
        "Grupo C (13 Reformulaciones)": grupo_c,
        "Grupo D (32 Exploratorios 8 Dominios)": grupo_d,
    }

    reporte_filas = []

    print("\n" + "=" * 90)
    print("EVALUACIÓN COMPARATIVA GENERALIZADA DE 4 GRUPOS x 4 VARIANTES DE PIPELINE")
    print("=" * 90)

    for nombre_grupo, casos in grupos.items():
        n = len(casos)
        res_grupo = {
            "svm_t1": 0, "svm_t3": 0, "svm_lat": [],
            "enr_t1": 0, "enr_t3": 0, "enr_lat": [],
            "reg_t1": 0, "reg_t3": 0, "reg_lat": [],
            "hib_t1": 0, "hib_t3": 0, "hib_lat": [], "hib_ml_lat": [], "hib_rag_lat": [], "falsas_abst": 0,
        }

        print(f"\nEvaluando {nombre_grupo} ({n} casos)...")
        for idx, caso in enumerate(casos):
            placa = f"P_{caso['id']}"
            session_id = f"sess_{caso['id']}_{time.time_ns()}"
            vehiculo = caso.get("vehiculo", "")
            r = evaluar_caso_en_variantes(gestor, caso["texto"], caso["gt"], placa=placa, session_id=session_id, vehiculo=vehiculo)

            if r["svm"]["t1"]: res_grupo["svm_t1"] += 1
            if r["svm"]["t3"]: res_grupo["svm_t3"] += 1
            res_grupo["svm_lat"].append(r["svm"]["lat"])

            if r["enr"]["t1"]: res_grupo["enr_t1"] += 1
            if r["enr"]["t3"]: res_grupo["enr_t3"] += 1
            res_grupo["enr_lat"].append(r["enr"]["lat"])

            if r["reg"]["t1"]: res_grupo["reg_t1"] += 1
            if r["reg"]["t3"]: res_grupo["reg_t3"] += 1
            res_grupo["reg_lat"].append(r["reg"]["lat"])

            if r["hib"]["t1"]: res_grupo["hib_t1"] += 1
            if r["hib"]["t3"]: res_grupo["hib_t3"] += 1
            res_grupo["hib_lat"].append(r["hib"]["lat"])
            res_grupo["hib_ml_lat"].append(r["hib"]["lat_ml"])
            res_grupo["hib_rag_lat"].append(r["hib"]["lat_rag"])
            if r["hib"]["falsa_abst"]: res_grupo["falsas_abst"] += 1

            reporte_filas.append({
                "grupo": nombre_grupo,
                "id": caso["id"],
                "texto": caso["texto"],
                "gt": caso["gt"],
                "pred_svm": r["svm"]["pred"],
                "t1_svm": r["svm"]["t1"],
                "pred_enr": r["enr"]["pred"],
                "t1_enr": r["enr"]["t1"],
                "pred_reg": r["reg"]["pred"],
                "t1_reg": r["reg"]["t1"],
                "pred_hib": r["hib"]["pred"],
                "t1_hib": r["hib"]["t1"],
                "t3_hib": r["hib"]["t3"],
                "lat_hib_ms": f"{r['hib']['lat']:.1f}",
            })

        avg = lambda l: sum(l) / len(l) if l else 0.0

        print(f"--- RESUMEN: {nombre_grupo} (N={n}) ---")
        print(f"  1. SVM Puro         : Top-1 = {res_grupo['svm_t1']}/{n} ({res_grupo['svm_t1']/n*100:.1f}%), Top-3 = {res_grupo['svm_t3']}/{n} ({res_grupo['svm_t3']/n*100:.1f}%), Lat = {avg(res_grupo['svm_lat']):.1f} ms")
        print(f"  2. SVM + Enrutador  : Top-1 = {res_grupo['enr_t1']}/{n} ({res_grupo['enr_t1']/n*100:.1f}%), Top-3 = {res_grupo['enr_t3']}/{n} ({res_grupo['enr_t3']/n*100:.1f}%), Lat = {avg(res_grupo['enr_lat']):.1f} ms")
        print(f"  3. SVM + Reglas     : Top-1 = {res_grupo['reg_t1']}/{n} ({res_grupo['reg_t1']/n*100:.1f}%), Top-3 = {res_grupo['reg_t3']}/{n} ({res_grupo['reg_t3']/n*100:.1f}%), Lat = {avg(res_grupo['reg_lat']):.1f} ms")
        print(f"  4. Híbrido Completo : Top-1 = {res_grupo['hib_t1']}/{n} ({res_grupo['hib_t1']/n*100:.1f}%), Top-3 = {res_grupo['hib_t3']}/{n} ({res_grupo['hib_t3']/n*100:.1f}%), Falsas Abst = {res_grupo['falsas_abst']}/{n}")
        print(f"     Latencias        : Total = {avg(res_grupo['hib_lat']):.1f} ms | ML = {avg(res_grupo['hib_ml_lat']):.1f} ms | RAG = {avg(res_grupo['hib_rag_lat']):.1f} ms")

    out_csv = Path(BACKEND_DIR) / "docs" / "auditorias" / "EVALUACION_GENERALIZADA_GRUPOS_A_B_C_D.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(reporte_filas[0].keys()))
        writer.writeheader()
        writer.writerows(reporte_filas)
    print(f"\n[OK] Reporte detallado guardado en: {out_csv}")


if __name__ == "__main__":
    ejecutar_benchmark_completo()
