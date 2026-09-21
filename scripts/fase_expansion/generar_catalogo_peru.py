import json
import re
from pathlib import Path
from collections import defaultdict, Counter

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
ALERTAS_PATH = PROJECT_ROOT / "machine_learning" / "data" / "fuentes_abiertas" / "fallas_vehiculares" / "peru_indecopi" / "alertas_indecopi.json"

with open(ALERTAS_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

alerts = data.get("alertas", [])

CONOCIDAS = [
    "TOYOTA", "HYUNDAI", "KIA", "NISSAN", "CHEVROLET", "FORD", "VOLKSWAGEN",
    "SUZUKI", "MITSUBISHI", "HONDA", "MAZDA", "SUBARU", "MERCEDES-BENZ",
    "MERCEDES BENZ", "BMW", "AUDI", "LEXUS", "JEEP", "RAM", "JAC", "HINO",
    "PEUGEOT", "RENAULT", "CITROEN", "CHERY", "GREAT WALL", "HAVAL", "CHANGAN",
    "GEELY", "VOLVO", "LAND ROVER", "PORSCHE", "FIAT", "SCANIA", "ISUZU",
    "FUSO", "YAMAHA", "BAJAJ", "CHRYSLER", "DODGE"
]

marca_a_modelos = defaultdict(set)
marca_conteo = Counter()

for a in alerts:
    tit = a.get("vcTitulo", "")
    prob = a.get("vcProblema", "")
    texto = f"{tit} {prob}".upper()

    marca_detectada = None
    # 1. Chequear lista de productos
    for p in a.get("productos", []):
        m = p.get("vcMarca")
        mod = p.get("vcModelo")
        if m:
            marca_detectada = m.strip().upper()
            if mod:
                marca_a_modelos[marca_detectada].add(mod.strip().upper())

    # 2. Si no hay productos, extraer del título
    if not marca_detectada:
        for c in CONOCIDAS:
            if re.search(r'\b' + re.escape(c) + r'\b', texto):
                marca_detectada = "MERCEDES-BENZ" if c == "MERCEDES BENZ" else c
                break

    if marca_detectada:
        marca_conteo[marca_detectada] += 1
        # Intentar extraer modelo del título (ej. "Vehículos Ford Mustang", "Vehículos Toyota Yaris")
        m_match = re.search(re.escape(marca_detectada) + r'\s+([A-Za-z0-9\-\s]{2,20}?)(?:\s+(?:podrían|presentarían|año|fabricados|modelo|con|por|\.|\,)|$)', tit, re.IGNORECASE)
        if m_match:
            mod_cand = m_match.group(1).strip().upper()
            if len(mod_cand) >= 2 and not any(w in mod_cand for w in ["VEHÍCULOS", "MODELO", "AÑO", "PODRÍAN"]):
                marca_a_modelos[marca_detectada].add(mod_cand)

# Convertir sets a listas ordenadas
catalogo = {
    "fecha": "2026-09-19",
    "fuente": "INDECOPI - Alertas de Consumo Perú",
    "total_alertas_vehiculares": len(alerts),
    "marcas_identificadas": len(marca_conteo),
    "distribucion_marcas": dict(marca_conteo.most_common()),
    "modelos_por_marca": {k: sorted(list(v)) for k, v in sorted(marca_a_modelos.items())}
}

out_path = PROJECT_ROOT / "machine_learning" / "data" / "fuentes_abiertas" / "fallas_vehiculares" / "peru_indecopi" / "catalogo_peru_marcas_modelos.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(catalogo, f, indent=2, ensure_ascii=False)

print(f"Catálogo de marcas y modelos Perú generado en: {out_path}")
print(f"Total marcas identificadas: {len(marca_conteo)}")
print("Top 15 marcas en Perú Indecopi:")
for k, v in marca_conteo.most_common(15):
    print(f"  {k}: {v} alertas (modelos: {len(marca_a_modelos.get(k, []))})")
