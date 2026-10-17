"""
Puente al contrato y taxonomía canónica de Machine Learning (`machine_learning/models/taxonomia_sistemas.py`).
Garantiza que `carbot-machine-learning` sea la única fuente de verdad (Single Source of Truth)
para las 61 clases entrenadas, los 7 macro-sistemas, las subáreas técnicas y el contrato de inferencia,
manteniendo respaldo sincronizado para despliegues de contenedor aislados del backend.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[4]
_ML_TAXONOMY_PATH = _REPO_ROOT / "machine_learning" / "models" / "taxonomia_sistemas.py"


def _cargar_modulo_ml():
    if _ML_TAXONOMY_PATH.exists():
        spec = importlib.util.spec_from_file_location("ml_taxonomia_sistemas", str(_ML_TAXONOMY_PATH))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules["ml_taxonomia_sistemas"] = mod
            spec.loader.exec_module(mod)
            return mod
    return None


_ml_mod = _cargar_modulo_ml()

if _ml_mod is not None:
    MODEL_VERSION: str = _ml_mod.MODEL_VERSION
    TAXONOMY_VERSION: str = _ml_mod.TAXONOMY_VERSION
    TAXONOMIA_MACRO_SISTEMAS: Dict[str, List[str]] = _ml_mod.TAXONOMIA_MACRO_SISTEMAS
    FALLA_A_SISTEMA: Dict[str, str] = _ml_mod.FALLA_A_SISTEMA
    CLASS_ID_POR_FALLA: Dict[str, str] = _ml_mod.CLASS_ID_POR_FALLA
    FALLA_POR_CLASS_ID: Dict[str, str] = _ml_mod.FALLA_POR_CLASS_ID
    CLASES_ENTRENADAS_61: Tuple[str, ...] = _ml_mod.CLASES_ENTRENADAS_61
    SUBAREAS_POR_CLASE: Dict[str, Set[str]] = _ml_mod.SUBAREAS_POR_CLASE
    DTC_A_SISTEMA: Dict[str, Tuple[str, List[str]]] = _ml_mod.DTC_A_SISTEMA
    ContratoPrediccionML = _ml_mod.ContratoPrediccionML
    es_clase_entrenada_svm = _ml_mod.es_clase_entrenada_svm
    obtener_class_id = _ml_mod.obtener_class_id
    obtener_subareas_de_clase = _ml_mod.obtener_subareas_de_clase
    obtener_macro_sistema = _ml_mod.obtener_macro_sistema
    obtener_sistema_por_dtc = _ml_mod.obtener_sistema_por_dtc
    construir_contrato_prediccion = _ml_mod.construir_contrato_prediccion
else:  # pragma: no cover - Respaldo sincronizado únicamente para imagen Docker aislada sin carpeta machine_learning/models
    from dataclasses import asdict, dataclass

    MODEL_VERSION = "c1_fase10_final"
    TAXONOMY_VERSION = "61_clases_7_macrosistemas_v2"
    TAXONOMIA_MACRO_SISTEMAS = {
        "MOTOR": [
            "Falla en bujias o bobinas de encendido (misfire)",
            "Bomba de gasolina quemada o con baja presion",
            "Inyectores sucios o filtro de combustible obstruido",
            "Falla en sensor de oxigeno o mezcla rica",
            "Cuerpo de aceleracion o valvula IAC sucia",
            "Empaque de culata soplado o danado",
            "Falla en termostato o motoventilador de radiador",
            "Fuga en mangueras de refrigerante o radiador picado",
            "Consumo de aceite por desgaste de anillos o retenes",
            "Baja presion de aceite o bomba de aceite defectuosa",
            "Faja o cadena de distribucion destensada o con salto de punto",
            "Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)",
            "Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)",
            "Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI",
            "Fuga en mangueras de intercooler o turbocompresor danado",
            "Falla de correa dentada banada en aceite (Motor Ford 1.0 Dragon / GM Turbo)",
            "Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet)",
            "Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)",
            "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)",
            "Falla en sistema Flex / Bi-combustible (Alcohol/Etanol)",
            "Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)",
            "Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)",
            "Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)",
            "Falla en regulador de presion de combustible o diafragma roto",
            "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)",
            "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados",
        ],
        "FRENOS": [
            "Desgaste de pastillas y zapatas de freno",
            "Discos de freno alabeados o desgastados",
            "Falla en servofreno (booster) o linea de vacio",
            "Fuga hidraulica o aire en el sistema de frenos",
            "Falla en sensor de velocidad de rueda ABS",
            "Falla en sistema de frenado regenerativo (EV / Hibridos)",
            "Caliper de freno trabado o mordaza pegada (piston agarrotado)",
        ],
        "TRANSMISION": [
            "Disco de embrague desgastado o patinando",
            "Falla en bombin o bomba hidraulica de embrague",
            "Falta o degradacion de aceite de caja de cambios",
            "Rodajes de caja mecanica o diferencial gastados",
            "Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
            "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)",
            "Desgaste en collarin de empuje o crapodina de embrague",
            "Rodajes de transmision manual o eje primario gastados",
        ],
        "SUSPENSION_CHASIS": [
            "Amortiguadores reventados o bujes de suspension gastados",
            "Juntas homocineticas o palieres danados",
            "Llantas desbalanceadas o desalineadas",
            "Cremallera de direccion asistida con holgura o fuga",
            "Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura)",
        ],
        "ELECTRICO": [
            "Alternador defectuoso o placa de diodos quemada",
            "Bateria descargada o bornes sulfatados",
            "Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)",
            "Fallo en inversor de corriente IGBT o motor electrico (EV)",
            "Foco o falla en sistema de refrigeracion de bateria/inversor (EV)",
            "Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)",
            "Fuga parasita de corriente en reposo (consumo nocturno de bateria)",
        ],
        "CLIMATIZACION": [
            "Falla en compresor de aire acondicionado o fuga de gas R134a",
        ],
        "CARROCERIA_NEUMATICA": [
            "Falla electrica del cierre centralizado o actuador de puerta",
            "Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado",
            "Elevalunas electrico o guaya de alzacristales rota o trabada",
            "Limpiaparabrisas o motor pluma quemado",
            "Fugas de aire o fallos en el sistema de frenos neumático (Camiones)",
            "Válvula de freno de aire o secador APS obstruido (Camiones)",
            "Falla en actuador de resorte o camara Maxi-Brake trabada (frenos de aire)",
        ],
    }
    FALLA_A_SISTEMA = {f: s for s, fs in TAXONOMIA_MACRO_SISTEMAS.items() for f in fs}
    CLASS_ID_POR_FALLA = {f: f"C{idx:02d}" for idx, f in enumerate(FALLA_A_SISTEMA.keys(), 1)}
    FALLA_POR_CLASS_ID = {cid: f for f, cid in CLASS_ID_POR_FALLA.items()}
    CLASES_ENTRENADAS_61 = tuple(FALLA_A_SISTEMA.keys())
    SUBAREAS_POR_CLASE = {}
    DTC_A_SISTEMA = {}

    @dataclass(frozen=True)
    class ContratoPrediccionML:
        model_version: str
        taxonomy_version: str
        class_id: str
        class_label: str
        subsystem: str
        top_k: List[Dict[str, Any]]
        raw_svm_score: float
        calibrated_probability: float
        prediction_source: str
        abstention_reason: Optional[str] = None

        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)

    def es_clase_entrenada_svm(falla: str) -> bool:
        return str(falla or "").strip() in FALLA_A_SISTEMA

    def obtener_class_id(falla: str) -> str:
        return CLASS_ID_POR_FALLA.get(str(falla or "").strip(), "HIPOTESIS_REGLA")

    def obtener_subareas_de_clase(falla: str) -> Set[str]:
        return set()

    def obtener_macro_sistema(falla: str) -> str:
        return FALLA_A_SISTEMA.get(falla, "MOTOR")

    def obtener_sistema_por_dtc(codigo_dtc: str) -> Optional[Tuple[str, List[str]]]:
        return None

    def construir_contrato_prediccion(**kwargs: Any) -> ContratoPrediccionML:
        return ContratoPrediccionML(
            model_version=MODEL_VERSION,
            taxonomy_version=TAXONOMY_VERSION,
            class_id=obtener_class_id(kwargs.get("class_label", "")),
            class_label=str(kwargs.get("class_label", "")),
            subsystem=obtener_macro_sistema(str(kwargs.get("class_label", ""))),
            top_k=list(kwargs.get("top_k") or []),
            raw_svm_score=float(kwargs.get("raw_svm_score", 0.0)),
            calibrated_probability=float(kwargs.get("calibrated_probability", 0.0)),
            prediction_source=str(kwargs.get("prediction_source", "SVM")),
            abstention_reason=kwargs.get("abstention_reason"),
        )
