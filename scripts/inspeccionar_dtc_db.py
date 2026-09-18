"""Inspección de las bases de datos descargadas: SQLite DTC y OBDex."""

import sqlite3
from pathlib import Path

db_path = Path("machine_learning/data/fuentes_abiertas/dtc_codes.db")
obdex_p0 = Path("machine_learning/data/fuentes_abiertas/obdex/P0xxx_enriched.yaml")

print("--- 1. DTC DATABASE (SQLite) ---")
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = [t[0] for t in cur.fetchall()]
    print("Tablas encontradas:", tablas)
    for t in tablas:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"  Tabla '{t}': {cur.fetchone()[0]} filas")
        cur.execute(f"SELECT * FROM {t} LIMIT 2")
        print(f"  Ejemplo '{t}':", cur.fetchall())
    conn.close()

print("\n--- 2. OBDex (YAML) ---")
if obdex_p0.exists():
    with open(obdex_p0, "r", encoding="utf-8") as f:
        lineas = [next(f) for _ in range(40)]
        print("".join(lineas[:35]))
