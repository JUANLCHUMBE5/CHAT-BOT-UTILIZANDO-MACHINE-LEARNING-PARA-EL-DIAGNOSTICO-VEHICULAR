import shutil
import hashlib
from pathlib import Path

# 1. Restore backend/src/infrastructure/modelo_ml.py to exact 8022 bytes
code = open("backend/src/infrastructure/modelo_ml.py", "rb").read()
old_chunk = b"""        if modelo_sistema_path is None:
            self.modelo_sistema_path = str(
                getattr(settings.paths, "modelo_sistema_pkl", None)
                or (Path(self.modelo_path).parent / "modelo_sistema.pkl")
            )
        else:
            self.modelo_sistema_path = modelo_sistema_path"""

target_chunk = b"""        if modelo_sistema_path is None:
            self.modelo_sistema_path = str(Path(self.modelo_path).parent / "modelo_sistema.pkl")
        else:
            self.modelo_sistema_path = modelo_sistema_path"""

new_bytes = code.replace(old_chunk, target_chunk)
assert hashlib.sha256(new_bytes).hexdigest() == "014d3e6f6f9f5c5bc5e6223e748566ce6a1ecdb70842df7afc7037c51b6a5eb4"
with open("backend/src/infrastructure/modelo_ml.py", "wb") as f:
    f.write(new_bytes)

# 2. Copy macrofix to modelo_sistema.pkl in c1_fase10_final so default path works
src_macro = Path("machine_learning/models/c1_fase10_final/modelo_sistema_c1_macrofix.pkl")
dst_macro = Path("machine_learning/models/c1_fase10_final/modelo_sistema.pkl")
shutil.copy2(src_macro, dst_macro)

print("Successfully restored modelo_ml.py to original hash and copied modelo_sistema.pkl!")
