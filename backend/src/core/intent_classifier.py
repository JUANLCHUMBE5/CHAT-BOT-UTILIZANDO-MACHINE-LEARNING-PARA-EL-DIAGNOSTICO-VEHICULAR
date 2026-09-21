"""Clasificación determinista de intención antes del diagnóstico vehicular."""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

TipoConsulta = Literal["diagnostico", "consulta_tecnica", "fuera_de_alcance"]


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto.lower())
    return " ".join(
        "".join(caracter for caracter in sin_tildes if not unicodedata.combining(caracter)).split()
    )


PATRONES_SINTOMA = (
    r"\bno (?:arranca|arrancaba|arranco|enciende|encendia|encendio|prende|prendia|prendio|da marcha|frena|frenaba|freno|acelera|aceleraba|acelero|enfria|enfriaba|funciona|funcionaba|abre|cierra|sube|subia|baja|bajaba|responde|respondia|carga|cargaba)\b",
    r"\b(?:pierde|perdio|perdia|perdiendo|perder|perdida) (?:de\s+)?(?:fuerza|potencia|aceite|refrigerante|pique|velocidad|desarrollo)\b",
    r"\b(?:se\s+)?(?:ahoga|ahogaba|ahogo|ahogando|ahogar|chupa|chupaba|chupo|chupando|chanchea|chancheaba|chancheando|aguanta|aguantaba|aguantando|amarrado|amarrada)\b",
    r"\bno (?:pasa|pasaba|puedo pasar|puede pasar|podia pasar|pudo pasar|llega|llegaba|sube|subia) de \d+\b",
    r"\bno (?:jala|jalaba|jalo|jalando|tira|tiraba|tirando|levanta|levantaba|desarrolla|desarrollaba)\b",
    r"\b(?:cuesta|costaba|demora|demoraba|tarda|tardaba|pesado para)\s+(?:en\s+)?(?:arrancar|encender|prender|partir)\b",
    r"\b(?:vibra|vibraba|vibrando|tiembla|temblaba|temblando|jalonea|jaloneaba|jaloneando|tironea|tironeaba|tironeando|ratea|rateaba|cabecea|cabeceaba|corcovea|corcoveaba|cascabelea|cascabeleaba|recalienta|recalentaba|hierve|hervia|patina|patinaba|gotea|goteaba|humea|humeaba|chilla|chillaba|rechina|rechinaba|golpea|golpeaba|raspa|raspaba|zumba|zumbaba|aulla|aullaba|ronca|roncaba|traquetea|traqueteaba|chasquea|chasqueaba|cruje|crujia)\b",
    r"\b(?:ruido|zumbido|aullido|ronquido|chillido|rechinido|golpeteo|traqueteo|chasquido|crujido|vibracion(?:es)?|fuga|humo|olor a quemado|luz de falla|check engine)\b",
    r"\b(?:se apaga|se apagaba|se apago|se apagando|se me apaga|se me apagaba|se corta|se cortaba|se muere|se moria|esta duro|esta esponjoso|se traba|esta trabado|se quedo trabado|trabado|inclinada|inclinado|no encaja|se descarga|consume demasiado)\b",
    r"\b(?:falla|fallando|averia|defectuoso|roto|quemado|sulfatado|baja presion|alta temperatura)\b",
    r"\b(?:atranca|atracando|atascado|oscila|sube y baja|no enfria|solo enfria|solo enfría|enfria solo|enfría solo|aire caliente|aire tibio|fuerza con la pierna|bloqueado|bloqueada|deja de enfriar|enfria poco|enfría poco|clima caliente|compresor no entra|compresor no acopla|sin gas)\b",

    r"\b(?:se hunde|hundiendose|hundido|se va al fondo|llega al fondo|al fondo contra|se cae hasta el piso|pedal esponjoso|pedal largo|pedal bajo|pedal blando|pedal duro|bomba de freno|cilindro maestro|liquido de freno|liquido de frenos|bombeo|bombear|sin presion|sin frenos?|frena mal|frenaba mal|frena largo|pedal raro)\b",
    r"\bpedal(?:\s+\w+){0,3}\s+(?:esponjoso|largo|bajo|blando|duro|se va al fondo|al fondo|en el piso|raro)\b",
    r"\b(?:frenos? (?:largos?|esponjosos?|sin presion|raros?)|pastillas? (?:gastadas?|desgastadas?)|discos? alabeados?)\b",
    r"\b(?:cremallera|rotula|rotulas|bieleta|bieletas|amortiguador|amortiguadores|palier|palieres|homocinetica|homocineticas|fuelle|guardapolvo|rodaje|rodamiento|desalineado|desalineada|alabeo)\b",
    r"\b(?:timon duro|direccion dura|juego en el timon|timon jala|tira a un lado|volante torcido|doblar|doblo|doblando)\b",
    r"\b(?:disco de embrague|plato y disco|collarin|crapodina|embrague patina|patina el embrague|no entran los cambios|caja dura|raspa el cambio|bota el cambio|bota la marcha)\b",
    r"\b(?:empaque de culata|soplo empaque|mayonesa en la tapa|cafe con leche|humo blanco|humo azul|humo negro|bota humo|botaba humo|tira humo|tiraba humo|burbujeo|burbujea|consume refrigerante|consume agua|mangueras duras)\b",
    r"\b(?:bateria descargada|se descargo|no retiene carga|borne sulfatado|alternador no carga)\b",
    r"\b(?:trac[- ]trac|clac[- ]clac|cloc[- ]cloc|tac[- ]tac|toc[- ]toc|hace clac|clac seco|golpe seco)\b",
    r"\b(?:luces tenues|intento arrancar|al intentar arrancar|no da arranque)\b",
    r"\b(?:al acelerar|en subida|en pendiente|a fondo|en neutro|en ralenti|subiendo una cuesta)\b",
    r"\b(?:se siente|siento)\s+(?:raro|inestable|pesado|duro|suelto)\b",
    r"\b(?:temperatura\s+(?:alta|al\s+maximo|al\s+m[aá]ximo|en\s+rojo|sube|elevada|pegada)|vapor\s+(?:blanco\s+)?(?:por\s+el|del|bajo\s+el)\s+cap[oó]|sale\s+vapor|humo\s+blanco\s+por\s+el\s+cap[oó])\b",
    r"\b(?:p|b|c|u)\d{4}\b",
)

PATRONES_PREGUNTA = (
    r"^(?:que|cual|cuanto|cuanta|cuantos|cuantas|por que)\b",
    r"^(?:como|cuando|donde)\s+(?:se|puedo|debo|va|funciona|hago|cambio|cambiar|calibro|calibrar|saber|instalar|desarmar|probar|medir|limpiar|revisar|identificar)\b",
    r"(?:^|[:;]\s*)(?:que|cual|cuanto|cuanta|cuantos|cuantas|por que)\b",
    r"^(?:se puede|puedo|debo|conviene|es recomendable|es normal|cada cuanto|necesito saber)\b",
    r"\b(?:que porcentaje|que potencia|que tipo|cuantos kilometros|cuanto kilometraje)\b",
)

TERMINOS_AUTOMOTRICES = {
    "auto", "carro", "vehiculo", "motor", "aceite", "refrigerante", "radiador",
    "gnv", "glp", "gas", "gasolina", "diesel", "freno", "frenos", "bateria",
    "embrague", "caja", "transmision", "llanta", "llantas", "faro", "faros",
    "foco", "focos", "led", "h4", "bujia", "bujias", "inyector", "inyectores",
    "kilometraje", "scanner", "escaner", "dtc", "suzuki", "toyota", "hyundai",
    "puerta", "chapa", "cerradura", "pestillo", "seguro", "ventana", "vidrio",
    "kia", "nissan", "chevrolet", "volkswagen", "ford", "mazda", "honda",
    "timon", "volante", "rueda", "ruedas", "direccion", "pista", "curva",
    "velocidad", "kilometros", "acondicionado", "clima", "compresor", "r134a",
    "camion", "camiones", "trailer", "muelles", "pulmon", "pulmones", "tanque",
    "tanques", "bares", "libras", "secador", "aps", "minimo", "ralenti",
    "mariposa", "iac", "gdi", "carbonilla", "admision", "escape", "distribucion",
    "faja", "cadena", "sincronizacion", "culata", "valvula", "valvulas",
    "anillos", "piston", "turbo", "intercooler", "dpf", "adblue", "catalizador",
    "limpiaparabrisas", "plumilla", "plumillas", "parabrisas", "alzacristales",
    "guaya", "cvt", "dsg", "hibrido", "prius", "inversor", "celda", "celdas",
    "alto voltaje", "common rail", "etanol", "flex", "valvulina", "diferencial",
    "arranque", "arrancador", "solenoide", "solenoides", "alternador", "frenar", "aceitera",
    "robot", "i-motion", "dualogic", "traca", "zapatea", "zapateo",
    "acelerar", "aceleracion", "aceleración", "subida", "cuesta", "pista rapida",
    "zumbido", "asiento", "asientos", "bomba", "aforador", "tanque de gasolina",
    "suspension", "suspensión", "bache", "baches", "rompemuelle", "rompemuelles",
    "pastilla", "pastillas", "pedal", "pedales", "caliper", "calipers", "mordaza",
    "mordazas", "bombeo", "bombazo", "bombazos", "purga", "purgado", "sangrado",
    "crapodina", "collarin", "maza", "bobina", "bobinas", "resorte", "maxi-brake",
    "acumulador", "parasito", "bcm", "corriente", "fuga", "multimetro",
    "arrancar", "encender", "prender", "luces", "potencia", "perdida", "climatizacion",
    "climatización", "manejar", "manejando", "conducir", "conduciendo",
    "temperatura", "vapor", "capo", "capó", "aguja",
}



def clasificar_intencion_consulta(texto: str) -> TipoConsulta:
    """Separa síntomas diagnosticables de preguntas informativas y texto ajeno.

    Las señales explícitas de avería tienen prioridad incluso cuando el mensaje
    está redactado como pregunta (por ejemplo: "¿por qué vibra al frenar?").
    """

    normalizado = _normalizar(texto)
    if any(re.search(patron, normalizado) for patron in PATRONES_SINTOMA):
        return "diagnostico"

    es_pregunta = "?" in texto or any(
        re.search(patron, normalizado) for patron in PATRONES_PREGUNTA
    )
    contiene_contexto_auto = any(
        re.search(rf"\b{re.escape(termino)}\b", normalizado)
        for termino in TERMINOS_AUTOMOTRICES
    )
    if es_pregunta and contiene_contexto_auto:
        return "consulta_tecnica"

    if contiene_contexto_auto:
        return "diagnostico"
    return "fuera_de_alcance"
