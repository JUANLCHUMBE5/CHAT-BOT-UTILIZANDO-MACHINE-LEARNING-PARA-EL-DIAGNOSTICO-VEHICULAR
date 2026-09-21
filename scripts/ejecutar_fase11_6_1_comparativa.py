"""
Script de Evaluación y Comparativa Científica: FASE 11.6.1
Compara ANTES (Fase 11.6) vs DESPUÉS (Fase 11.6.1) sobre los 50 casos del Stress Test
y evalúa el conjunto de 20 casos HOLDOUT inéditos.
"""

import csv
import json
import re
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from src.core.diagnostico.taxonomia_sistemas import obtener_macro_sistema
from src.core.gestor_diagnostico import GestorDiagnostico
from src.infrastructure.container import ServiceContainer

# Palabras clave canónicas de relevancia técnica para RAG (según evaluar_rag_relevancia.py)
KEYWORDS_RELEVANCIA = {
    "misfire": ["misfire", "bujia", "bobina", "p0300", "p0301", "p0302", "p0303", "combustion"],
    "bujia": ["misfire", "bujia", "bobina", "p0300", "p0301", "p0302", "p0303", "combustion"],
    "bomba de gasolina": ["bomba", "combustible", "presion", "tanque", "caudal", "p0087", "aforador"],
    "inyectores": ["inyector", "inyectores", "riel", "combustible", "limpieza", "filtro", "scv"],
    "sensor de oxigeno": ["sensor", "oxigeno", "mezcla", "lambda", "p0171", "p0172", "p0420", "catalizador", "maf", "map"],
    "catalizador": ["catalizador", "p0420", "contrapresion", "escape", "emisiones", "eficiencia"],
    "valvula iac": ["iac", "cuerpo de aceleracion", "ralenti", "marcha minima", "p0505", "p0506", "mariposa", "etcs"],
    "cuerpo de aceleracion": ["iac", "cuerpo de aceleracion", "ralenti", "marcha minima", "p0505", "p0506", "mariposa", "etcs"],
    "culata": ["culata", "empaque", "sobrecalentamiento", "co2", "refrigerante", "burbujas", "mayonesa"],
    "termostato": ["termostato", "motoventilador", "ventilador", "refrigeracion", "p0128", "temperatura", "purga", "radiador"],
    "aceite": ["aceite", "presion de aceite", "bomba de aceite", "taque", "punterias", "anillos", "retenes", "humo azul", "pcv"],
    "embrague": ["embrague", "clutch", "disco", "prensa", "bombin", "esclavo", "patina", "calado"],
    "freno": ["freno", "pastilla", "disco", "alabeo", "dtv", "liquido", "purga", "booster", "servofreno", "caliper"],
    "pastilla": ["freno", "pastilla", "disco", "alabeo", "dtv", "liquido", "purga", "booster", "servofreno", "caliper"],
    "caliper": ["caliper", "freno", "embolo", "traba", "pastilla", "mordaza"],
    "bateria": ["bateria", "arranque", "arrancador", "solenoide", "terminal 50", "clac", "alternador", "carga", "p0562"],
    "arranque": ["arranque", "arrancador", "solenoide", "terminal 50", "clac", "bateria"],
    "alternador": ["alternador", "carga", "diodos", "regulador", "lin", "p0562", "bateria", "voltaje"],
    "caja": ["caja", "transmision", "cvt", "dsg", "dualogic", "atf", "solenoide", "p0841", "p0700", "valvolina", "robotizada"],
    "transmision": ["caja", "transmision", "cvt", "dsg", "dualogic", "atf", "solenoide", "p0841", "p0700", "valvolina", "robotizada"],
    "suspension": ["amortiguador", "buje", "suspension", "llanta", "balanceo", "alineacion", "rebote", "trapecio"],
    "amortiguador": ["amortiguador", "buje", "suspension", "llanta", "balanceo", "alineacion", "rebote", "trapecio"],
    "llantas": ["balanceo", "alineacion", "llanta", "convergencia", "camber", "neumatico", "vibracion", "desbalance"],
    "desbalanceadas": ["balanceo", "alineacion", "llanta", "convergencia", "camber", "neumatico", "vibracion", "desbalance"],
    "abs": ["abs", "velocidad", "rueda", "c0035", "c0040", "c1101", "sensor"],
    "evap": ["evap", "canister", "purga", "valvula", "p0440", "p0442", "p0455", "emisiones"],
    "servofreno": ["servofreno", "booster", "vacio", "pedal duro", "diafragma"],
    "rodamiento": ["rodamiento", "rodaje", "maza", "rueda", "ruleman", "zumbido"],
    "ckp": ["ckp", "cmp", "cigueñal", "arbol de levas", "posicion", "p0335", "p0340"]
}

def es_doc_relevante(titulo: str, contenido: str, falla_esperada: str, dtc_esperado: str = "") -> bool:
    tit_low = titulo.lower()
    cont_low = (contenido or "")[:1500].lower()
    falla_low = falla_esperada.lower()

    if dtc_esperado and dtc_esperado != "N/A" and dtc_esperado.lower() in tit_low:
        return True

    for grupo, palabras in KEYWORDS_RELEVANCIA.items():
        if grupo in falla_low:
            if any(p in tit_low for p in palabras):
                return True
            coincidencias = sum(1 for p in palabras if p in cont_low)
            if coincidencias >= 2:
                return True
    return False

# ============================================================
# 20 CASOS HOLDOUT INÉDITOS (Fase 11.6.1)
# ============================================================
HOLDOUT_20_CASOS = [
    # 4 Técnicos
    {
        "id": "HOLDOUT_01",
        "tipo": "TECNICO",
        "texto": "Presión en riel Common Rail cae a 180 bar bajo demanda plena en dinamómetro. Tensión de alimentación a la bomba de alta presión es 13.8V y no hay fugas externas.",
        "ground_truth": "Bomba de gasolina quemada o con baja presion",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "HOLDOUT_02",
        "tipo": "TECNICO",
        "texto": "Tras prueba en ruta sin aplicar el pedal, la temperatura del disco delantero derecho alcanza 190°C con pirómetro óptico. El émbolo de la mordaza no retrocede al liberar el purgador.",
        "ground_truth": "Caliper de freno trabado o mordaza pegada (piston agarrotado)",
        "macro_esperado": "FRENOS",
        "dtc": "N/A"
    },
    {
        "id": "HOLDOUT_03",
        "tipo": "TECNICO",
        "texto": "Se evidencia fuga profusa de aceite hidráulico en el cartucho del amortiguador posterior izquierdo con pérdida total de amortiguación en compresión y rebote continuo.",
        "ground_truth": "Amortiguadores reventados o bujes de suspension gastados",
        "macro_esperado": "SUSPENSION_CHASIS",
        "dtc": "N/A"
    },
    {
        "id": "HOLDOUT_04",
        "tipo": "TECNICO",
        "texto": "Tensión en bornes de batería cae a 11.8V al encender luces altas y aire acondicionado con motor a 2500 RPM. Osciloscopio registra ondulación de 2.4V pico a pico por diodo abierto.",
        "ground_truth": "Alternador defectuoso o placa de diodos quemada",
        "macro_esperado": "ELECTRICO",
        "dtc": "N/A"
    },

    # 4 Coloquiales
    {
        "id": "HOLDOUT_05",
        "tipo": "COLOQUIAL",
        "texto": "Cuando meto quinta en la autopista y piso a fondo para pasar a otro carro, el motor ruge fuertísimo y la aguja de las revoluciones vuela pero el carro se queda sonso y no aumenta de velocidad.",
        "ground_truth": "Disco de embrague desgastado o patinando",
        "macro_esperado": "TRANSMISION",
        "dtc": "N/A"
    },
    {
        "id": "HOLDOUT_06",
        "tipo": "COLOQUIAL",
        "texto": "En plena cola del peaje el agua del tachito empieza a hervir y botar vapor, pero apenas agarro pista despejada la temperatura baja a la mitad.",
        "ground_truth": "Falla en termostato o motoventilador de radiador",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "HOLDOUT_07",
        "tipo": "COLOQUIAL",
        "texto": "Siento que el timón me zangolotea en las manos únicamente cuando paso de 85 km por hora en pista lisa, pero si voy despacio en la ciudad va derechito y no tiembla.",
        "ground_truth": "Llantas desbalanceadas o desalineadas",
        "macro_esperado": "SUSPENSION_CHASIS",
        "dtc": "N/A"
    },
    {
        "id": "HOLDOUT_08",
        "tipo": "COLOQUIAL",
        "texto": "Cada vez que freno suavemente en las esquinas se escucha un chillido metálico agudo insoportable adelante, como si raspara fierro con fierro.",
        "ground_truth": "Desgaste de pastillas y zapatas de freno",
        "macro_esperado": "FRENOS",
        "dtc": "N/A"
    },

    # 4 Ambiguos
    {
        "id": "HOLDOUT_09",
        "tipo": "AMBIGUO",
        "texto": "El motor tose y tironea de vez en cuando al acelerar suave en frío, pero no se prende ningún testigo en el tablero.",
        "ground_truth": "Falla en bujias o bobinas de encendido (misfire)",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "HOLDOUT_10",
        "tipo": "AMBIGUO",
        "texto": "Hoy en la mañana quise prender y solo sonó un chasquido tenue y se apagaron las luces del tablero por completo.",
        "ground_truth": "Bateria descargada o bornes sulfatados",
        "macro_esperado": "ELECTRICO",
        "dtc": "N/A"
    },
    {
        "id": "HOLDOUT_11",
        "tipo": "AMBIGUO",
        "texto": "Noto que el nivel del refrigerante en el depósito baja cada semana un dedo pero no veo charco en el piso ni humo blanco evidente.",
        "ground_truth": "Fuga en mangueras de refrigerante o radiador picado",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "HOLDOUT_12",
        "tipo": "AMBIGUO",
        "texto": "Se escucha un zumbido sordo adelante que cambia de tono con la velocidad del carro y se atenúa un poco al pisar el pedal de embrague.",
        "ground_truth": "Falta o degradacion de aceite de caja de cambios",
        "macro_esperado": "TRANSMISION",
        "dtc": "N/A"
    },

    # 4 DTC
    {
        "id": "HOLDOUT_13",
        "tipo": "DTC",
        "texto": "Escáner automotriz reporta código de falla P0302 con tironeo persistente bajo carga. Se detectó falla de combustión en el cilindro 2.",
        "ground_truth": "Falla en bujias o bobinas de encendido (misfire)",
        "macro_esperado": "MOTOR",
        "dtc": "P0302"
    },
    {
        "id": "HOLDOUT_14",
        "tipo": "DTC",
        "texto": "Luz Check Engine encendida con código P0171. El ajuste de combustible a corto plazo STFT marca +24% en ralentí pero el motor empareja al acelerar.",
        "ground_truth": "Falla en sensor de oxigeno o mezcla rica",
        "macro_esperado": "MOTOR",
        "dtc": "P0171"
    },
    {
        "id": "HOLDOUT_15",
        "tipo": "DTC",
        "texto": "Código DTC P0420 almacenado en memoria de la ECU. El sensor de oxígeno posterior copia exactamente la oscilación del sensor delantero.",
        "ground_truth": "Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)",
        "macro_esperado": "MOTOR",
        "dtc": "P0420"
    },
    {
        "id": "HOLDOUT_16",
        "tipo": "DTC",
        "texto": "Testigo ABS encendido de forma permanente con código C0035. La señal del captador de velocidad de rueda delantera izquierda marca 0 km/h en línea recta.",
        "ground_truth": "Falla en sensor de velocidad de rueda ABS",
        "macro_esperado": "FRENOS",
        "dtc": "C0035"
    },

    # 4 Diferenciales
    {
        "id": "HOLDOUT_17",
        "tipo": "DIFERENCIAL",
        "texto": "El volante vibra de manera notable entre 90 y 110 km/h en autopista, pero al presionar el pedal del freno el frenado es suave y la vibración no aumenta ni se siente en el pedal.",
        "ground_truth": "Llantas desbalanceadas o desalineadas",
        "macro_esperado": "SUSPENSION_CHASIS",
        "dtc": "N/A"
    },
    {
        "id": "HOLDOUT_18",
        "tipo": "DIFERENCIAL",
        "texto": "Se acaban de colocar 4 bujías de iridio nuevas originales pero el cilindro 3 sigue sin chispa y el motor continúa cojeando en ralentí.",
        "ground_truth": "Falla en bujias o bobinas de encendido (misfire)",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "HOLDOUT_19",
        "tipo": "DIFERENCIAL",
        "texto": "Giro la llave para darle arranque y el motor de arranque gira con fuerza y rapidez normal, pero el motor no enciende porque la bomba en el tanque no zumba.",
        "ground_truth": "Bomba de gasolina quemada o con baja presion",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "HOLDOUT_20",
        "tipo": "DIFERENCIAL",
        "texto": "Circulando a 100 km/h en sexta marcha por la autopista el motor se apagó de golpe al encenderse el testigo de check engine.",
        "ground_truth": "Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
]


def ejecutar_evaluacion_completa():
    print("Iniciando Evaluación Científica Fase 11.6.1...")
    gestor = GestorDiagnostico()
    motor_rag = ServiceContainer.get_motor_rag()
    modelo_ml = ServiceContainer.get_modelo_ml()

    # 1. Cargar los 50 casos del Stress Test original de Fase 11.6
    archivo_csv_50 = BASE_DIR / "docs" / "fase11_6" / "FASE11_6_50_CASOS.csv"
    with open(archivo_csv_50, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        casos_50 = list(reader)

    print(f"Cargados {len(casos_50)} casos originales de Fase 11.6.")

    # Evaluación de los 50 casos ANTES vs DESPUÉS
    resultados_50_after = []
    
    for i, c in enumerate(casos_50):
        cid = c.get("id") or c.get("\ufeffid") or f"STRESS_{i+1:02d}"
        tipo = c["tipo_caso"]
        texto = c["texto_ingresado"]
        gt = c["ground_truth"]
        macro_esp = c["macro_sistema_esperado"]
        dtc_esp = c.get("dtc_codigo", "N/A")

        # Inferencia con pipeline completo de CarBot (Purificación + ML + RAG + Política de Fusión)
        res = gestor.procesar_consulta_texto(texto, diferir_encolado_persistente=True)
        top1_falla = res.diagnostico_ml
        conf1 = res.confianza_ml
        preds = res.predicciones_ml

        top2_falla = preds[1].falla if len(preds) > 1 else "DESCONOCIDO"
        conf2 = preds[1].probabilidad if len(preds) > 1 else 0.0
        top3_falla = preds[2].falla if len(preds) > 2 else "DESCONOCIDO"
        conf3 = preds[2].probabilidad if len(preds) > 2 else 0.0

        macro_pred = obtener_macro_sistema(top1_falla)

        top1_ok = 1 if (top1_falla == gt) else 0
        top3_ok = 1 if (gt in [top1_falla, top2_falla, top3_falla]) else 0
        macro_ok = 1 if (macro_pred == macro_esp) else 0

        tit_rag = res.titulo_manual
        sim_rag = res.similitud_rag

        # Evaluar Hit@K y MRR buscando en candidatos canónicos reordenados
        dtcs_in = [dtc_esp] if dtc_esp and dtc_esp != "N/A" else []
        top_fallas_rag = [{"falla": p.falla, "probabilidad": p.probabilidad} for p in preds]

        from src.infrastructure.rag.query_builder import construir_consulta_hibrida
        from src.infrastructure.rag.relevance_filter import reordenar_candidatos_rag

        consulta_hibrida = construir_consulta_hibrida(
            consulta_usuario=texto,
            macro_sistema=macro_pred,
            top_fallas=top_fallas_rag,
            codigos_dtc=dtcs_in,
        )
        consulta_expandida = motor_rag._expandir_consulta(consulta_hibrida)
        consulta_vec = motor_rag.vectorizador.transform([consulta_expandida]).toarray().astype("float32")
        import faiss
        faiss.normalize_L2(consulta_vec)
        sims_faiss, idxs_faiss = motor_rag.faiss_index.search(consulta_vec, k=15)

        cands = []
        for kidx in range(len(idxs_faiss[0])):
            didx = int(idxs_faiss[0][kidx])
            if 0 <= didx < len(motor_rag.documentos):
                cands.append({
                    "indice": didx,
                    "titulo": motor_rag.titulos[didx],
                    "documento": motor_rag.documentos[didx],
                    "similitud": float(sims_faiss[0][kidx]),
                    "metadatos": motor_rag.metadatos_procedimientos[didx] if didx < len(motor_rag.metadatos_procedimientos) else {}
                })
        cands_reord = reordenar_candidatos_rag(
            cands,
            macro_sistema=macro_pred,
            top_fallas=top_fallas_rag,
            codigos_dtc=dtcs_in,
            confianza_ml=conf1
        )

        rank_hit = None
        for rk, cand in enumerate(cands_reord[:5], start=1):
            if es_doc_relevante(cand["titulo"], cand["documento"], gt, dtc_esp):
                rank_hit = rk
                break

        hit_1 = 1 if (rank_hit == 1) else 0
        hit_3 = 1 if (rank_hit is not None and rank_hit <= 3) else 0
        hit_5 = 1 if (rank_hit is not None and rank_hit <= 5) else 0
        mrr = (1.0 / rank_hit) if rank_hit is not None else 0.0


        # Almacenar fila
        fila = {
            "id": cid,
            "tipo_caso": tipo,
            "texto_ingresado": texto,
            "ground_truth": gt,
            "macro_sistema_esperado": macro_esp,
            "top1_predicho_antes": c["top1_predicho"],
            "confianza_antes": float(c["confianza_top1"]),
            "top1_correcto_antes": int(c["top1_correcto"]),
            "top1_predicho_despues": top1_falla,
            "confianza_despues": round(conf1, 4),
            "top1_correcto_despues": top1_ok,
            "top2_despues": top2_falla,
            "conf2_despues": round(conf2, 4),
            "top3_despues": top3_falla,
            "conf3_despues": round(conf3, 4),
            "top3_correcto_despues": top3_ok,
            "macro_sistema_despues": macro_pred,
            "macro_correcto_despues": macro_ok,
            "dtc_codigo": dtc_esp,
            "rag_titulo_despues": tit_rag,
            "rag_sim_despues": round(sim_rag, 4),
            "hit_1_despues": hit_1,
            "hit_3_despues": hit_3,
            "hit_5_despues": hit_5,
            "mrr_despues": round(mrr, 4)
        }
        resultados_50_after.append(fila)

    # Métricas Globales 50 casos ANTES vs DESPUÉS
    top1_antes = sum(int(c["top1_correcto"]) for c in casos_50)
    top3_antes = sum(int(c["top3_correcto"]) for c in casos_50)
    macro_antes = sum(int(c["macro_correcto"]) for c in casos_50)
    err_75_antes = sum(1 for c in casos_50 if int(c["top1_correcto"]) == 0 and float(c["confianza_top1"]) >= 0.75)

    top1_despues = sum(r["top1_correcto_despues"] for r in resultados_50_after)
    top3_despues = sum(r["top3_correcto_despues"] for r in resultados_50_after)
    macro_despues = sum(r["macro_correcto_despues"] for r in resultados_50_after)
    err_75_despues = sum(1 for r in resultados_50_after if r["top1_correcto_despues"] == 0 and r["confianza_despues"] >= 0.75)

    rag_h1_despues = sum(r["hit_1_despues"] for r in resultados_50_after)
    rag_h3_despues = sum(r["hit_3_despues"] for r in resultados_50_after)
    rag_h5_despues = sum(r["hit_5_despues"] for r in resultados_50_after)
    rag_mrr_despues = sum(r["mrr_despues"] for r in resultados_50_after) / len(resultados_50_after)

    print("\n" + "="*60)
    print("COMPARATIVA 50 CASOS STRESS TEST (FASE 11.6 vs FASE 11.6.1)")
    print("="*60)
    print(f"Top-1 Global:   ANTES {top1_antes}/50 ({top1_antes/50*100:.1f}%) -> DESPUÉS {top1_despues}/50 ({top1_despues/50*100:.1f}%)")
    print(f"Top-3 Global:   ANTES {top3_antes}/50 ({top3_antes/50*100:.1f}%) -> DESPUÉS {top3_despues}/50 ({top3_despues/50*100:.1f}%)")
    print(f"Macro-Sistema:  ANTES {macro_antes}/50 ({macro_antes/50*100:.1f}%) -> DESPUÉS {macro_despues}/50 ({macro_despues/50*100:.1f}%)")
    print(f"Errores >= 75%: ANTES {err_75_antes} -> DESPUÉS {err_75_despues}")
    print(f"RAG Hit@1:      ANTES 40/50 (80.0%) -> DESPUÉS {rag_h1_despues}/50 ({rag_h1_despues/50*100:.1f}%)")
    print(f"RAG Hit@3:      ANTES 43/50 (86.0%) -> DESPUÉS {rag_h3_despues}/50 ({rag_h3_despues/50*100:.1f}%)")
    print(f"RAG Hit@5:      ANTES 43/50 (86.0%) -> DESPUÉS {rag_h5_despues}/50 ({rag_h5_despues/50*100:.1f}%)")
    print(f"RAG MRR:        ANTES 0.827 -> DESPUÉS {rag_mrr_despues:.3f}")

    # Desglose por categoría
    categorias = ["TECNICO", "COLOQUIAL", "AMBIGUO", "DTC", "DIFERENCIAL"]
    metricas_cat = {}
    print("\n--- DESGLOSE POR CATEGORÍA ---")
    for cat in categorias:
        c_ant = [c for c in casos_50 if c["tipo_caso"] == cat]
        c_des = [r for r in resultados_50_after if r["tipo_caso"] == cat]
        t1_a = sum(int(x["top1_correcto"]) for x in c_ant)
        t1_d = sum(x["top1_correcto_despues"] for x in c_des)
        t3_a = sum(int(x["top3_correcto"]) for x in c_ant)
        t3_d = sum(x["top3_correcto_despues"] for x in c_des)
        metricas_cat[cat] = {
            "top1_antes": t1_a, "top1_despues": t1_d,
            "top3_antes": t3_a, "top3_despues": t3_d,
            "total": len(c_ant)
        }
        print(f"{cat:12s}: Top-1 {t1_a}/{len(c_ant)} ({t1_a/len(c_ant)*100:.0f}%) -> {t1_d}/{len(c_des)} ({t1_d/len(c_des)*100:.0f}%) | Top-3 {t3_a} -> {t3_d}")

    # Guardar CSV comparativo de los 50 casos
    out_csv_50 = BASE_DIR / "docs" / "fase11_6" / "FASE11_6_1_50_CASOS_COMPARATIVA.csv"
    with open(out_csv_50, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = list(resultados_50_after[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(resultados_50_after)
    print(f"\nArchivo guardado: {out_csv_50}")

    # ============================================================
    # EVALUACIÓN DE LOS 20 CASOS HOLDOUT
    # ============================================================
    print("\n" + "="*60)
    print("EVALUACIÓN DE 20 CASOS HOLDOUT INÉDITOS")
    print("="*60)
    resultados_holdout = []
    
    for h in HOLDOUT_20_CASOS:
        hid = h["id"]
        tipo = h["tipo"]
        texto = h["texto"]
        gt = h["ground_truth"]
        macro_esp = h["macro_esperado"]
        dtc_esp = h["dtc"]

        res = gestor.procesar_consulta_texto(texto, diferir_encolado_persistente=True)
        top1_falla = res.diagnostico_ml
        conf1 = res.confianza_ml
        preds = res.predicciones_ml

        top2_falla = preds[1].falla if len(preds) > 1 else "DESCONOCIDO"
        conf2 = preds[1].probabilidad if len(preds) > 1 else 0.0
        top3_falla = preds[2].falla if len(preds) > 2 else "DESCONOCIDO"
        conf3 = preds[2].probabilidad if len(preds) > 2 else 0.0

        macro_pred = obtener_macro_sistema(top1_falla)

        top1_ok = 1 if (top1_falla == gt) else 0
        top3_ok = 1 if (gt in [top1_falla, top2_falla, top3_falla]) else 0
        macro_ok = 1 if (macro_pred == macro_esp) else 0

        tit_rag = res.titulo_manual
        sim_rag = res.similitud_rag

        # RAG
        dtcs_in = [dtc_esp] if dtc_esp and dtc_esp != "N/A" else []
        top_fallas_rag = [{"falla": p.falla, "probabilidad": p.probabilidad} for p in preds]

        from src.infrastructure.rag.query_builder import construir_consulta_hibrida
        from src.infrastructure.rag.relevance_filter import reordenar_candidatos_rag

        consulta_hibrida = construir_consulta_hibrida(
            consulta_usuario=texto,
            macro_sistema=macro_pred,
            top_fallas=top_fallas_rag,
            codigos_dtc=dtcs_in,
        )
        consulta_expandida = motor_rag._expandir_consulta(consulta_hibrida)
        consulta_vec = motor_rag.vectorizador.transform([consulta_expandida]).toarray().astype("float32")
        import faiss
        faiss.normalize_L2(consulta_vec)
        sims_faiss, idxs_faiss = motor_rag.faiss_index.search(consulta_vec, k=15)

        cands = []
        for kidx in range(len(idxs_faiss[0])):
            didx = int(idxs_faiss[0][kidx])
            if 0 <= didx < len(motor_rag.documentos):
                cands.append({
                    "indice": didx,
                    "titulo": motor_rag.titulos[didx],
                    "documento": motor_rag.documentos[didx],
                    "similitud": float(sims_faiss[0][kidx]),
                    "metadatos": motor_rag.metadatos_procedimientos[didx] if didx < len(motor_rag.metadatos_procedimientos) else {}
                })
        cands_reord = reordenar_candidatos_rag(
            cands,
            macro_sistema=macro_pred,
            top_fallas=top_fallas_rag,
            codigos_dtc=dtcs_in,
            confianza_ml=conf1
        )

        rank_hit = None
        for rk, cand in enumerate(cands_reord[:5], start=1):
            if es_doc_relevante(cand["titulo"], cand["documento"], gt, dtc_esp):
                rank_hit = rk
                break

        hit_1 = 1 if (rank_hit == 1) else 0
        hit_3 = 1 if (rank_hit is not None and rank_hit <= 3) else 0

        res_h = {
            "id": hid,
            "tipo_caso": tipo,
            "texto_ingresado": texto,
            "ground_truth": gt,
            "macro_sistema_esperado": macro_esp,
            "top1_predicho": top1_falla,
            "confianza_top1": round(conf1, 4),
            "top2_predicho": top2_falla,
            "confianza_top2": round(conf2, 4),
            "top3_predicho": top3_falla,
            "confianza_top3": round(conf3, 4),
            "macro_sistema_predicho": macro_pred,
            "top1_correcto": top1_ok,
            "top3_correcto": top3_ok,
            "macro_correcto": macro_ok,
            "dtc_codigo": dtc_esp,
            "rag_titulo": tit_rag,
            "rag_similitud": round(sim_rag, 4),
            "hit_1_rag": hit_1,
            "hit_3_rag": hit_3
        }
        resultados_holdout.append(res_h)

    h_top1 = sum(r["top1_correcto"] for r in resultados_holdout)
    h_top3 = sum(r["top3_correcto"] for r in resultados_holdout)
    h_macro = sum(r["macro_correcto"] for r in resultados_holdout)
    h_err75 = sum(1 for r in resultados_holdout if r["top1_correcto"] == 0 and r["confianza_top1"] >= 0.75)
    h_rag1 = sum(r["hit_1_rag"] for r in resultados_holdout)
    h_rag3 = sum(r["hit_3_rag"] for r in resultados_holdout)

    print(f"Holdout Top-1:   {h_top1}/20 ({h_top1/20*100:.1f}%)")
    print(f"Holdout Top-3:   {h_top3}/20 ({h_top3/20*100:.1f}%)")
    print(f"Holdout Macro:   {h_macro}/20 ({h_macro/20*100:.1f}%)")
    print(f"Holdout Err>=75: {h_err75}")
    print(f"Holdout RAG H@1: {h_rag1}/20 ({h_rag1/20*100:.1f}%)")
    print(f"Holdout RAG H@3: {h_rag3}/20 ({h_rag3/20*100:.1f}%)")

    # Guardar CSV de los 20 holdout
    out_csv_holdout = BASE_DIR / "docs" / "fase11_6" / "FASE11_6_1_20_HOLDOUT.csv"
    with open(out_csv_holdout, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = list(resultados_holdout[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(resultados_holdout)
    print(f"Archivo guardado: {out_csv_holdout}")

    # Guardar JSON con todas las métricas consolidadas
    metricas_completas = {
        "fecha": "2026-09-19",
        "lote": "FASE_11_6_1",
        "50_casos": {
            "antes": {
                "top1": top1_antes, "top1_pct": round(top1_antes/50*100, 2),
                "top3": top3_antes, "top3_pct": round(top3_antes/50*100, 2),
                "macro": macro_antes, "macro_pct": round(macro_antes/50*100, 2),
                "errores_alta_confianza_75": err_75_antes,
                "rag_hit1_pct": 80.0, "rag_hit3_pct": 86.0, "rag_hit5_pct": 86.0, "rag_mrr": 0.827
            },
            "despues": {
                "top1": top1_despues, "top1_pct": round(top1_despues/50*100, 2),
                "top3": top3_despues, "top3_pct": round(top3_despues/50*100, 2),
                "macro": macro_despues, "macro_pct": round(macro_despues/50*100, 2),
                "errores_alta_confianza_75": err_75_despues,
                "rag_hit1": rag_h1_despues, "rag_hit1_pct": round(rag_h1_despues/50*100, 2),
                "rag_hit3": rag_h3_despues, "rag_hit3_pct": round(rag_h3_despues/50*100, 2),
                "rag_hit5": rag_h5_despues, "rag_hit5_pct": round(rag_h5_despues/50*100, 2),
                "rag_mrr": round(rag_mrr_despues, 3)
            },
            "por_categoria": metricas_cat
        },
        "holdout_20_casos": {
            "total": 20,
            "top1": h_top1, "top1_pct": round(h_top1/20*100, 2),
            "top3": h_top3, "top3_pct": round(h_top3/20*100, 2),
            "macro": h_macro, "macro_pct": round(h_macro/20*100, 2),
            "errores_alta_confianza_75": h_err75,
            "rag_hit1": h_rag1, "rag_hit1_pct": round(h_rag1/20*100, 2),
            "rag_hit3": h_rag3, "rag_hit3_pct": round(h_rag3/20*100, 2)
        }
    }
    out_json = BASE_DIR / "docs" / "fase11_6" / "FASE11_6_1_REPORTE_COMPARATIVO.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(metricas_completas, f, indent=2, ensure_ascii=False)
    print(f"Resumen JSON guardado: {out_json}")


if __name__ == "__main__":
    ejecutar_evaluacion_completa()
