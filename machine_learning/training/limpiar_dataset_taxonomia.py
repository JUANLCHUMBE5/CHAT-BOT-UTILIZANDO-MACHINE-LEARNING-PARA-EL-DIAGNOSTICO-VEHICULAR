"""Limpieza y normalización de dataset aplicando taxonomía vehicular con códigos estables."""

import json
import re
import sys
from pathlib import Path

import pandas as pd

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))
BACKEND_ROOT = RAIZ_PROYECTO.parent / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.core.taxonomy.catalogo_fallas import (  # noqa: E402 - importa tras configurar sys.path
    CATALOGO_TAXONOMIA,
    MAPA_UNIFICACION_ETIQUETAS,
)
from training.entrenar_y_comparar_modelos import normalizar_grupo  # noqa: E402


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

    df["sintoma_norm"] = df["sintoma"].apply(normalizar_texto_sintoma)

    # 1. Patrones de cuarentena: códigos DTC genéricos (P0, P2, P3, U0) y categorías ambiguas
    patrones_cuarentena = [
        "falla de sensores",
        "falla de control electronico",
        "averia detectada en sistema",
        "averia en modulo",
        "soportes de motor rotos o inyectores sucios",
    ]

    # Clases de puertas que requieren división técnica según el síntoma
    clases_puertas = [
        "Daño o desalineacion en la chapa / mecanismo de seguro de la puerta",
        "Dao o desalineacion en la chapa / mecanismo de seguro de la puerta",
        "Mecanismo de chapa / cerradura de puerta desalineada o trabada",
    ]

    codigos = []
    fallas_estandar = []
    sistemas = []
    severidades = []
    estados = []

    for _, row in df.iterrows():
        f = str(row["falla"]).strip()
        s = str(row["sintoma_norm"]).strip()
        f_lower = f.lower()

        # Verificar si pertenece a cuarentena
        if any(p in f_lower for p in patrones_cuarentena):
            estados.append("cuarentena")
            continue

        # Enrutamiento técnico para casos de puertas
        if f in clases_puertas or ("chapa" in f_lower or "puerta" in f_lower):
            palabras_electrico = [
                "control", "electrico", "eléctrico", "bloqueada",
                "desbloquea", "salta y no traba", "centralizado"
            ]
            if any(k in s for k in palabras_electrico):
                codigo = "CARROCERIA_001"
            else:
                codigo = "CARROCERIA_002"
        else:
            codigo = MAPA_UNIFICACION_ETIQUETAS.get(f)

        if codigo and codigo in CATALOGO_TAXONOMIA:
            estandar = CATALOGO_TAXONOMIA[codigo]
            codigos.append(codigo)
            fallas_estandar.append(estandar.falla_principal)
            sistemas.append(estandar.sistema)
            severidades.append(estandar.severidad)
            estados.append("valido")
        else:
            estados.append("sin_mapeo")

    filas_cuarentena = sum(1 for e in estados if e == "cuarentena")
    filas_sin_mapeo = sum(1 for e in estados if e == "sin_mapeo")

    # Filtrar solo las filas válidas mapeadas a la taxonomía
    serie_estados = pd.Series(estados, index=df.index)
    df_valido = df[serie_estados == "valido"].copy()
    df_valido["codigo_falla"] = codigos
    df_valido["falla_estandar"] = fallas_estandar
    df_valido["sistema"] = sistemas
    df_valido["severidad"] = severidades

    # 2. Detectar y resolver contradicciones (mismo síntoma idéntico con distintos códigos)
    agrupado = df_valido.groupby("sintoma_norm")["codigo_falla"].nunique()
    sintomas_contradictorios = agrupado[agrupado > 1].index.tolist()

    df_sin_contradicciones = (
        df_valido.groupby(["sintoma_norm", "codigo_falla"])
        .size()
        .reset_index(name="conteo")
        .sort_values(["sintoma_norm", "conteo"], ascending=[True, False])
        .drop_duplicates(subset=["sintoma_norm"], keep="first")
    )

    # 3. Eliminar duplicados exactos dentro de las filas válidas
    ganadores = df_sin_contradicciones[["sintoma_norm", "codigo_falla"]]
    df_resuelto = df_valido.merge(
        ganadores, on=["sintoma_norm", "codigo_falla"], how="inner"
    )
    filas_contradiccion_eliminadas = len(df_valido) - len(df_resuelto)
    filas_antes_dedup = len(df_resuelto)
    df_final = df_resuelto.drop_duplicates(
        subset=["sintoma_norm", "codigo_falla"]
    ).copy()
    duplicados_exactos_eliminados = filas_antes_dedup - len(df_final)

    # Reemplazar columna 'falla' por la falla_estandar para mantener compatibilidad
    df_final["falla"] = df_final["falla_estandar"]
    df_export = df_final[["sintoma", "falla", "codigo_falla", "sistema", "severidad"]].copy()

    df_export.to_csv(path_out, index=False, encoding="utf-8")

    # Calcular distribución por clase y conteo de familias independientes
    distribucion_clases = df_export["codigo_falla"].value_counts().to_dict()
    df_export["familia_sintoma"] = df_export["sintoma"].map(normalizar_grupo)
    familias_por_clase = (
        df_export.groupby("codigo_falla")["familia_sintoma"]
        .nunique()
        .to_dict()
    )
    df_export = df_export.drop(columns=["familia_sintoma"])

    clases_sin_mapeo = sorted(
        df.loc[serie_estados == "sin_mapeo", "falla"].astype(str).unique().tolist()
    )
    clases_cuarentena = sorted(
        df.loc[serie_estados == "cuarentena", "falla"].astype(str).unique().tolist()
    )

    reporte = {
        "filas_iniciales": filas_iniciales,
        "clases_iniciales": clases_iniciales,
        "filas_cuarentena_excluidas": filas_cuarentena,
        "filas_sin_mapeo": filas_sin_mapeo,
        "clases_sin_mapeo": len(clases_sin_mapeo),
        "detalle_clases_sin_mapeo": clases_sin_mapeo,
        "clases_en_cuarentena": len(clases_cuarentena),
        "detalle_clases_cuarentena": clases_cuarentena,
        "duplicados_exactos_eliminados": duplicados_exactos_eliminados,
        "sintomas_contradictorios_resueltos": len(sintomas_contradictorios),
        "filas_contradiccion_eliminadas": filas_contradiccion_eliminadas,
        "filas_finales": len(df_export),
        "clases_unificadas": df_export["codigo_falla"].nunique(),
        "sistemas_cubiertos": df_export["sistema"].nunique(),
        "distribucion_por_clase": distribucion_clases,
        "familias_por_clase": familias_por_clase,
        "catalogo_codigos": sorted(list(df_export["codigo_falla"].unique())),
    }

    path_reporte.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
    print("=" * 80)
    print("REPORTE DE LIMPIEZA Y NORMALIZACION DE TAXONOMIA ML")
    print("=" * 80)
    print(f"Filas iniciales:                     {filas_iniciales}")
    print(f"Clases iniciales en dataset:         {clases_iniciales}")
    print(f"Filas en cuarentena (DTC/genéricas): {filas_cuarentena}")
    print(f"Filas sin mapeo técnico:             {filas_sin_mapeo}")
    print(f"Duplicados exactos eliminados:       {duplicados_exactos_eliminados}")
    print(f"Filas limpias finales:               {len(df_export)}")
    print(f"Clases unificadas con código único:  {df_export['codigo_falla'].nunique()}")
    print(f"Sistemas automotrices cubiertos:     {df_export['sistema'].nunique()}")
    print(f"Contradicciones resueltas:           {len(sintomas_contradictorios)}")
    print(f"Archivo generado:                    {path_out}")
    print(f"Reporte de calidad guardado en:      {path_reporte}")
    print("=" * 80)


if __name__ == "__main__":
    limpiar_y_estructurar_dataset()
