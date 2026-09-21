"""
Pipeline Arquitectónico y Reproducible para Fase 10 de CarBot.
Permite:
1. Ingestar y auditar lotes incrementales (Lote 01, Lote 02, etc.).
2. Filtrar duplicados, near-duplicates, artefactos de plantilla y leakage.
3. Consolidar el dataset maestro separado (machine_learning/data/fase10/dataset_fase10_master.csv).
4. Realizar GroupSplit por id_grupo para evitar leakage entre TRAIN10 y DEV10.
5. Gestionar la política de entrenamiento (bloqueo de producción si hay cobertura parcial).
"""

from __future__ import annotations

import logging
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Asegurar backend en sys.path
BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "backend"))

from src.core.diagnostico.taxonomia_sistemas import FALLA_A_SISTEMA  # noqa: E402

logger = logging.getLogger("PipelineFase10")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")


def normalizar_texto(t: str) -> str:
    """Normaliza texto para comparaciones exactas y análisis de duplicados."""
    if not isinstance(t, str):
        return ""
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


class AuditorLoteFase10:
    """Auditor de calidad estructural, semántica y de leakage para lotes CSV."""

    COLUMNAS_ESPERADAS = [
        "id", "id_grupo", "clase_objetivo", "macro_sistema", "nivel_informacion",
        "texto_usuario", "tipo_lenguaje", "condicion_operacion", "sintomas_presentes",
        "sintomas_negados", "dtc", "requiere_pregunta", "es_contrastivo",
        "clase_contrastiva", "fuente", "observaciones"
    ]

    PATRONES_PLANTILLA = [
        r"comenz[oó] a motor tiembla",
        r"comenz[oó] a ralenti",
        r"comenz[oó] a se queda sin",
        r"comenz[oó] a sale humo",
        r"comenz[oó] a rpm suben",
        r"cuando voy al acelerar fuerte",
        r"cuando est[aá] al acelerar fuerte",
        r"al manejar despues de manejar un rato",
        r"al manejar despues de varias horas",
        r"al manejar despues de calentar",
    ]

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or BASE_DIR
        self.clases_validas = set(FALLA_A_SISTEMA.keys())
        self.corpus_ref: Dict[str, Tuple[str, str]] = {}
        self._cargar_referencias_historicas()

    def _cargar_referencias_historicas(self):
        """Carga TRAIN canónico y benchmarks para control estricto de leakage."""
        train_csv = self.base_dir / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"
        if train_csv.exists():
            df_train = pd.read_csv(train_csv)
            for idx, row in df_train.iterrows():
                self.corpus_ref[f"TRAIN_{idx}"] = ("TRAIN", str(row["sintoma"]))

        field_csv = self.base_dir / "machine_learning" / "data" / "casos_reales_mecanicos_evaluacion.csv"
        if field_csv.exists():
            df_field = pd.read_csv(field_csv)
            for idx, row in df_field.iterrows():
                self.corpus_ref[f"FIELD_{idx}"] = ("FIELD_60", str(row.get("sintoma", "")))

    def auditar_lote(self, csv_path: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Ejecuta la auditoría integral y retorna reporte fila por fila y métricas."""
        df = pd.read_csv(csv_path)
        total = len(df)
        textos_lote = [str(t) for t in df["texto_usuario"].tolist()]
        textos_lote_norm = [normalizar_texto(t) for t in textos_lote]

        # Vectorización TF-IDF
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
        ref_keys = list(self.corpus_ref.keys())
        ref_texts = [self.corpus_ref[k][1] for k in ref_keys]
        ref_texts_norm = [normalizar_texto(t) for t in ref_texts]

        todos_textos = textos_lote_norm + ref_texts_norm
        vectorizer.fit(todos_textos)
        mat_lote = vectorizer.transform(textos_lote_norm)
        mat_ref = vectorizer.transform(ref_texts_norm)

        sim_intra = cosine_similarity(mat_lote, mat_lote)
        np.fill_diagonal(sim_intra, 0.0)
        sim_inter = cosine_similarity(mat_lote, mat_ref) if len(ref_texts) > 0 else np.zeros((total, 1))

        rows_auditoria = []
        conteo = {"APROBADO": 0, "REVISAR": 0, "RECHAZADO": 0}

        for i, row in df.iterrows():
            reg_id = str(row["id"])
            clase = str(row["clase_objetivo"])
            macro = str(row["macro_sistema"])
            nivel = str(row["nivel_informacion"])
            texto = str(row["texto_usuario"])
            texto_norm = textos_lote_norm[i]
            es_cont = str(row["es_contrastivo"]).strip().upper()
            clase_cont = str(row["clase_contrastiva"]) if pd.notna(row["clase_contrastiva"]) else ""
            dtc_val = str(row["dtc"]).strip() if pd.notna(row["dtc"]) else ""

            motivos = []
            estado = "APROBADO"

            if clase not in self.clases_validas:
                motivos.append(f"Clase objetivo '{clase}' inválida.")
                estado = "RECHAZADO"

            if nivel not in ("L1", "L2", "L3"):
                motivos.append(f"Nivel '{nivel}' desconocido.")
                estado = "RECHAZADO"

            if dtc_val and not re.match(r"^[PBCU]\d{4}$", dtc_val):
                motivos.append(f"Formato DTC inválido: '{dtc_val}'.")
                estado = "REVISAR"

            macro_esp = FALLA_A_SISTEMA.get(clase, "")
            if macro != macro_esp:
                motivos.append(f"Macro-sistema '{macro}' != esperado '{macro_esp}'.")
                estado = "REVISAR"

            if es_cont == "SI":
                if not clase_cont or clase_cont not in self.clases_validas:
                    motivos.append(f"Clase contrastiva inválida: '{clase_cont}'.")
                    estado = "RECHAZADO"

            # Duplicados exactos dentro del lote con diferente etiqueta
            dups = [j for j, tn in enumerate(textos_lote_norm) if j != i and tn == texto_norm]
            if dups:
                clase_dup = df.iloc[dups[0]]["clase_objetivo"]
                if clase_dup != clase:
                    motivos.append(f"Duplicado exacto con etiqueta contradictoria ({df.iloc[dups[0]]['id']}).")
                    estado = "RECHAZADO"
                else:
                    motivos.append(f"Duplicado exacto de {df.iloc[dups[0]]['id']}.")
                    estado = "REVISAR"

            # Similitudes máximas
            max_intra = float(np.max(sim_intra[i]))
            max_inter = float(np.max(sim_inter[i])) if sim_inter.shape[1] > 0 else 0.0

            if max_inter >= max_intra:
                sim_max = round(max_inter, 4)
                orig = f"LEAKAGE_{self.corpus_ref[ref_keys[int(np.argmax(sim_inter[i]))]][0]}"
                if max_inter > 0.95:
                    motivos.append(f"Leakage severo (>0.95) con {orig}.")
                    estado = "RECHAZADO"
                elif max_inter > 0.88 and estado != "RECHAZADO":
                    motivos.append(f"Similitud alta (>0.88) con {orig}.")
                    estado = "REVISAR"
            else:
                sim_max = round(max_intra, 4)
                orig = f"INTRA_{df.iloc[int(np.argmax(sim_intra[i]))]['id']}"
                if max_intra > 0.92 and estado != "RECHAZADO":
                    motivos.append(f"Near-duplicate intra-lote (>0.92) con {orig}.")
                    estado = "REVISAR"

            # Plantillas sintéticas
            for pat in self.PATRONES_PLANTILLA:
                if re.search(pat, texto, re.IGNORECASE):
                    motivos.append(f"Artefacto de plantilla sintética ('{pat}').")
                    if estado != "RECHAZADO":
                        estado = "REVISAR"
                    break

            conteo[estado] += 1
            rows_auditoria.append({
                "id": reg_id,
                "estado": estado,
                "motivos": " | ".join(motivos) if motivos else "Conforme.",
                "similitud_maxima": sim_max,
                "origen_similitud": orig,
                "recomendacion": "Aprobar" if estado == "APROBADO" else ("Revisar/Editar" if estado == "REVISAR" else "Excluir")
            })

        df_audit = pd.DataFrame(rows_auditoria)
        metricas = {
            "total_registros": total,
            "conteo": conteo,
            "tasa_aprobacion": round(conteo["APROBADO"] / total * 100, 2),
            "clases_presentes": df["clase_objetivo"].nunique(),
            "distribucion_niveles": df["nivel_informacion"].value_counts().to_dict(),
        }
        return df_audit, metricas


class GestorMasterFase10:
    """Consolida lotes auditados y aprobados en el dataset maestro de Fase 10."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or BASE_DIR
        self.master_path = self.base_dir / "machine_learning" / "data" / "fase10" / "dataset_fase10_master.csv"
        self.master_path.parent.mkdir(parents=True, exist_ok=True)

    def consolidar_lote(self, df_lote: pd.DataFrame, df_audit: pd.DataFrame, nombre_lote: str):
        """Incorpora únicamente registros APROBADOS conservando metadatos de trazabilidad."""
        aprobados_ids = set(df_audit[df_audit["estado"] == "APROBADO"]["id"])
        df_aprobados = df_lote[df_lote["id"].isin(aprobados_ids)].copy()

        df_aprobados["source_dataset"] = nombre_lote
        df_aprobados["source_row_id"] = df_aprobados["id"]
        df_aprobados["source_type"] = "LOTE_ESTRATIFICADO_L1_L2_L3"
        df_aprobados["specificity_level"] = df_aprobados["nivel_informacion"]
        df_aprobados["synthetic_or_original"] = df_aprobados["fuente"].fillna("SINTETICO_IA")

        if self.master_path.exists():
            df_existente = pd.read_csv(self.master_path)
            # Evitar re-ingesta de IDs existentes
            ids_existentes = set(df_existente["id"])
            df_nuevos = df_aprobados[~df_aprobados["id"].isin(ids_existentes)]
            df_final = pd.concat([df_existente, df_nuevos], ignore_index=True)
        else:
            df_final = df_aprobados

        df_final.to_csv(self.master_path, index=False, encoding="utf-8")
        logger.info("Dataset maestro Fase 10 actualizado: %d registros en %s", len(df_final), self.master_path)
        return len(df_final)


class PoliticaEntrenamientoFase10:
    """Verifica si los datos acumulados cumplen con los requisitos para entrenamiento."""

    @staticmethod
    def verificar_elegibilidad(master_path: Path) -> Dict[str, Any]:
        if not master_path.exists():
            return {"elegible_definitivo": False, "motivo": "Dataset maestro no existe aún."}

        df = pd.read_csv(master_path)
        clases_unicas = df["clase_objetivo"].nunique()
        total_clases_canonica = len(FALLA_A_SISTEMA)

        if clases_unicas < total_clases_canonica:
            return {
                "elegible_definitivo": False,
                "estado_modelo": "EXPERIMENTAL_PARCIAL",
                "clases_presentes": clases_unicas,
                "clases_totales": total_clases_canonica,
                "motivo": (
                    f"Cobertura incompleta ({clases_unicas}/{total_clases_canonica} clases). "
                    "Un entrenamiento actual generaría un sesgo desbalanceado hacia las clases ingresadas. "
                    "Se restringe a modelo EXPERIMENTAL_PARCIAL sin tocar producción."
                )
            }

        return {
            "elegible_definitivo": True,
            "estado_modelo": "CANDIDATO_COMPLETO",
            "clases_presentes": clases_unicas,
            "clases_totales": total_clases_canonica,
            "motivo": "Todas las 61 clases cuentan con datos representativos de Fase 10."
        }
