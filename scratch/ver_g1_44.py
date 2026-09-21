import json

with open("docs/graficas/reporte_prueba_general_100_casos.json", encoding="utf-8") as f:
    d = json.load(f)
c = [x for x in d["casos_completos"] if x["id"] == "G1_44"][0]
rep = c.get("reporte_tecnico_completo", "")
print("RAG:", c.get("titulo_rag"))
print("Longitud reporte:", len(rep))
for line in rep.split("\n")[:25]:
    print(line.encode("ascii", "replace").decode("ascii"))
