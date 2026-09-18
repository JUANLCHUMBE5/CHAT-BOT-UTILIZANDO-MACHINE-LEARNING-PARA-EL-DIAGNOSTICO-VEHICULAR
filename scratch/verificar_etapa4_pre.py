import hashlib
import json
import pathlib

base_dir = pathlib.Path('.').resolve()
rep_path = base_dir / 'machine_learning' / 'models' / 'reporte_fase8_3_congelado.json'
with open(rep_path, 'r', encoding='utf-8') as f:
    f8_data = json.load(f)

hashes_ref = f8_data['hashes_sha256']
f8_intact = 0
for k, v in hashes_ref.items():
    file_path = base_dir / v['archivo']
    h = hashlib.sha256(file_path.read_bytes()).hexdigest()
    if h == v['sha256']:
        f8_intact += 1
    else:
        print(f"MISMATCH in {k}: {h} != {v['sha256']}")
print(f"F8.3 Hashes verified: {f8_intact}/{len(hashes_ref)}")
assert f8_intact == len(hashes_ref), "F8.3 hash mismatch!"

p_vec = base_dir / 'machine_learning/training/fase10/candidates/C1/vectorizador_c1.pkl'
p_diag = base_dir / 'machine_learning/training/fase10/candidates/C1/modelo_diagnostico_c1.pkl'
p_macrofix = base_dir / 'machine_learning/training/fase10/candidates/C1/modelo_sistema_c1_macrofix.pkl'
p_test = base_dir / 'machine_learning/data/fase10/test10_fase10_blind_v1.csv'
p_tr_fix = base_dir / 'machine_learning/data/fase10/train10_v1_1_macrofix.csv'
p_dev_fix = base_dir / 'machine_learning/data/fase10/dev10_v1_1_macrofix.csv'

h_vec = hashlib.sha256(p_vec.read_bytes()).hexdigest()
h_diag = hashlib.sha256(p_diag.read_bytes()).hexdigest()
h_macrofix = hashlib.sha256(p_macrofix.read_bytes()).hexdigest()
h_test = hashlib.sha256(p_test.read_bytes()).hexdigest()
h_tr_fix = hashlib.sha256(p_tr_fix.read_bytes()).hexdigest()
h_dev_fix = hashlib.sha256(p_dev_fix.read_bytes()).hexdigest()

print(f"C1 Vectorizer: {h_vec}")
assert h_vec == '060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7'

print(f"C1 Diagnostico: {h_diag}")
assert h_diag == '24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c'

print(f"C1 Macrofix: {h_macrofix}")
assert h_macrofix == 'dec3ba707ff000b34c9368935ebe14c30439475910ea82f846cc8e3b9c85930c'

print(f"TEST10: {h_test}")
assert h_test == '6eaf42bca03d2aad98c8e414bfef541a74a42a0ff605eb4431b34b90cb7d0d0c'

print(f"TRAIN10 Macrofix: {h_tr_fix}")
assert h_tr_fix == '71d67e1109e9de0cafa86640d9fd04045b6809f912d342eb706f836d114c326c'

print(f"DEV10 Macrofix: {h_dev_fix}")
assert h_dev_fix == '2b5aba4f21bb32f848eca639ea933600f43502544a20acee84c54c638f85ee16'

print("\nTODAS LAS VERIFICACIONES PREVIAS COMPLETADAS AL 100%!")
