"""Fase 4: Análisis exhaustivo del clasificador Linear SVM sobre los 30 casos de la auditoría profunda."""

import json
from pathlib import Path

import joblib

from src.config import settings

try:
    from tests.auditoria_profunda.casos_01_a_10 import CASOS_01_A_10
    from tests.auditoria_profunda.casos_11_a_20 import CASOS_11_A_20
    from tests.auditoria_profunda.casos_21_a_30 import CASOS_21_A_30
except ImportError:
    from scratch.auditoria_profunda.casos_01_a_10 import CASOS_01_A_10
    from scratch.auditoria_profunda.casos_11_a_20 import CASOS_11_A_20
    from scratch.auditoria_profunda.casos_21_a_30 import CASOS_21_A_30

# Cargar modelo y clases
modelo = joblib.load(settings.paths.model_pkl)
vectorizador = joblib.load(settings.paths.vectorizer_pkl)
clases_entrenadas = list(modelo.classes_)

todos_los_casos = CASOS_01_A_10 + CASOS_11_A_20 + CASOS_21_A_30

# Mapeo de correspondencia ontológica entre falla física de taller y clases entrenadas del SVM
# Si una falla confirmada corresponde a una de las 61 clases entrenadas, se indica la clase canónica exacta.
# Si no existe clase entrenada en el modelo para esa falla específica, se marca como FUERA_DE_CLASE (Grupo B).
MAPEO_ONTOLOGICO = {
    "CASO_01": {
        "categoria": "A",
        "clase_esperada": "Falla en bujias o bobinas de encendido (misfire)",
        "motivo": "Misfire P0302 / bobina con salto a cilindro 1.",
    },
    "CASO_02": {
        "categoria": "A",
        "clase_esperada": "Inyectores sucios o filtro de combustible obstruido", # O mezcla/o-ring
        "motivo": "Fuga de vacío en o-ring de inyector / mezcla pobre.",
    },
    "CASO_03": {
        "categoria": "A",
        "clase_esperada": "Falla en termostato o motoventilador de radiador",
        "motivo": "Termostato trabado cerrado / recalentamiento.",
    },
    "CASO_04": {
        "categoria": "A",
        "clase_esperada": "Empaque de culata soplado o danado",
        "motivo": "Culata soplada entre cilindros 2 y 3.",
    },
    "CASO_05": {
        "categoria": "A",
        "clase_esperada": "Fuga parasita de corriente en reposo (consumo nocturno de bateria)",
        "motivo": "Consumo parásito de 480 mA en reposo.",
    },
    "CASO_06": {
        "categoria": "A",
        "clase_esperada": "Alternador defectuoso o placa de diodos quemada",
        "motivo": "Diodos quemados en alternador con rizado AC.",
    },
    "CASO_07": {
        "categoria": "B",
        "clase_esperada": None,
        "motivo": "Transponder de llave desprogramado (inmovilizador puro sin clase en SVM).",
    },
    "CASO_08": {
        "categoria": "A",
        "clase_esperada": "Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)",
        "motivo": "Escobillas de motor de arranque gastadas.",
    },
    "CASO_09": {
        "categoria": "A",
        "clase_esperada": "Faja o cadena de distribucion destensada o con salto de punto",
        "motivo": "Cadena de distribución estirada desfasada.",
    },
    "CASO_10": {
        "categoria": "A",
        "clase_esperada": "Cuerpo de aceleracion o valvula IAC sucia",
        "motivo": "Cuerpo de aceleración descalibrado / sucio.",
    },
    "CASO_11": {
        "categoria": "A",
        "clase_esperada": "Disco de embrague desgastado o patinando",
        "motivo": "Disco de embrague desgastado / patinando.",
    },
    "CASO_12": {
        "categoria": "B",
        "clase_esperada": None, # No hay clase específica 'Volante bimasa', la más cercana es embrague
        "motivo": "Volante bimasa desgastado (componente específico no etiquetado independientemente en SVM).",
    },
    "CASO_13": {
        "categoria": "A",
        "clase_esperada": "Falla en bombin o bomba hidraulica de embrague",
        "motivo": "Cilindro esclavo concéntrico (CSC) de embrague.",
    },
    "CASO_14": {
        "categoria": "A",
        "clase_esperada": "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)",
        "motivo": "Retorno excesivo en inyector diésel con caída de presión de riel.",
    },
    "CASO_15": {
        "categoria": "A",
        "clase_esperada": "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)",
        "motivo": "Válvula reguladora SCV atascada en bomba de alta Denso Common Rail.",
    },
    "CASO_16": {
        "categoria": "A",
        "clase_esperada": "Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)",
        "motivo": "Filtro DPF colmatado.",
    },
    "CASO_17": {
        "categoria": "A",
        "clase_esperada": "Fuga en mangueras de intercooler o turbocompresor danado",
        "motivo": "Manguera de intercooler rajada con fuga de presión boost.",
    },
    "CASO_18": {
        "categoria": "A",
        "clase_esperada": "Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI",
        "motivo": "Geometría variable VGT de turbo trabada.",
    },
    "CASO_19": {
        "categoria": "A",
        "clase_esperada": "Fuga en mangueras de intercooler o turbocompresor danado", # O consumo de aceite
        "motivo": "Cojinetes axiales de turbo con paso de aceite.",
    },
    "CASO_20": {
        "categoria": "A",
        "clase_esperada": "Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)",
        "motivo": "Cristalización de urea en inyector AdBlue / SCR.",
    },
    "CASO_21": {
        "categoria": "B",
        "clase_esperada": None,
        "motivo": "Reductor/filtro GLP de conversión a gas (componente retrofit no entrenado en SVM).",
    },
    "CASO_22": {
        "categoria": "B",
        "clase_esperada": None,
        "motivo": "Emulador de corte de inyectores GNV (accesorio electrónico externo no entrenado en SVM).",
    },
    "CASO_23": {
        "categoria": "A",
        "clase_esperada": "Discos de freno alabeados o desgastados",
        "motivo": "Alabeo excesivo de disco de freno con vibración en pedal.",
    },
    "CASO_24": {
        "categoria": "A",
        "clase_esperada": "Fuga hidraulica o aire en el sistema de frenos",
        "motivo": "Fuga interna en bomba maestra de freno con pedal esponjoso al fondo.",
    },
    "CASO_25": {
        "categoria": "B",
        "clase_esperada": None,
        "motivo": "Rótula de suspensión inferior (la clase SVM cubre 'Amortiguadores reventados o bujes' pero no rótula explícita).",
    },
    "CASO_26": {
        "categoria": "A",
        "clase_esperada": "Fuga en mangueras de refrigerante o radiador picado", # O termostato
        "motivo": "Caja termostática plástica rajada con fuga de refrigerante.",
    },
    "CASO_27": {
        "categoria": "A",
        "clase_esperada": "Bateria descargada o bornes sulfatados", # O EVAP
        "motivo": "Doble falla con borne sulfatado y manguera de purga EVAP.",
    },
    "CASO_28": {
        "categoria": "A",
        "clase_esperada": "Inyectores sucios o filtro de combustible obstruido", # O baja presión
        "motivo": "Malla filtrante pescador de tanque colmatada.",
    },
    "CASO_29": {
        "categoria": "A",
        "clase_esperada": "Cuerpo de aceleracion o valvula IAC sucia",
        "motivo": "Válvula IAC atascada con carbón en posición abierta.",
    },
    "CASO_30": {
        "categoria": "A",
        "clase_esperada": "Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura)",
        "motivo": "Rodamiento de maza picado con zumbido en curva.",
    },
}

resultados_eval = []
top1_aciertos = 0
top3_aciertos = 0
total_evaluables = 0

conteo_categorias = {"A": 0, "B": 0, "C": 0, "D": 0}

for c in todos_los_casos:
    cid = c["id"]
    map_info = MAPEO_ONTOLOGICO.get(cid, {"categoria": "C", "clase_esperada": None, "motivo": "Sin clasificar"})
    cat = map_info["categoria"]
    conteo_categorias[cat] += 1
    
    # Texto completo del caso hasta el turno de diagnóstico técnico
    # Tomamos los primeros 5 turnos donde se expone el síntoma y pruebas iniciales
    turnos = c.get("turnos", [])
    texto_eval = " ".join(turnos[:min(5, len(turnos))])
    
    vec = vectorizador.transform([texto_eval])
    probs = modelo.predict_proba(vec)[0]
    top_indices = probs.argsort()[::-1][:5]
    top_predicciones = [
        {"clase": str(clases_entrenadas[idx]), "prob": round(float(probs[idx]), 4)}
        for idx in top_indices
    ]
    
    es_evaluable = (cat == "A")
    es_top1 = False
    es_top3 = False
    
    if es_evaluable:
        total_evaluables += 1
        clase_esp = map_info["clase_esperada"]
        
        # Evaluar Top-1
        if top_predicciones[0]["clase"] == clase_esp:
            es_top1 = True
            top1_aciertos += 1
        
        # Evaluar Top-3
        clases_top3 = [p["clase"] for p in top_predicciones[:3]]
        if clase_esp in clases_top3:
            es_top3 = True
            top3_aciertos += 1
            
    resultados_eval.append({
        "id": cid,
        "categoria": cat,
        "falla_confirmada": c.get("falla_confirmada"),
        "clase_esperada": map_info["clase_esperada"],
        "motivo": map_info["motivo"],
        "top_1": top_predicciones[0],
        "top_3": top_predicciones[:3],
        "es_top1": es_top1,
        "es_top3": es_top3,
    })

print("=" * 70)
print("RESUMEN DE CLASIFICACIÓN DE LOS 30 CASOS:")
print(f"  Categoría A (Clase entrenada): {conteo_categorias['A']}")
print(f"  Categoría B (Fuera de clases / OOD): {conteo_categorias['B']}")
print(f"  Categoría C (Ambiguo / evidencia insuficiente): {conteo_categorias['C']}")
print(f"  Categoría D (Error de extracción / contexto): {conteo_categorias['D']}")
print("=" * 70)
print(f"MÉTRICAS SVM SOBRE CASOS EVALUABLES (Categoría A = {total_evaluables} casos):")
print(f"  Top-1 Accuracy: {top1_aciertos}/{total_evaluables} ({top1_aciertos/total_evaluables:.2%})")
print(f"  Top-3 Accuracy: {top3_aciertos}/{total_evaluables} ({top3_aciertos/total_evaluables:.2%})")
print("=" * 70)

# Imprimir detalle de casos donde Top-1 o Top-3 falló en Categoría A
print("\nDETALLE DE CASOS CATEGORÍA A CON DISCREPANCIA:")
for r in resultados_eval:
    if r["categoria"] == "A":
        status = "ACIERTO TOP-1" if r["es_top1"] else ("ACIERTO TOP-3" if r["es_top3"] else "FALLO TOTAL")
        print(f"[{r['id']}] {status} | Esp: '{r['clase_esperada']}'")
        print(f"       Pred Top-1: '{r['top_1']['clase']}' ({r['top_1']['prob']:.2%})")
        if not r["es_top1"]:
            print(f"       Pred Top-2: '{r['top_3'][1]['clase']}' ({r['top_3'][1]['prob']:.2%})")
            print(f"       Pred Top-3: '{r['top_3'][2]['clase']}' ({r['top_3'][2]['prob']:.2%})")

# Imprimir casos Categoría B (OOD)
print("\nDETALLE DE CASOS CATEGORÍA B (FUERA DE DISTRIBUCIÓN / SIN CLASE):")
for r in resultados_eval:
    if r["categoria"] == "B":
        print(f"[{r['id']}] Falla física: '{r['falla_confirmada']}'")
        print(f"       Asignación espuria Top-1: '{r['top_1']['clase']}' ({r['top_1']['prob']:.2%})")
        print(f"       Motivo OOD: {r['motivo']}")

# Guardar análisis en JSON
salida_path = Path("tests/auditoria_profunda/analisis_fase_4_svm.json")
salida_path.parent.mkdir(parents=True, exist_ok=True)
with open(salida_path, "w", encoding="utf-8") as f:
    json.dump({
        "conteo_categorias": conteo_categorias,
        "total_evaluables_cat_a": total_evaluables,
        "top1_aciertos": top1_aciertos,
        "top1_accuracy": round(top1_aciertos / total_evaluables, 4),
        "top3_aciertos": top3_aciertos,
        "top3_accuracy": round(top3_aciertos / total_evaluables, 4),
        "casos": resultados_eval,
    }, f, indent=2, ensure_ascii=False)

print(f"\nResultados guardados en {salida_path}")
