import pandas as pd
import unicodedata
import re
from pathlib import Path

PREFIJOS = re.compile(
    r"\b(amigo una consulta|tengo un problema con mi auto|tengo un problema|"
    r"resulta que en mi carro|resulta que|sabes que|mi carro presenta|"
    r"amigo mi auto presenta|maestro una consulta|buenas tardes mecanico|"
    r"en mi vehiculo noto que|hace dos dias noto que)\b"
)
SUFIJOS = re.compile(
    r"\b(ultimamente|desde ayer|en carabayllo|en la pista|en las mananas|"
    r"cuando voy manejando|cuando salgo a trabajar|al pasar un rompemuelles|"
    r"de la nada|al acelerar|al andar a \d+ km(?:/h| por hora)?)\b"
)


def norm_g(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = PREFIJOS.sub(" ", t)
    t = SUFIJOS.sub(" ", t)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()


def test():
    df = pd.read_csv("machine_learning/data/dataset_sintomas_limpio.csv")
    grps = df.apply(lambda r: r["falla"] + "###" + norm_g(r["sintoma"]), axis=1)
    print("Total filas:", len(df))
    print("Total grupos únicos:", grps.nunique())
    print("Distribución tamaño de grupos:")
    vc = grps.value_counts()
    print("  Tamaño 1:", (vc == 1).sum())
    print("  Tamaño 2-4:", ((vc >= 2) & (vc <= 4)).sum())
    print("  Tamaño 5+:", (vc >= 5).sum())
    print("  Tamaño máximo:", vc.max())


if __name__ == "__main__":
    test()
