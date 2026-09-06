"""Genera un dataset candidato y auditable a partir de dos guias de GemaCar.

El resultado modela relaciones multicausa para revision mecanica y uso futuro en
RAG. No modifica el dataset de entrenamiento ni convierte una causa posible en
un diagnostico confirmado.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = DATA_DIR / "candidatos_revision"

FUENTES = {
    "fallas_comunes": {
        "titulo": "Fallas comunes del auto: guia para diagnosticar sintomas, causas y que revisar",
        "url": "https://gemacar.com/blog/fallas-comunes-auto/",
        "sha256": "88cb512affaf6573b6d81bb1a5e172192c0c1e9c761255bbba78c6ab591669d6",
    },
    "perdida_potencia": {
        "titulo": "Perdida de potencia del motor: causas comunes y que revisar primero",
        "url": "https://gemacar.com/blog/perdida-de-potencia-del-motor/",
        "sha256": "da91396c7ac7fd5669b4b4ae809a0ebc8649d6197dcf91b104f669a7498fc4f1",
    },
}


@dataclass(frozen=True)
class Grupo:
    fuente: str
    seccion: str
    sintoma: str
    condicion: str
    revision: str
    pregunta: str
    urgencia: str
    sistema: str
    causas: tuple[tuple[str, str, str], ...]


def causa(nombre: str, codigo: str = "", estado: str = "") -> tuple[str, str, str]:
    if not estado:
        estado = "MAPEO_PROPUESTO" if codigo else "SIN_CLASE_CANONICA"
    return nombre, codigo, estado


GRUPOS: tuple[Grupo, ...] = (
    Grupo(
        "fallas_comunes",
        "El auto no arranca",
        "el auto no arranca",
        "al girar la llave o pulsar el boton de encendido",
        "Revisar luces, bornes y sonido al intentar arrancar.",
        "¿El motor gira, solo hace clic o no enciende ninguna luz?",
        "ALTA",
        "Sistema electrico y combustible",
        (
            causa("bateria descargada", "ELECTRICO_002"),
            causa("bornes sulfatados o flojos", "ELECTRICO_002"),
            causa("alternador que no carga", "ELECTRICO_001"),
            causa("motor de arranque defectuoso"),
            causa("fusible quemado"),
            causa("problema de llave, inmovilizador o alarma"),
            causa("falta de combustible", estado="REQUIERE_DESCARTE"),
            causa("bomba de gasolina defectuosa", "COMBUSTIBLE_002"),
        ),
    ),
    Grupo(
        "fallas_comunes",
        "Check engine",
        "se enciende la luz check engine",
        "con el motor encendido",
        "Leer codigos OBD2 y comprobar si la luz esta fija o parpadea.",
        "¿La luz esta fija o parpadea?",
        "MEDIA_ALTA",
        "Motor, emisiones y combustible",
        (
            causa("tapa de combustible floja o dañada"),
            causa("sensor de oxigeno defectuoso", "COMBUSTIBLE_004"),
            causa("bujias o bobinas en mal estado", "MOTOR_001"),
            causa("mezcla incorrecta de aire y combustible", "COMBUSTIBLE_004"),
            causa("catalizador con problema"),
            causa("sensor de motor defectuoso"),
            causa("fuga de vacio"),
            causa("problema del sistema de emisiones"),
        ),
    ),
    Grupo(
        "fallas_comunes",
        "Motor recalentado",
        "el motor se calienta",
        "durante la marcha o en trafico",
        "Comprobar temperatura y refrigerante solo con el motor frio.",
        "¿Sube la temperatura, pierde refrigerante o sale vapor?",
        "ALTA",
        "Refrigeracion y motor",
        (
            causa("nivel bajo de refrigerante", "REFRIGERACION_002"),
            causa("fuga de refrigerante", "REFRIGERACION_002"),
            causa("radiador obstruido o dañado"),
            causa("motoventilador que no enciende", "REFRIGERACION_001"),
            causa("termostato trabado", "REFRIGERACION_001"),
            causa("bomba de agua defectuosa"),
            causa("tapa de radiador dañada"),
            causa("aceite bajo o degradado", estado="REQUIERE_REVISION_AMBIGUEDAD"),
        ),
    ),
    Grupo(
        "fallas_comunes",
        "El auto se apaga solo",
        "el auto se apaga solo",
        "en minimo, en marcha, al frenar o al acelerar",
        "Precisar cuando se apaga y revisar combustible, carga y admision.",
        "¿Se apaga en minimo, al frenar, al acelerar o despues de calentarse?",
        "ALTA",
        "Combustible, electrico y admision",
        (
            causa("bomba de gasolina debil", "COMBUSTIBLE_002"),
            causa("filtro de combustible obstruido", "COMBUSTIBLE_001"),
            causa("alternador defectuoso", "ELECTRICO_001"),
            causa("conexion deficiente de bateria", "ELECTRICO_002"),
            causa("sensor de cigüeñal defectuoso"),
            causa("sensor de arbol de levas defectuoso"),
            causa("cuerpo de aceleracion sucio", "COMBUSTIBLE_003"),
            causa("valvula IAC sucia o defectuosa", "COMBUSTIBLE_003"),
            causa("fuga de vacio"),
        ),
    ),
    Grupo(
        "fallas_comunes",
        "Bateria descargada",
        "la bateria se descarga con frecuencia",
        "con el vehiculo apagado o despues de trayectos cortos",
        "Medir bateria, carga del alternador, bornes y consumo en reposo.",
        "¿Se descarga aun despues de cargarla o cambiarla?",
        "MEDIA_ALTA",
        "Sistema electrico",
        (
            causa("bateria envejecida", "ELECTRICO_002"),
            causa("luces o accesorios quedaron encendidos", estado="REQUIERE_DESCARTE"),
            causa("alternador que no carga", "ELECTRICO_001"),
            causa("bornes sucios o flojos", "ELECTRICO_002"),
            causa("consumo electrico parasitario"),
            causa("trayectos demasiado cortos", estado="REQUIERE_DESCARTE"),
            causa("degradacion por calor", "ELECTRICO_002", "REQUIERE_REVISION_AMBIGUEDAD"),
        ),
    ),
    Grupo(
        "fallas_comunes",
        "Alternador en mal estado",
        "hay luz de bateria, luces debiles o apagones",
        "con el motor en funcionamiento",
        "Medir voltaje de bateria y carga del alternador.",
        "¿Las luces se debilitan o el auto se apaga con el motor encendido?",
        "ALTA",
        "Sistema electrico",
        (causa("alternador defectuoso", "ELECTRICO_001"),),
    ),
    Grupo(
        "fallas_comunes",
        "Perdida de potencia",
        "el auto pierde fuerza",
        "al acelerar o subir pendientes",
        "Revisar filtro de aire, respuesta al acelerar y codigos OBD2.",
        "¿Pierde fuerza al acelerar, en subida o en ambos casos?",
        "MEDIA_ALTA",
        "Motor, combustible y transmision",
        (
            causa("filtro de aire sucio"),
            causa("filtro de combustible obstruido", "COMBUSTIBLE_001"),
            causa("bujias desgastadas", "MOTOR_001"),
            causa("bobinas defectuosas", "MOTOR_001"),
            causa("inyectores sucios", "COMBUSTIBLE_001"),
            causa("sensor MAF o MAP defectuoso"),
            causa("catalizador obstruido"),
            causa("problema de transmision", estado="REQUIERE_REVISION_AMBIGUEDAD"),
            causa("combustible de mala calidad", estado="REQUIERE_DESCARTE"),
        ),
    ),
    Grupo(
        "fallas_comunes",
        "Consumo excesivo",
        "el auto consume demasiado combustible",
        "comparado con su consumo habitual",
        "Comparar consumo y revisar mantenimiento y presion de neumaticos.",
        "¿Aumento el consumo junto con tirones, humo o perdida de fuerza?",
        "MEDIA",
        "Combustible, motor y rodaje",
        (
            causa("filtro de aire sucio"),
            causa("bujias en mal estado", "MOTOR_001"),
            causa("sensor de oxigeno defectuoso", "COMBUSTIBLE_004"),
            causa("inyectores sucios", "COMBUSTIBLE_001"),
            causa("presion baja de neumaticos", estado="REQUIERE_DESCARTE"),
            causa("aceite incorrecto", estado="REQUIERE_DESCARTE"),
            causa("frenos pegados"),
            causa("manejo agresivo", estado="REQUIERE_DESCARTE"),
            causa("exceso de peso", estado="REQUIERE_DESCARTE"),
        ),
    ),
    Grupo(
        "fallas_comunes",
        "Humo blanco",
        "sale humo blanco por el escape",
        "de forma persistente con el motor caliente",
        "Comprobar perdida de refrigerante y temperatura.",
        "¿El humo desaparece al calentar o sigue siendo denso?",
        "ALTA",
        "Motor y refrigeracion",
        (
            causa("refrigerante entrando al motor", "MOTOR_003"),
            causa("empaque de culata dañado", "MOTOR_003"),
        ),
    ),
    Grupo(
        "fallas_comunes",
        "Vapor blanco en frio",
        "sale vapor blanco leve por el escape",
        "solo al encender en frio y desaparece",
        "Observar si desaparece al alcanzar temperatura normal.",
        "¿Desaparece pocos minutos despues del arranque?",
        "BAJA",
        "Escape",
        (causa("condensacion normal", estado="DESCARTAR_NO_FALLA"),),
    ),
    Grupo(
        "fallas_comunes",
        "Humo azul",
        "sale humo azul por el escape",
        "al acelerar o de forma constante",
        "Revisar nivel y consumo de aceite.",
        "¿Baja el nivel de aceite entre servicios?",
        "MEDIA_ALTA",
        "Motor",
        (causa("aceite quemado por desgaste o sellos", "MOTOR_002"),),
    ),
    Grupo(
        "fallas_comunes",
        "Humo negro",
        "sale humo negro por el escape",
        "al acelerar o bajo carga",
        "Revisar mezcla, filtro de aire, inyectores y sensores.",
        "¿El humo aparece al acelerar y aumento el consumo?",
        "MEDIA_ALTA",
        "Combustible y motor",
        (
            causa("mezcla rica de combustible", "COMBUSTIBLE_004"),
            causa("filtro de aire muy sucio"),
            causa("inyectores defectuosos", "COMBUSTIBLE_001", "REQUIERE_REVISION_AMBIGUEDAD"),
            causa("sensor de mezcla defectuoso", "COMBUSTIBLE_004"),
        ),
    ),
    Grupo(
        "fallas_comunes",
        "Ruidos al conducir",
        "se escucha un ruido nuevo en el auto",
        "al frenar, pasar baches, rodar, girar o acelerar",
        "Identificar origen, tipo de ruido y momento en que aparece.",
        "¿Suena al frenar, girar, acelerar o pasar un bache?",
        "MEDIA_ALTA",
        "Frenos, suspension, direccion y motor",
        (
            causa("pastillas de freno gastadas", "FRENO_001"),
            causa("bujes o suspension desgastados", "SUSPENSION_001"),
            causa("rodamiento o neumatico defectuoso"),
            causa("correa floja o desgastada"),
            causa("bajo aceite o daño interno de motor", "MOTOR_004", "REQUIERE_REVISION_AMBIGUEDAD"),
            causa("direccion, junta homocinetica o suspension", estado="REQUIERE_REVISION_AMBIGUEDAD"),
        ),
    ),
    Grupo(
        "fallas_comunes",
        "Vibracion a velocidad",
        "el auto vibra al manejar",
        "a una velocidad determinada",
        "Revisar balanceo, alineacion, neumaticos y rines.",
        "¿Vibra a cierta velocidad, al frenar o tambien detenido?",
        "MEDIA",
        "Suspension y rodaje",
        (
            causa("neumaticos desbalanceados", "SUSPENSION_004"),
            causa("rin doblado"),
            causa("neumatico deformado", "SUSPENSION_004", "REQUIERE_REVISION_AMBIGUEDAD"),
            causa("falta de alineacion", "SUSPENSION_004"),
        ),
    ),
    Grupo(
        "fallas_comunes",
        "Vibracion al frenar",
        "el auto o el pedal vibra al frenar",
        "durante el frenado",
        "Inspeccionar discos y componentes del sistema de frenos.",
        "¿La vibracion aparece solo al pisar el freno?",
        "MEDIA_ALTA",
        "Frenos",
        (causa("discos de freno deformados", "FRENO_003"),),
    ),
    Grupo(
        "fallas_comunes",
        "Vibracion en minimo",
        "el motor vibra estando detenido",
        "en minimo o ralenti",
        "Revisar soportes y descartar falla de combustion.",
        "¿Vibra detenido y cambia al acelerar?",
        "MEDIA",
        "Motor y soportes",
        (
            causa("soporte de motor dañado"),
            causa("falla de combustion", "MOTOR_001", "REQUIERE_REVISION_AMBIGUEDAD"),
        ),
    ),
    Grupo(
        "fallas_comunes",
        "Vibracion en marcha",
        "el vehiculo vibra durante la marcha",
        "al acelerar o cambiar de carga",
        "Revisar ejes, juntas homocineticas y suspension.",
        "¿Se siente en el volante, asiento o en todo el vehiculo?",
        "MEDIA_ALTA",
        "Suspension y transmision",
        (
            causa("junta homocinetica o palier desgastado", "SUSPENSION_002"),
            causa("componente de suspension desgastado", "SUSPENSION_001"),
        ),
    ),
    Grupo(
        "fallas_comunes",
        "Fuga de liquido",
        "hay una fuga de liquido debajo del auto",
        "despues de estacionar",
        "Identificar color, ubicacion y variacion del nivel.",
        "¿De que color es el liquido y debajo de que zona aparece?",
        "MEDIA_ALTA",
        "Motor, frenos, refrigeracion y transmision",
        (
            causa("fuga de aceite de motor"),
            causa("fuga de refrigerante", "REFRIGERACION_002"),
            causa("fuga de fluido de transmision", "TRANSMISION_003", "REQUIERE_REVISION_AMBIGUEDAD"),
            causa("agua limpia del aire acondicionado", estado="DESCARTAR_NO_FALLA"),
            causa("fuga de liquido de frenos", "FRENO_002"),
        ),
    ),
    Grupo(
        "fallas_comunes",
        "Distribucion",
        "hay ruido, fallas o perdida de sincronizacion",
        "cerca de la correa de distribucion",
        "Comprobar historial, kilometraje y sincronizacion sin desmontar a ciegas.",
        "¿La correa supero su intervalo o hay ruido en esa zona?",
        "ALTA",
        "Motor",
        (causa("correa de distribucion desgastada o fuera de punto", "MOTOR_005"),),
    ),
    Grupo(
        "perdida_potencia",
        "Causas comunes de perdida de potencia",
        "el motor pierde potencia",
        "de forma general",
        "Leer codigos y revisar aire, encendido, combustible, escape y transmision.",
        "¿Ocurre al acelerar, subir, en caliente o todo el tiempo?",
        "MEDIA_ALTA",
        "Motor, combustible, escape y transmision",
        (
            causa("filtro de aire sucio"),
            causa("inyectores sucios", "COMBUSTIBLE_001"),
            causa("cuerpo de aceleracion sucio", "COMBUSTIBLE_003"),
            causa("sensor MAF o MAP defectuoso"),
            causa("bujias gastadas", "MOTOR_001"),
            causa("bobinas defectuosas", "MOTOR_001"),
            causa("bomba de gasolina debil", "COMBUSTIBLE_002"),
            causa("filtro de combustible obstruido", "COMBUSTIBLE_001"),
            causa("catalizador obstruido"),
            causa("sensor de oxigeno defectuoso", "COMBUSTIBLE_004"),
            causa("fuga de vacio"),
            causa("problema de transmision", estado="REQUIERE_REVISION_AMBIGUEDAD"),
            causa("bajo voltaje o falla electrica", estado="REQUIERE_REVISION_AMBIGUEDAD"),
            causa("motor sobrecalentado", estado="REQUIERE_REVISION_AMBIGUEDAD"),
        ),
    ),
    Grupo(
        "perdida_potencia",
        "Perdida de potencia al acelerar",
        "el auto pierde potencia al acelerar",
        "al pisar el acelerador",
        "Revisar admision, encendido, combustible, escape y entrega de transmision.",
        "¿Da tirones, suben las revoluciones o se ahoga?",
        "MEDIA_ALTA",
        "Motor, combustible y transmision",
        (
            causa("filtro de aire sucio"),
            causa("sensor MAF o MAP defectuoso"),
            causa("bujias gastadas", "MOTOR_001"),
            causa("bobinas defectuosas", "MOTOR_001"),
            causa("inyectores sucios", "COMBUSTIBLE_001"),
            causa("presion de combustible insuficiente", "COMBUSTIBLE_002", "REQUIERE_REVISION_AMBIGUEDAD"),
            causa("cuerpo de aceleracion sucio", "COMBUSTIBLE_003"),
            causa("catalizador obstruido"),
            causa("problema de transmision", estado="REQUIERE_REVISION_AMBIGUEDAD"),
        ),
    ),
    Grupo(
        "perdida_potencia",
        "Perdida de potencia en subida",
        "el auto pierde fuerza en subidas",
        "bajo carga o en pendientes",
        "Medir combustible y revisar encendido, escape, transmision y compresion.",
        "¿Falla solo en subida o tambien al acelerar en plano?",
        "MEDIA_ALTA",
        "Motor, combustible y transmision",
        (
            causa("bomba de gasolina debil", "COMBUSTIBLE_002"),
            causa("filtro de combustible obstruido", "COMBUSTIBLE_001"),
            causa("catalizador obstruido"),
            causa("bujias o bobinas defectuosas", "MOTOR_001"),
            causa("inyectores sucios", "COMBUSTIBLE_001"),
            causa("problema de transmision", estado="REQUIERE_REVISION_AMBIGUEDAD"),
            causa("baja compresion del motor"),
        ),
    ),
    Grupo(
        "perdida_potencia",
        "Perdida de potencia con humo negro",
        "el auto pierde potencia y bota humo negro",
        "al acelerar o bajo carga",
        "Revisar mezcla, admision, encendido, inyeccion y escape.",
        "¿El humo aparece al acelerar y aumento el consumo?",
        "ALTA",
        "Combustible, motor y escape",
        (
            causa("inyectores goteando", "COMBUSTIBLE_001", "REQUIERE_REVISION_AMBIGUEDAD"),
            causa("sensor MAF o MAP defectuoso"),
            causa("sensor de oxigeno defectuoso", "COMBUSTIBLE_004"),
            causa("filtro de aire muy sucio"),
            causa("bujias defectuosas", "MOTOR_001"),
            causa("bobinas defectuosas", "MOTOR_001"),
            causa("mezcla rica", "COMBUSTIBLE_004"),
            causa("catalizador afectado"),
        ),
    ),
    Grupo(
        "perdida_potencia",
        "Perdida de potencia y consumo alto",
        "el auto pierde potencia y consume mas combustible",
        "en uso habitual",
        "Revisar encendido, inyeccion, admision, sensores, escape y frenos.",
        "¿Tambien hay tirones, humo negro o check engine?",
        "MEDIA_ALTA",
        "Combustible, motor, escape y frenos",
        (
            causa("bujias gastadas", "MOTOR_001"),
            causa("inyectores sucios", "COMBUSTIBLE_001"),
            causa("filtro de aire sucio"),
            causa("sensor de oxigeno defectuoso", "COMBUSTIBLE_004"),
            causa("sensor MAF o MAP defectuoso"),
            causa("cuerpo de aceleracion sucio", "COMBUSTIBLE_003"),
            causa("catalizador obstruido"),
            causa("frenos pegados"),
            causa("trafico, clima o habito de manejo", estado="REQUIERE_DESCARTE"),
        ),
    ),
    Grupo(
        "perdida_potencia",
        "Perdida de potencia sin check engine",
        "el auto pierde potencia sin encender check engine",
        "sin luces de averia",
        "Revisar elementos mecanicos y mantenimiento aunque no existan codigos.",
        "¿Ocurre siempre, a cierta velocidad o solo bajo carga?",
        "MEDIA",
        "Motor, rodaje, frenos y transmision",
        (
            causa("filtro de aire sucio"),
            causa("presion baja de neumaticos", estado="REQUIERE_DESCARTE"),
            causa("mantenimiento atrasado", estado="REQUIERE_DESCARTE"),
            causa("peso excesivo", estado="REQUIERE_DESCARTE"),
            causa("frenos pegados"),
            causa("alineacion deficiente", "SUSPENSION_004"),
            causa("aceite incorrecto", estado="REQUIERE_DESCARTE"),
            causa("filtro de combustible restringido", "COMBUSTIBLE_001"),
            causa("catalizador parcialmente obstruido"),
            causa("transmision desgastada", estado="REQUIERE_REVISION_AMBIGUEDAD"),
        ),
    ),
    Grupo(
        "perdida_potencia",
        "Perdida de potencia con vibraciones o tirones",
        "el auto pierde fuerza, vibra o da tirones",
        "al acelerar o bajo carga",
        "Separar falla de combustion, soportes, combustible y transmision.",
        "¿Vibra detenido, al acelerar o al cambiar de marcha?",
        "MEDIA_ALTA",
        "Motor, combustible y transmision",
        (
            causa("bujias o bobinas defectuosas", "MOTOR_001"),
            causa("inyectores o suministro de combustible", "COMBUSTIBLE_001", "REQUIERE_REVISION_AMBIGUEDAD"),
            causa("soportes de motor dañados"),
            causa("problema de transmision", estado="REQUIERE_REVISION_AMBIGUEDAD"),
        ),
    ),
)


def sha256_archivo(ruta: Path) -> str:
    digest = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(65536), b""):
            digest.update(bloque)
    return digest.hexdigest()


def cargar_taxonomia(ruta: Path) -> dict[str, tuple[str, str]]:
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        filas = csv.DictReader(archivo)
        taxonomia: dict[str, tuple[str, str]] = {}
        for fila in filas:
            codigo = fila["codigo_falla"].strip()
            taxonomia[codigo] = (fila["falla"].strip(), fila["sistema"].strip())
    if not taxonomia:
        raise ValueError("La taxonomia canonica esta vacia.")
    return taxonomia


def verificar_fuente(ruta: Path | None, fuente: str) -> tuple[str, bool]:
    esperado = FUENTES[fuente]["sha256"]
    if ruta is None:
        return esperado, False
    obtenido = sha256_archivo(ruta)
    if obtenido != esperado:
        raise ValueError(f"SHA-256 inesperado para {fuente}: {obtenido}")
    return obtenido, True


def preparar(
    salida: Path,
    reporte: Path,
    taxonomia_path: Path,
    fuente_general: Path | None = None,
    fuente_potencia: Path | None = None,
) -> dict[str, object]:
    taxonomia = cargar_taxonomia(taxonomia_path)
    hashes = {
        "fallas_comunes": verificar_fuente(fuente_general, "fallas_comunes"),
        "perdida_potencia": verificar_fuente(fuente_potencia, "perdida_potencia"),
    }
    filas: list[dict[str, str]] = []
    vistos: set[tuple[str, str, str, str]] = set()
    conteo = Counter()

    for grupo in GRUPOS:
        fuente = FUENTES[grupo.fuente]
        for causa_nombre, codigo, estado in grupo.causas:
            clave = (grupo.fuente, grupo.sintoma, grupo.condicion, causa_nombre)
            if clave in vistos:
                raise ValueError(f"Relacion duplicada: {clave}")
            vistos.add(clave)
            if codigo and codigo not in taxonomia:
                raise ValueError(f"Codigo canonico desconocido: {codigo}")
            falla_canonica, sistema_canonico = taxonomia.get(codigo, ("", ""))
            conteo[estado] += 1
            filas.append(
                {
                    "id_candidato": f"GEM-{len(filas) + 1:04d}",
                    "sintoma": grupo.sintoma,
                    "condicion": grupo.condicion,
                    "causa_candidata": causa_nombre,
                    "revision_inicial": grupo.revision,
                    "pregunta_aclaracion": grupo.pregunta,
                    "urgencia_fuente": grupo.urgencia,
                    "sistema_fuente": grupo.sistema,
                    "codigo_canonico_propuesto": codigo,
                    "falla_canonica_propuesta": falla_canonica,
                    "sistema_canonico": sistema_canonico,
                    "estado_mapeo": estado,
                    "decision_revision": "PENDIENTE_MECANICO",
                    "validado_por_mecanico": "NO",
                    "apto_entrenamiento": "NO",
                    "uso_recomendado_actual": "CANDIDATO_RAG_Y_REVISION",
                    "fuente": fuente["titulo"],
                    "url_fuente": fuente["url"],
                    "seccion_fuente": grupo.seccion,
                    "fecha_consulta": "2026-09-02",
                    "licencia_fuente": "NO_DECLARADA",
                    "sha256_texto_fuente": hashes[grupo.fuente][0],
                    "observaciones_revision": "",
                }
            )

    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)

    resumen: dict[str, object] = {
        "tipo_dataset": "CONOCIMIENTO_MULTICAUSA_CANDIDATO",
        "generado_el": "2026-09-02",
        "registros": len(filas),
        "sintomas_unicos": len({fila["sintoma"] for fila in filas}),
        "causas_unicas": len({fila["causa_candidata"] for fila in filas}),
        "conteo_estado_mapeo": dict(sorted(conteo.items())),
        "fuentes": {
            clave: {
                "url": FUENTES[clave]["url"],
                "sha256": valor[0],
                "archivo_verificado": valor[1],
                "licencia": "NO_DECLARADA",
            }
            for clave, valor in hashes.items()
        },
        "duplicados_exactos": 0,
        "incorporado_al_entrenamiento": False,
        "motivo": (
            "La fuente es secundaria, no declara licencia reutilizable y las relaciones son "
            "multicausa. Requiere permiso y validacion por mecanico."
        ),
    }
    reporte.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    return resumen


def generar_derivados(
    candidatos_path: Path,
    entrenamiento_path: Path,
    rag_path: Path,
) -> dict[str, int]:
    """Crea derivados seguros: casos univocos para ML y conocimiento multicausa para RAG."""
    with candidatos_path.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))

    grupos: dict[tuple[str, str, str, str], list[dict[str, str]]] = {}
    for fila in filas:
        clave = (
            fila["fuente"],
            fila["seccion_fuente"],
            fila["sintoma"],
            fila["condicion"],
        )
        grupos.setdefault(clave, []).append(fila)

    entrenamiento: list[dict[str, str]] = []
    secciones_rag: list[str] = []
    for (fuente, seccion, sintoma, condicion), relaciones in grupos.items():
        estados = {fila["estado_mapeo"] for fila in relaciones}
        codigos = {
            fila["codigo_canonico_propuesto"]
            for fila in relaciones
            if fila["codigo_canonico_propuesto"]
        }
        if estados == {"MAPEO_PROPUESTO"} and len(codigos) == 1:
            representativa = relaciones[0]
            entrenamiento.append(
                {
                    "sintoma": f"{sintoma}; {condicion}",
                    "falla": representativa["falla_canonica_propuesta"],
                    "codigo_falla": representativa["codigo_canonico_propuesto"],
                    "sistema": representativa["sistema_canonico"],
                    "severidad": representativa["urgencia_fuente"].lower(),
                    "origen": "GEMACAR_WEB_EXPERIMENTAL",
                    "url_fuente": representativa["url_fuente"],
                    "licencia": representativa["licencia_fuente"],
                    "estado_validacion": "FUENTE_SECUNDARIA_NO_VALIDADA_POR_MECANICO",
                }
            )

        posibles = [
            fila["causa_candidata"]
            for fila in relaciones
            if fila["estado_mapeo"] not in {"DESCARTAR_NO_FALLA", "REQUIERE_DESCARTE"}
        ]
        descartes = [
            fila["causa_candidata"]
            for fila in relaciones
            if fila["estado_mapeo"] == "REQUIERE_DESCARTE"
        ]
        normales = [
            fila["causa_candidata"]
            for fila in relaciones
            if fila["estado_mapeo"] == "DESCARTAR_NO_FALLA"
        ]
        representativa = relaciones[0]
        cuerpo = [
            f"=== ORIENTACION SECUNDARIA NO VALIDADA: {seccion.upper()} ===",
            "Estado: fuente web secundaria; pendiente de validacion mecanica.",
            f"Sintoma: {sintoma}.",
            f"Condicion: {condicion}.",
        ]
        if posibles:
            cuerpo.append(f"Causas posibles a diferenciar: {'; '.join(posibles)}.")
        if descartes:
            cuerpo.append(f"Factores no concluyentes que deben descartarse: {'; '.join(descartes)}.")
        if normales:
            cuerpo.append(f"Condiciones que pueden ser normales: {'; '.join(normales)}.")
        cuerpo.extend(
            [
                f"Revision inicial: {representativa['revision_inicial']}",
                f"Pregunta de aclaracion: {representativa['pregunta_aclaracion']}",
                f"Urgencia orientativa: {representativa['urgencia_fuente']}.",
                (
                    "Regla de seguridad: no confirmar una pieza ni ordenar un reemplazo sin "
                    "pruebas fisicas, codigos y mediciones del fabricante."
                ),
                f"Fuente secundaria: {fuente}.",
                f"URL: {representativa['url_fuente']}",
            ]
        )
        secciones_rag.append("\n".join(cuerpo))

    entrenamiento_path.parent.mkdir(parents=True, exist_ok=True)
    with entrenamiento_path.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(entrenamiento[0]))
        escritor.writeheader()
        escritor.writerows(entrenamiento)

    rag_path.parent.mkdir(parents=True, exist_ok=True)
    rag_path.write_text("\n\n".join(secciones_rag) + "\n", encoding="utf-8")
    return {
        "registros_ml_experimentales": len(entrenamiento),
        "secciones_rag_secundarias": len(secciones_rag),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fuente-general", type=Path)
    parser.add_argument("--fuente-potencia", type=Path)
    parser.add_argument(
        "--salida",
        type=Path,
        default=OUTPUT_DIR / "gemacar_sintomas_causas_candidatas.csv",
    )
    parser.add_argument(
        "--reporte",
        type=Path,
        default=OUTPUT_DIR / "gemacar_sintomas_causas_reporte.json",
    )
    parser.add_argument(
        "--taxonomia",
        type=Path,
        default=DATA_DIR / "dataset_sintomas_limpio.csv",
    )
    parser.add_argument(
        "--salida-entrenamiento",
        type=Path,
        default=DATA_DIR / "dataset_gemacar_experimental.csv",
    )
    parser.add_argument(
        "--salida-rag",
        type=Path,
        default=ROOT / "manuals/generales/orientacion_secundaria_gemacar.txt",
    )
    args = parser.parse_args()
    resumen = preparar(
        salida=args.salida,
        reporte=args.reporte,
        taxonomia_path=args.taxonomia,
        fuente_general=args.fuente_general,
        fuente_potencia=args.fuente_potencia,
    )
    resumen.update(generar_derivados(args.salida, args.salida_entrenamiento, args.salida_rag))
    args.reporte.write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
