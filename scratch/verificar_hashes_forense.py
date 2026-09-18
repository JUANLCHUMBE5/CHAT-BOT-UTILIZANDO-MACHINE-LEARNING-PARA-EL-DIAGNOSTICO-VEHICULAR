import hashlib
import json
from pathlib import Path

base_dir = Path('.').resolve()
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
        print(f"MISMATCH in {k} ({v['archivo']}): {h} != {v['sha256']}")

print(f"F8.3 Hashes verified: {f8_intact}/{len(hashes_ref)}")

datasets = {
    'TRAIN10': ('machine_learning/data/fase10/train10_v1.csv', 'ec407886b48d66c4d9be6fc8b72decf605f4f94ac1af0575d9c4fa0db005e92b'),
    'DEV10': ('machine_learning/data/fase10/dev10_v1.csv', 'b44a752ca58fb4e27c7d9167198747e076d0c3cd5c4b07eaa03919777d1fd2b6'),
    'TEST10': ('machine_learning/data/fase10/test10_fase10_blind_v1.csv', '6eaf42bca03d2aad98c8e414bfef541a74a42a0ff605eb4431b34b90cb7d0d0c'),
}

for name, (rel_path, expected) in datasets.items():
    fp = base_dir / rel_path
    h = hashlib.sha256(fp.read_bytes()).hexdigest()
    match = (h == expected)
    print(f"{name}: {h} (Match: {match})")
