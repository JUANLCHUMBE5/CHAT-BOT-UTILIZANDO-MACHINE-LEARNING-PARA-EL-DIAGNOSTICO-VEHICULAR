import hashlib
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent

files = [
    ("C1 Vectorizador Congelado", "machine_learning/training/fase10/final_candidate/C1/vectorizador_c1.pkl", "060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7"),
    ("C1 Falla Congelado", "machine_learning/training/fase10/final_candidate/C1/modelo_diagnostico_c1.pkl", "24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c"),
    ("C1 Macrofix Congelado", "machine_learning/training/fase10/final_candidate/C1/modelo_sistema_c1_macrofix.pkl", "dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c"),
    ("C1 Vectorizador Produccion", "machine_learning/models/c1_fase10_final/vectorizador_c1.pkl", "060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7"),
    ("C1 Falla Produccion", "machine_learning/models/c1_fase10_final/modelo_diagnostico_c1.pkl", "24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c"),
    ("C1 Macrofix Produccion", "machine_learning/models/c1_fase10_final/modelo_sistema_c1_macrofix.pkl", "dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c"),
    ("F8.3 Falla Original", "machine_learning/models/modelo_diagnostico.pkl", "3d8199595b69bb0176fbb4bb9d7c57b43484f16e6f6baa115660405b76aa13fd"),
    ("F8.3 Macro Original", "machine_learning/models/modelo_sistema.pkl", "22d11492e9576664ee21fcc3dc75e040c2b9f2c5c326ccdef98c602fbc78fc27"),
    ("F8.3 Vectorizador Original", "machine_learning/models/vectorizador_tfidf.pkl", "8b8e8c3b3571fe965174bff67faff0ac57aaadccf17d4e40395e4c1ab3273104"),
    ("F8.3 Falla Frozen", "machine_learning/models/fase8_3_frozen/modelo_diagnostico.pkl", "3d8199595b69bb0176fbb4bb9d7c57b43484f16e6f6baa115660405b76aa13fd"),
    ("F8.3 Macro Frozen", "machine_learning/models/fase8_3_frozen/modelo_sistema.pkl", "22d11492e9576664ee21fcc3dc75e040c2b9f2c5c326ccdef98c602fbc78fc27"),
    ("F8.3 Vectorizador Frozen", "machine_learning/models/fase8_3_frozen/vectorizador_tfidf.pkl", "8b8e8c3b3571fe965174bff67faff0ac57aaadccf17d4e40395e4c1ab3273104"),
    ("TRAIN10 v1.1 Macrofix", "machine_learning/data/fase10/train10_v1_1_macrofix.csv", "71d67e1109e9de0cafa86640d9fd04045b6809f912d342eb706f836d114c326c"),
    ("DEV10 v1.1 Macrofix", "machine_learning/data/fase10/dev10_v1_1_macrofix.csv", "2b5aba4f21bb32f848eca639ea933600f43502544a20acee84c54c638f85ee16"),
    ("TEST10 Blind Sealed", "machine_learning/data/fase10/test10_fase10_blind_v1.csv", "6eaf42bca03d2aad98c8e414bfef541a74a42a0ff605eb4431b34b90cb7d0d0c"),
]

all_intact = True
print("=== VERIFICACION FINAL DE INMUTABILIDAD DE HASHES ===")
for label, rel_path, exp_hash in files:
    p = base_dir / rel_path
    if not p.exists():
        print(f"ERROR: {label} ({rel_path}) NO EXISTE!")
        all_intact = False
        continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    match = (h == exp_hash)
    if not match:
        all_intact = False
    status = "OK" if match else "FALLO"
    print(f"  {label:<32}: {status} [{h[:16]}...]")

print(f"\nDictamen de inmutabilidad: {'TODOS INTACTOS (100%)' if all_intact else 'ALERTA: DISCREPANCIA DETECTADA'}")
