"""Contrato único: documental tipos de RAG-03G."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Tuple


def normalizar_texto(texto: str) -> str:
    """Elimina diacríticos, convierte a minúsculas y colapsa espacios múltiples."""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFD", str(texto).lower())
    texto = "".join((c for c in texto if unicodedata.category(c) != "Mn"))
    return re.sub("\\s+", " ", texto).strip()


class EstadoDocumental(str, Enum):
    """Categorías canónicas de clasificación documental (C02 / A02)."""

    ESPECIFICACION_DOCUMENTADA = "ESPECIFICACION_DOCUMENTADA"
    PROCEDIMIENTO_ESPECIFICO_OEM = "PROCEDIMIENTO_ESPECIFICO_OEM"
    PROCEDIMIENTO_GENERAL = "PROCEDIMIENTO_GENERAL"
    INFORMACION_PARCIAL = "INFORMACION_PARCIAL"
    AUSENCIA_DOCUMENTACION = "AUSENCIA_DOCUMENTACION"
    VEHICULO_NO_CUBIERTO = "VEHICULO_NO_CUBIERTO"


@dataclass(frozen=True)
class VehiculoConsulta:
    """Representación normalizada y estructurada del vehículo consultado (A03)."""

    marca: Optional[str] = None
    modelo: Optional[str] = None
    anio: Optional[int] = None
    motor: Optional[str] = None
    mercado: Optional[str] = None

    @classmethod
    def extraer(cls, consulta: str, vehiculo_str: str = "") -> VehiculoConsulta:
        """Extrae la información vehicular estructurada desde el texto de la consulta o contexto."""
        texto_comb = normalizar_texto(f"{vehiculo_str} {consulta}")
        marca = None
        marcas_conocidas = [
            "hyundai",
            "kia",
            "toyota",
            "nissan",
            "honda",
            "mitsubishi",
            "chevrolet",
            "ford",
            "volkswagen",
            "suzuki",
            "fiat",
            "renault",
            "mazda",
            "subaru",
            "peugeot",
            "citroen",
            "byd",
            "chery",
            "geely",
            "brembo",
        ]
        for m in marcas_conocidas:
            if re.search(f"\\b{m}\\b", texto_comb):
                marca = m
                break
        modelo = None
        modelos_conocidos = [
            "elantra",
            "accent",
            "sonata",
            "tucson",
            "santa fe",
            "i10",
            "i20",
            "i30",
            "rio",
            "cerato",
            "forte",
            "optima",
            "sportage",
            "sorento",
            "picanto",
            "soul",
            "yaris",
            "corolla",
            "hilux",
            "rav4",
            "raize",
            "etios",
            "s-presso",
            "spresso",
            "swift",
            "vitara",
            "alto",
            "mobi",
            "argo",
            "cronos",
            "uno",
            "civic",
            "fit",
            "city",
            "cr-v",
            "crv",
            "sentra",
            "versa",
            "tiida",
            "kicks",
            "frontier",
            "golf",
            "jetta",
            "polo",
            "gol",
            "amarok",
            "sail",
            "onix",
            "cruze",
            "tracker",
        ]
        for mod in modelos_conocidos:
            if re.search(f"\\b{re.escape(mod)}\\b", texto_comb):
                modelo = mod.replace("-", "")
                break
        anio = None
        m_anio = re.search("\\b(19\\d\\d|20[0-2]\\d|2030)\\b", texto_comb)
        if m_anio:
            anio = int(m_anio.group(1))
        motor = None
        m_motor = re.search(
            "\\b(1\\.[0-9]|2\\.[0-9]|d4fb|g4fc|1nz(?:-fe)?|2nz(?:-fe)?|hr16de|valvematic|vvt-i|crdi|tsi|tdi|firefly)\\b",
            texto_comb,
        )
        if m_motor:
            motor = m_motor.group(1).upper()
        mercado = None
        if re.search("\\b(?:peru|latam|latinoamerica|sudamerica)\\b", texto_comb):
            mercado = "peru_latam"
        elif re.search("\\b(?:ee\\.?uu\\.?|usa|norteamerica|usdm|hma)\\b", texto_comb):
            mercado = "usa_norteamerica"
        elif re.search("\\b(?:japon|jdm)\\b", texto_comb):
            mercado = "japon"
        elif re.search("\\b(?:europa|ece)\\b", texto_comb):
            mercado = "europa"
        return cls(marca=marca, modelo=modelo, anio=anio, motor=motor, mercado=mercado)


@dataclass(frozen=True)
class TrazabilidadDocumental:
    """Trazabilidad física y formal de una especificación OEM."""

    fuente: str
    pagina: str
    paginas: List[int]
    componente: str
    marca_aplicable: Optional[str] = None
    modelos_aplicables: List[str] = field(default_factory=list)
    rango_anios: Optional[Tuple[int, int]] = None
    mercado_aplicable: Optional[str] = None
    cifra_encontrada: str = ""
    unidad: str = ""
    parametro: str = ""
    condicion: str = ""
    pagina_cifra: str = ""


@dataclass(frozen=True)
class DictamenDocumental:
    """Resultado del control documental previo a la emisión de respuesta técnica."""

    estado: EstadoDocumental
    autorizado_publicar_cifra: bool
    confianza_ml_maxima: float
    factor_relevancia: float
    trazabilidad: Optional[TrazabilidadDocumental]
    motivo: str


def parsear_referencias_paginas(pagina_input: Any) -> Tuple[bool, List[int], str]:
    """Parsea y valida referencias de páginas complejas (B-INT-02).

    Admite:
    - Enteros directos: 5 -> [5]
    - Cadenas con entero simple: "5" -> [5]
    - Rangos: "5-6", "8-9" -> [5, 6], [8, 9]
    - Listas separadas por coma: "7, 10, 14" -> [7, 10, 14]
    - Listas complejas con rangos: "3, 4, 5, 14", "3-4, 10, 16", "4, 10, 11-12, 16"
    - Listas o tuplas nativas de Python: [5, 6], ["7", "10", "14"]

    Retorna: (es_valido, lista_ordenada_enteros_unicos, representacion_estandar)
    """
    if pagina_input is None:
        return (False, [], "Referencia de página nula (None)")
    if isinstance(pagina_input, int):
        if pagina_input <= 0:
            return (False, [], f"Número de página inválido ({pagina_input} <= 0)")
        return (True, [pagina_input], str(pagina_input))
    if isinstance(pagina_input, (list, tuple)):
        items_str = []
        for x in pagina_input:
            items_str.append(str(x).strip())
        cadena = ", ".join(items_str)
    else:
        cadena = str(pagina_input).strip()
    if not cadena or cadena.lower() in ("none", "null", "", "nan"):
        return (False, [], "Referencia de página vacía o nula")
    partes = [p.strip() for p in re.split("[,;]+", cadena) if p.strip()]
    if not partes:
        return (False, [], "Referencia de página sin elementos identificables")
    paginas_detectadas: set[int] = set()
    for parte in partes:
        m_rango = re.match("^(\\d+)\\s*(?:-|–|—|a)\\s*(\\d+)$", parte)
        if m_rango:
            ini = int(m_rango.group(1))
            fin = int(m_rango.group(2))
            if ini <= 0 or fin <= 0:
                return (False, [], f"Rango con páginas <= 0: '{parte}'")
            if ini > fin:
                return (False, [], f"Rango invertido incoherente: '{parte}' ({ini} > {fin})")
            if fin - ini > 100:
                return (False, [], f"Rango excesivamente amplio (>100 páginas): '{parte}'")
            for p in range(ini, fin + 1):
                paginas_detectadas.add(p)
            continue
        if parte.isdigit():
            p_val = int(parte)
            if p_val <= 0:
                return (False, [], f"Página individual <= 0: '{parte}'")
            paginas_detectadas.add(p_val)
            continue
        m_prefijo = re.match(
            "^(?:p[aá]g\\.?|pp\\.?|p\\.)\\s*(\\d+)(?:\\s*(?:-|–|—|a)\\s*(\\d+))?$", parte, re.IGNORECASE
        )
        if m_prefijo:
            ini = int(m_prefijo.group(1))
            fin = int(m_prefijo.group(2)) if m_prefijo.group(2) else ini
            if ini <= 0 or fin <= 0 or ini > fin:
                return (False, [], f"Página con prefijo inválida: '{parte}'")
            for p in range(ini, fin + 1):
                paginas_detectadas.add(p)
            continue
        return (False, [], f"Formato de página no reconocido: '{parte}'")
    if not paginas_detectadas:
        return (False, [], "No se pudieron extraer páginas válidas")
    lista_ordenada = sorted(paginas_detectadas)
    rep_estandar = cadena.replace("–", "-").replace("—", "-")
    return (True, lista_ordenada, rep_estandar)


def parsear_rango_anios(anio_raw: Any) -> Optional[Tuple[int, int]]:
    """Convierte cadenas como '2011-2018' o enteros en una tupla (año_min, año_max)."""
    if anio_raw is None:
        return None
    if isinstance(anio_raw, int):
        return (anio_raw, anio_raw)
    s = str(anio_raw).strip()
    m_rango = re.match("^(\\d{4})\\s*(?:-|–|—|a)\\s*(\\d{4})$", s)
    if m_rango:
        return (int(m_rango.group(1)), int(m_rango.group(2)))
    m_simple = re.search("\\b(19\\d\\d|20[0-2]\\d)\\b", s)
    if m_simple:
        val = int(m_simple.group(1))
        return (val, val)
    return None
