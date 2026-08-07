import json
import re
import sys
from pathlib import Path
import pandas as pd

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from src.core.taxonomy.catalogo_fallas import CATALOGO_TAXONOMIA, MAPA_UNIFICACION_ETIQUETAS


def normalizar_texto_sintoma(texto: str) -> str:
    """Normaliza espacios, minúsculas y caracteres especiales."""
    if not isinstance(texto, str):
        return ""
    texto = texto.lower().strip()
    texto = re.sub(r"\s+", " ", texto)
    return texto


def limpiar_y_estructurar_dataset():
    path_in = Path("data/dataset_sintomas.csv")
    path_out = Path("data/dataset_sintomas_limpio.csv")
    path_reporte = Path("data/reporte_calidad_dataset.json")

    df = pd.read_csv(path_in, encoding="utf-8")
    filas_iniciales = len(df)
    clases_iniciales = df["falla"].nunique()

    # 1. Mapear cada falla antigua a su código estable y falla principal estándar
    df["sintoma_norm"] = df["sintoma"].apply(normalizar_texto_sintoma)
    
    codigos = []
    fallas_estandar = []
    sistemas = []
    severidades = []

    no_mapeadas = 0
    for f in df["falla"]:
        codigo = MAPA_UNIFICACION_ETIQUETAS.get(f)
        if codigo and codigo in CATALOGO_TAXONOMIA:
            estandar = CATALOGO_TAXONOMIA[codigo]
            codigos.append(codigo)
            fallas_estandar.append(estandar.falla_principal)
            sistemas.append(estandar.sistema)
            severidades.append(estandar.severidad)
        else:
            # Fallback limpio si no está en el mapa
            codigos.append("OTROS_001")
            fallas_estandar.append(f)
            sistemas.append("General")
            severidades.append("media")
            no_mapeadas += 1

    df["codigo_falla"] = codigos
    df["falla_estandar"] = fallas_estandar
    df["sistema"] = sistemas
    df["severidad"] = severidades

    # 2. Filtrar fallas genéricas no clasificadas (OBD genérico tipo P0, P2) si son ruido
    df_filtrado = df[df["codigo_falla"] != "OTROS_001"].copy()
    
    # 3. Detectar y resolver contradicciones (mismo síntoma idéntico con distintos códigos)
    agrupado = df_filtrado.groupby("sintoma_norm")["codigo_falla"].nunique()
    sintomas_contradictorios = agrupado[agrupado > 1].index.tolist()

    # Conservar la etiqueta con mayor frecuencia ante contradicción
    df_sin_contradicciones = (
        df_filtrado.groupby(["sintoma_norm", "codigo_falla"])
        .size()
        .reset_index(name="conteo")
        .sort_values(["sintoma_norm", "conteo"], ascending=[True, False])
        .drop_duplicates(subset=["sintoma_norm"], keep="first")
    )

    # 4. Reconstruir dataset limpio sin duplicados
    df_final = df_filtrado.drop_duplicates(subset=["sintoma_norm", "codigo_falla"]).copy()
    df_final = df_final[df_final["sintoma_norm"].isin(df_sin_contradicciones["sintoma_norm"])]
    
    # Reemplazar columna 'falla' por la falla_estandar para mantener compatibilidad
    df_final["falla"] = df_final["falla_estandar"]
    df_export = df_final[["sintoma", "falla", "codigo_falla", "sistema", "severidad"]].copy()

    df_export.to_csv(path_out, index=False, encoding="utf-8")

    reporte = {
        "filas_iniciales": filas_iniciales,
        "clases_iniciales": clases_iniciales,
        "filas_finales": len(df_export),
        "clases_unificadas": df_export["codigo_falla"].nunique(),
        "sistemas_cubiertos": df_export["sistema"].nunique(),
        "sintomas_contradictorios_resueltos": len(sintomas_contradictorios),
        "duplicados_exactos_eliminados": filas_iniciales - len(df_export),
        "catalogo_codigos": sorted(list(df_export["codigo_falla"].unique())),
    }

    path_reporte.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
    print("=" * 80)
    print("REPORTE DE LIMPIEZA Y NORMALIZACION DE TAXONOMIA ML")
    print("=" * 80)
    print(f"Filas iniciales:                     {filas_iniciales}")
    print(f"Filas limpias finales:               {len(df_export)}")
    print(f"Clases unificadas con código único:  {df_export['codigo_falla'].nunique()}")
    print(f"Contradicciones resueltas:           {len(sintomas_contradictorios)}")
    print(f"Archivo generado:                    {path_out}")
    print(f"Reporte de calidad guardado en:      {path_reporte}")
    print("=" * 80)


if __name__ == "__main__":
    limpiar_y_estructurar_dataset()
