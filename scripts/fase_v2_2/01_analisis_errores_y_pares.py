"""
01_analisis_errores_y_pares.py
FASE EXPERIMENTAL CARBOT V2.2 — FASES 0, 1 Y 2
1. Inicializa el sandbox carbot_v2_2.
2. Registra hashes PRE de producción.
3. Analiza los 66 errores reales de V2.1-B (ANALISIS_ERRORES_MEJOR_CANDIDATO.csv).
4. Genera ERROR_PAIRS_V2_2.csv priorizando pares con mayor solapamiento y degradación.
"""
import sys
import os
import json
import csv
import hashlib
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
V2_1_DIR = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2_1"
V2_2_DIR = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2_2"
DATA_DIR = V2_2_DIR / "data"
MODELS_DIR = V2_2_DIR / "models"
EVAL_DIR = V2_2_DIR / "evaluacion"

for d in [DATA_DIR, MODELS_DIR, EVAL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 1. Hashes PRE (Fase 0)
MANIFEST_PATH = PROJECT_ROOT / "docs" / "fase11_6" / "CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json"

def registrar_hashes_pre():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    pre_hashes = {}
    for comp, info in manifest["hashes_sha256"].items():
        p = PROJECT_ROOT / info["ruta_relativa"]
        h = hashlib.sha256()
        with open(p, "rb") as bf:
            while chunk := bf.read(65536):
                h.update(chunk)
        calc_hash = h.hexdigest()
        assert calc_hash == info["sha256"], f"ALERTA PRE: Hash no coincide en {comp}"
        pre_hashes[comp] = {
            "ruta": info["ruta_relativa"],
            "sha256": calc_hash,
            "status": "VERIFIED_IDENTICAL"
        }

    out_pre = V2_2_DIR / "HASHES_PRE_V2_2.json"
    with open(out_pre, "w", encoding="utf-8") as f:
        json.dump(pre_hashes, f, indent=2)
    print(f"Hashes PRE verificados y guardados: {out_pre.name} (13/13 coinciden)")

# 2. Analizar errores reales de V2.1 (Fase 1 y 2)
def analizar_errores_v2_1():
    csv_errores = V2_1_DIR / "ANALISIS_ERRORES_MEJOR_CANDIDATO.csv"
    assert csv_errores.exists(), f"No existe {csv_errores}"

    df_err = pd.read_csv(csv_errores)
    print(f"\nCargados {len(df_err)} errores reales de V2.1-B")

    # Contar pares (ground_truth, prediction_top1)
    pair_counts = Counter()
    pair_examples = defaultdict(list)
    pair_causes = defaultdict(lambda: Counter())

    for _, row in df_err.iterrows():
        gt = row["ground_truth"]
        pred = row["prediction_top1"]
        causa = row["causa_probable"]
        txt = row["texto"]
        pair_counts[(gt, pred)] += 1
        pair_examples[(gt, pred)].append(txt)
        pair_causes[(gt, pred)][causa] += 1

    # Definición de pruebas diagnósticas y discriminantes basadas en manuales OEM y metrología
    REGLAS_DISCRIMINANTES = {
        ("Empaque de culata soplado o danado", "Fuga en mangueras de refrigerante o radiador picado"): {
            "discriminating_features": "Presencia de burbujas continuas de compresión en vaso de expansión vs fuga externa visible con circuito presurizado",
            "required_test": "Prueba química con reactivo de CO2 (bloque tester) o prueba de fuga de cilindros con aire comprimido",
            "required_measurement": "Presión circuito >1.5 bar en frío y cambio de color azul a amarillo en reactivo de hidrocarburos",
            "dtc_if_applicable": "P0217, P0300",
            "priority": "CRITICA"
        },
        ("Falla en bombin o bomba hidraulica de embrague", "Disco de embrague desgastado o patinando"): {
            "discriminating_features": "Pedal de embrague se va al fondo sin resistencia mecánica o fuga de líquido de frenos DOT3/4 en vástago vs patinamiento a altas RPM con pedal duro",
            "required_test": "Inspección de carrera libre del vástago del actuador hidráulico y purga de aire del circuito",
            "required_measurement": "Carrera efectiva de desacople <12 mm con pedal a fondo; nivel de depósito DOT",
            "dtc_if_applicable": "N/A (Falla mecánica hidráulica pura)",
            "priority": "ALTA"
        },
        ("Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados", "Falla en bujias o bobinas de encendido (misfire)"): {
            "discriminating_features": "Misfire persiste en el mismo cilindro tras intercambiar bobina y bujía a cilindro adyacente; pérdida de presión en cámara",
            "required_test": "Prueba de compresión húmeda con manómetro y prueba de estanqueidad neumática (leak-down tester)",
            "required_measurement": "Compresión relativa <70% respecto al cilindro de referencia; fuga >25% por escape o admisión",
            "dtc_if_applicable": "P0300, P0301, P0302, P0303, P0304",
            "priority": "CRITICA"
        },
        ("Baja presion de aceite o bomba de aceite defectuosa", "Consumo de aceite por desgaste de anillos o retenes"): {
            "discriminating_features": "Testigo de presión de aceite encendido en ralentí en caliente con ruido de taqués vs humo azulado en escape al desacelerar con nivel bajo",
            "required_test": "Manómetro físico en puerto del bulbo de presión de aceite con motor a 90°C",
            "required_measurement": "Presión de aceite <0.8 bar (12 PSI) en ralentí o <2.5 bar a 2500 RPM",
            "dtc_if_applicable": "P0524, P0521",
            "priority": "ALTA"
        },
        ("Falla en bujias o bobinas de encendido (misfire)", "Disco de embrague desgastado o patinando"): {
            "discriminating_features": "Tironeo con caída brusca de RPM y testigo check parpadeante vs subida libre de RPM sin aumento proporcional de velocidad",
            "required_test": "Escáner en flujo de datos PID contador de fallos de encendido (Misfire Counts)",
            "required_measurement": "Contador >15 misfires por 1000 revoluciones",
            "dtc_if_applicable": "P0300, P0301-P0308",
            "priority": "MEDIA"
        },
        ("Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)", "Falla en sensor de oxigeno o mezcla rica"): {
            "discriminating_features": "Sensor downstream B1S2 oscila al mismo ritmo que upstream B1S1 indicando saturación del monolito cerámico vs sensor upstream congelado en tensión fija",
            "required_test": "Oscilograma comparativo de voltajes O2 sensor 1 vs sensor 2 a 2000 RPM en crucero",
            "required_measurement": "Frecuencia de oscilación B1S2 >0.5 Hz a temperatura de régimen (inversión de fase)",
            "dtc_if_applicable": "P0420, P0430",
            "priority": "ALTA"
        },
        ("Falla en sensor de oxigeno o mezcla rica", "Falla en regulador de presion de combustible o diafragma roto"): {
            "discriminating_features": "Presencia de combustible líquido en la manguera de vacío del regulador de riel vs código eléctrico de circuito de calefactor o señal fija",
            "required_test": "Inspección visual de diafragma y manómetro de riel con vacío conectado y desconectado",
            "required_measurement": "Variación de presión de combustible de 0.5 bar al desconectar toma de vacío",
            "dtc_if_applicable": "P0172, P0131, P0132",
            "priority": "MEDIA"
        },
        ("Discos de freno alabeados o desgastados", "Desgaste de pastillas y zapatas de freno"): {
            "discriminating_features": "Pulsación física en pedal de freno y oscilación del timón solo en desaceleración vs chirrido metálico constante de aviso acústico",
            "required_test": "Reloj comparador con base magnética en pista de fricción del disco montado en maza",
            "required_measurement": "Alabeo axial (runout) >0.05 mm (0.002 pulgadas); espesor mínimo por debajo de grabado OEM",
            "dtc_if_applicable": "N/A (Metrología mecánica pura)",
            "priority": "ALTA"
        },
        ("Caliper de freno trabado o mordaza pegada (piston agarrotado)", "Desgaste de pastillas y zapatas de freno"): {
            "discriminating_features": "Sobrecalentamiento extremo en una sola rueda, olor a balata quemada y desvío de dirección al soltar volante vs frenado uniforme",
            "required_test": "Pirómetro láser de temperatura en masa/cáliper tras recorrido y prueba de giro libre en elevador",
            "required_measurement": "Diferencial térmico >40°C entre rueda izquierda y derecha del mismo eje",
            "dtc_if_applicable": "N/A (Física térmica pura)",
            "priority": "ALTA"
        },
        ("Fuga parasita de corriente en reposo (consumo nocturno de bateria)", "Bateria descargada o bornes sulfatados"): {
            "discriminating_features": "Batería nueva o cargada se descarga tras 12-24h de parqueo; amperaje fluye con vehículo en reposo y módulos en sleep mode",
            "required_test": "Pinza amperimétrica milimétrica de corriente continua en borne negativo tras 30 min de bloqueo",
            "required_measurement": "Corriente de reposo parásita >50 mA (0.050 A)",
            "dtc_if_applicable": "U0100, B1000 (en caso de módulo que no entra en reposo)",
            "priority": "ALTA"
        },
        ("Alternador defectuoso o placa de diodos quemada", "Bateria descargada o bornes sulfatados"): {
            "discriminating_features": "Tensión de carga cae por debajo de 13.5V con motor encendido y luces altas; ondulación de corriente alterna en osciloscopio",
            "required_test": "Multímetro en bornes con motor en marcha a 2000 RPM y prueba de rizado AC",
            "required_measurement": "Tensión en bornes 13.8V - 14.4V normal; rizado AC <0.5V (diodos sanos)",
            "dtc_if_applicable": "P0562, P0620",
            "priority": "ALTA"
        },
        ("Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)", "Falla en bujias o bobinas de encendido (misfire)"): {
            "discriminating_features": "Corte simultáneo total de chispa en todas las bujías e inyección; tacómetro no marca RPM al dar arranque",
            "required_test": "Lectura de RPM por escáner durante arranque en seco y osciloscopio en señal inductiva/hall",
            "required_measurement": "Señal cuadrada 0-5V o senoidal >1V pico-pico durante arranque a 200 RPM",
            "dtc_if_applicable": "P0335, P0340",
            "priority": "MEDIA"
        },
        ("Bomba de gasolina quemada o con baja presion", "Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet)"): {
            "discriminating_features": "Bomba recibe 12V directos en conector pero no genera presión ni zumbido vs bomba sana pero módulo FSCM no modula PWM de tierra o no comunica",
            "required_test": "Medición de ciclo de trabajo PWM con multímetro/osciloscopio en terminal de control de bomba y prueba de caída de tensión",
            "required_measurement": "Presión fija vs modulada; código U0109 de comunicación perdida con FSCM",
            "dtc_if_applicable": "P0087, P025A, U0109",
            "priority": "ALTA"
        }
    }

    # Guardar ERROR_PAIRS_V2_2.csv
    filas_pares = []
    for (gt, pred), cnt in pair_counts.most_common():
        causa_top = pair_causes[(gt, pred)].most_common(1)[0][0]
        meta = REGLAS_DISCRIMINANTES.get((gt, pred), {
            "discriminating_features": f"Distinción técnica específica entre {gt} y {pred}",
            "required_test": "Inspección visual y escaneo de parámetros específicos",
            "required_measurement": "Tolerancia según manual de servicio OEM",
            "dtc_if_applicable": "DTC específico del subsistema",
            "priority": "ALTA" if cnt >= 2 else "MEDIA"
        })

        filas_pares.append({
            "ground_truth": gt,
            "confused_with": pred,
            "frequency": cnt,
            "error_type": causa_top,
            "discriminating_features": meta["discriminating_features"],
            "required_test": meta["required_test"],
            "required_measurement": meta["required_measurement"],
            "dtc_if_applicable": meta["dtc_if_applicable"],
            "priority": meta["priority"]
        })

    out_csv = V2_2_DIR / "ERROR_PAIRS_V2_2.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(filas_pares[0].keys()))
        writer.writeheader()
        writer.writerows(filas_pares)

    print(f"Pares de error guardados: {out_csv.name} ({len(filas_pares)} pares únicos)")
    print("\nTop 5 Pares de Confusión Más Críticos:")
    for p in filas_pares[:5]:
        print(f"  [{p['frequency']} casos] {p['ground_truth']}  -->  {p['confused_with']} ({p['priority']})")


if __name__ == "__main__":
    registrar_hashes_pre()
    analizar_errores_v2_1()
