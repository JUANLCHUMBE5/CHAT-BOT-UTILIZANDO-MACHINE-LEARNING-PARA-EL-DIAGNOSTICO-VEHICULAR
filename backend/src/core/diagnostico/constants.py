"""Constantes técnicas y vocabularios automotrices para detección y análisis."""

from __future__ import annotations

from src.core.taxonomy.catalogo_fallas import CATALOGO_TAXONOMIA

# Vocabulario de componentes automotrices derivado de taxonomía y sistemas vehiculares
VOCABULARIO_COMPONENTES = [
    "freno", "frenos", "pastilla", "pastillas", "disco", "discos", "zapata", "zapatas", "tambor", "pedal",
    "booster", "servofreno", "abs", "pulmon", "secador", "aps", "camion", "camiones",
    "motor", "bujia", "bujias", "bobina", "bobinas", "piston", "pistones", "anillos", "culata", "empaque",
    "faja", "cadena", "distribucion", "tiempo", "aceite", "bomba", "lubricacion", "carter",
    "inyector", "inyectores", "filtro", "combustible", "gasolina", "diesel", "diésel", "petroleo", "riel",
    "gnv", "glp", "gas natural", "reductor", "vaporizador", "riel de gas", "inyector de gas",
    "common rail", "scv", "iac", "mariposa", "acelerador", "aceleracion", "sensor", "oxigeno", "lambda", "maf", "map",
    "embrague", "clutch", "bombin", "prensa", "collarin", "caja", "cambio", "cambios", "transmision",
    "automatica", "mecanica", "cvt", "dsg", "dualogic", "diferencial", "rodaje", "rodajes", "valvolina",
    "refrigeracion", "termostato", "radiador", "ventilador", "electroventilador", "refrigerante", "manguera",
    "electrico", "eléctrico", "alternador", "bateria", "batería", "borne", "bornes", "arranque", "arrancador",
    "solenoide", "ignicion", "fusible", "rele", "cableado",
    "suspension", "suspensión", "amortiguador", "amortiguadores", "buche", "bujes", "trapecio", "rotula", "rótula",
    "palier", "palieres", "homocinetica", "homocinética", "tripoide", "cremallera", "direccion", "dirección",
    "timon", "timón", "volante", "eps", "llanta", "llantas", "rueda", "ruedas", "aro",
    "clima", "aire", "acondicionado", "a/c", "compresor", "gas", "r134a", "evaporador", "condensador",
    "turbo", "turbocompresor", "intercooler", "vgt", "wastegate", "dpf", "fap", "adblue", "def", "escape", "catalizador",
    "puerta", "puertas", "chapa", "chapas", "pestillo", "pestillos", "cerradura", "cerraduras", "seguro", "seguros",
    "control", "mando", "remoto", "actuador", "trinquete", "manija", "tirador",
    "ventana", "ventanas", "vidrio", "vidrios", "luna", "lunas", "elevalunas", "alzacristales", "guaya",
    "limpiaparabrisas", "pluma", "plumas", "parabrisas", "plumillas",
    "hibrido", "híbrido", "ev", "inversor", "alto voltaje", "hv", "prius", "regenerativo",
    "caliper", "mordaza", "bomba principal de freno", "modulo abs", "modulo de abs",
    "calefaccion", "radiador de calefaccion", "soplador", "ventilador de cabina", "resistencia de soplador",
    "eje", "eje posterior", "eje rigido", "cruceta", "junta universal", "cardan", "acople viscoso",
    "faro", "luz delantera", "claxon", "bocina", "lavaparabrisas", "bomba lavaparabrisas",
    "canister", "valvula de purga", "convertidor catalitico", "multiple de escape", "tapa de combustible",
    "sensor de detonacion", "eje balanceador", "bujia de precalentamiento", "soporte de motor",
    "valvula de admision", "valvula de escape", "tapa de valvulas", "pcv", "filtro de aire",
    "regulador de presion", "tanque de combustible", "tps", "sensor de posicion del acelerador",
    "liquido de direccion", "direccion hidraulica", "convertidor de par", "cubo de rueda", "tpms"
]


def _vocabulario_desde_taxonomia() -> set[str]:
    """Extrae terminos utiles para que el filtro evolucione con la taxonomia."""
    ignoradas = {
        "para", "con", "del", "los", "las", "una", "por", "falla", "sistema",
        "alta", "baja", "media", "motor", "vehiculo", "vehicular",
    }
    terminos: set[str] = set()
    for falla in CATALOGO_TAXONOMIA.values():
        textos = [falla.sistema, falla.falla_principal, *falla.posibles_causas]
        for texto in textos:
            palabras = "".join(
                caracter.lower() if caracter.isalnum() else " " for caracter in texto
            ).split()
            terminos.update(
                palabra for palabra in palabras if len(palabra) >= 3 and palabra not in ignoradas
            )
    return terminos


VOCABULARIO_COMPONENTES = sorted(
    set(VOCABULARIO_COMPONENTES) | _vocabulario_desde_taxonomia()
)

VERBOS_FALLA = [
    "no abre", "no cierra", "trabado", "trabada", "trancado", "trancada", "chueco", "chueca", "inclinado", "inclinada",
    "desalineado", "desalineada", "bloqueado", "bloqueada", "desbloquea", "salta", "no sube", "no baja", "se cayo", "se cayó",
    "chirria", "chirría", "chillido", "rechina", "rechinido", "vibra", "vibracion", "vibración", "tiembla", "cascabelea",
    "cascabeleo", "golpeteo", "crujido", "chasquido", "sonido", "ruido", "se apaga", "apaga", "pierde fuerza", "sin fuerza",
    "no arranca", "cuesta arrancar", "jalonea", "jaloneo", "tirones", "gotea", "fuga", "bota", "humo", "recalienta",
    "hierve", "patina", "esponjoso", "duro", "pesado", "no responde", "no funciona", "falla", "defectuoso", "quemado", "roto", "partido",
    "suelto", "oxido", "sulfatado", "baja presion", "alta presion", "no enfria", "no marca", "oscila",
    "permanece encendido", "se amarra", "bambolea", "se inclina", "rebota", "pulsa", "demora en acoplar",
    "flujo debil", "poca presion", "olor", "raspa", "golpea", "se mueve demasiado", "trabaja disparejo",
    "zapatea", "zapateo", "se hunde", "se va al fondo", "traca traca", "trac trac", "clac clac", "tac tac",
    "prende en rojo", "se prende en rojo", "aceitera", "robot", "i-motion", "dualogic",
]

PALABRAS_MECANICAS = VOCABULARIO_COMPONENTES[:30]
