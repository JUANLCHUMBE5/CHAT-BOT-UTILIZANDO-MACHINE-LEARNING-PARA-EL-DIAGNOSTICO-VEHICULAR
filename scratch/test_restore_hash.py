import hashlib

content = open("backend/src/infrastructure/modelo_ml.py", "rb").read()

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

restored = content.replace(old_chunk, target_chunk)
print("Restored len:", len(restored))
h = hashlib.sha256(restored).hexdigest()
print("Restored hash:", h)
print("Matches 014d3e6f...?", h == "014d3e6f6f9f5c5bc5e6223e748566ce6a1ecdb70842df7afc7037c51b6a5eb4")
