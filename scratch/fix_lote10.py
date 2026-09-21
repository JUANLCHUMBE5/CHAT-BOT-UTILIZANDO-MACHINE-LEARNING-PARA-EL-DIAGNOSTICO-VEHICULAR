import re

with open("scratch/lote10_clases_55_58.py", "r", encoding="utf-8") as f:
    text = f.read()

text = re.sub(r'agregar\("(G-10-55-\d+)",\s*"L3",', r'agregar("\1", CLASE_55, "L3",', text)
text = re.sub(r'agregar\("(G-10-56-\d+)",\s*"L3",', r'agregar("\1", CLASE_56, "L3",', text)
text = re.sub(r'agregar\("(G-10-57-\d+)",\s*"L3",', r'agregar("\1", CLASE_57, "L3",', text)
text = re.sub(r'agregar\("(G-10-58-\d+)",\s*"L3",', r'agregar("\1", CLASE_58, "L3",', text)

with open("scratch/lote10_clases_55_58.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Reemplazo completado con exito.")
