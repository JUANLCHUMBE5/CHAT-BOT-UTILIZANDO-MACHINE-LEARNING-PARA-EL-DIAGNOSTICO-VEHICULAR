import json
import re
import unicodedata
import pandas as pd

# Cargar dataset TRAIN congelado
df = pd.read_csv("machine_learning/data/dataset_sintomas_limpio.csv")


def normalizar_texto(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    texto_norm = unicodedata.normalize("NFKD", texto.lower())
    texto_norm = "".join(c for c in texto_norm if not unicodedata.combining(c))
    return texto_norm.strip()


# Patrones semánticos exhaustivos

# 1. SÍNTOMAS PRIMARIOS (S)
PATRONES_SINTOMAS = [
    (r"\b(no\s+jala|pierde\s+fuerza|sin\s+fuerza|falta\s+de\s+fuerza|se\s+ahoga|chanchea|se\s+aguanta|no\s+pasa\s+de|falta\s+potencia|perdida\s+de\s+potencia|se\s+chupa|amarrado|lento|no\s+desarrolla|no\s+responde\s+al\s+acelerar)\b", "perdida_potencia"),
    (r"\b(tiembla|vibra|vibracion|zapatea|sacude|trepida|inestable|tembladera)\b", "vibracion"),
    (r"\b(ratea|cabecea|corcovea|tironea|jalonea|misfire|falla\s+cilindro|fallo\s+cilindro|tirones)\b", "misfire"),
    (r"\b(se\s+apaga|se\s+muere|apagon|se\s+corta|apaga\s+solo|se\s+me\s+apaga|muere\s+al)\b", "apagado"),
    (r"\b(no\s+prende|no\s+arranca|no\s+enciende|no\s+da\s+marcha|cuesta\s+arrancar|arranque\s+largo|no\s+gira|no\s+arranco|no\s+prendio|pesado\s+para\s+arrancar)\b", "no_arranca"),
    (r"\b(hierve|calienta|temperatura\s+alta|recalienta|ebullicion|vapor|sube\s+la\s+aguja|recalentamiento)\b", "sobrecalentamiento"),
    (r"\b(humo\s+blanco|humo\s+azul|humo\s+negro|humareda|vapor\s+blanco)\b", "humo_anomalo"),
    (r"\b(clac|tac|chasquido|chirrido|chillido|zumbido|golpeteo|traqueteo|crujido|rechina|ronquido|aulla|chillando|matraca|cascabelea|cascabeleo|golpe|suena\s+feo|ruido)\b", "ruido_anomalo"),
    (r"\b(pedal\s+esponjoso|pedal\s+duro|se\s+va\s+al\s+fondo|frena\s+largo|no\s+frena|sin\s+frenos|pedal\s+bajo|pedal\s+blando|frenos\s+largos|frena\s+mal)\b", "falla_frenos"),
    (r"\b(patina|embrague\s+patina|clutch\s+patina|no\s+entran\s+los\s+cambios|raspa\s+el\s+cambio|caja\s+dura|bota\s+la\s+tercera|bota\s+el\s+cambio|no\s+engancha)\b", "falla_transmision"),
    (r"\b(jala\s+a\s+un\s+lado|tira\s+a\s+la\s+derecha|tira\s+a\s+la\s+izquierda|direccion\s+dura|timon\s+duro|juego\s+en\s+el\s+timon|timon\s+pesado)\b", "falla_direccion"),
    (r"\b(luces\s+bajan|luces\s+tenues|bateria\s+descargada|no\s+retiene\s+carga|descarga\s+bateria|titilan\s+las\s+luces|radio\s+se\s+reinicia|falla\s+electrica|testigo\s+bateria)\b", "falla_electrica"),
    (r"\b(consume\s+gasolina|alto\s+consumo|gasta\s+combustible|olor\s+a\s+gasolina|traga\s+gasolina|gasta\s+mucha\s+nafta)\b", "consumo_combustible"),
    (r"\b(rebota|golpe\s+seco\s+en\s+bache|golpeteo\s+al\s+pasar\s+bache|suspension\s+caida|inclinado|caido|bujes\s+rotos)\b", "falla_suspension"),
]

# 2. CONDICIONES OPERACIONALES (C)
PATRONES_CONDICION_OPERACION = [
    (r"\b(en\s+carretera|a\s+velocidad|alta\s+velocidad|a\s+\d+\s*km/h|en\s+pista|en\s+viaje|en\s+ruta|autopista|autovia|andando|manejando|rodando)\b", "alta_velocidad"),
    (r"\b(al\s+acelerar|cuando\s+acelero|en\s+subida|en\s+cuesta|bajo\s+carga|a\s+fondo|pisando\s+fuerte|al\s+exigir|en\s+pendiente|con\s+peso|con\s+carga|aceleracion\s+brusca)\b", "carga_aceleracion"),
    (r"\b(en\s+ralenti|parado|detenido|en\s+el\s+semaforo|en\s+neutro|estacionado|en\s+minimo|en\s+marcha\s+lenta|sin\s+acelerar)\b", "ralenti_detenido"),
    (r"\b(al\s+frenar|cuando\s+freno|al\s+pisar\s+el\s+freno|desacelerando|en\s+bajada\s+frenando)\b", "al_frenar"),
    (r"\b(al\s+girar|al\s+doblar|girando|en\s+curva|toda\s+la\s+direccion|en\s+la\s+esquina|doblando)\b", "al_girar"),
    (r"\b(en\s+baches|en\s+empedrado|en\s+huecos|en\s+rompemuelles|terreno\s+irregular|pista\s+rota)\b", "baches_terreno"),
]

# 3. TEMPERATURA Y TIEMPO (T)
PATRONES_TEMPERATURA_TIEMPO = [
    (r"\b(en\s+frio|primer\s+arranque|por\s+la\s+mañana|motor\s+frio|al\s+arrancar\s+temprano)\b", "frio"),
    (r"\b(en\s+caliente|despues\s+de\s+calentar|ya\s+caliente|tras\s+andar|cuando\s+calienta|al\s+alcanzar\s+temperatura|por\s+calor)\b", "caliente"),
    (r"\b(a\s+los\s+\d+\s+minutos|despues\s+de\s+\d+|al\s+rato|a\s+los\s+5\s+minutos|tras\s+\d+|en\s+viaje\s+largo|mas\s+de\s+20\s+minutos)\b", "tiempo_transcurrido"),
    (r"\b(a\s+veces|intermitente|de\s+vez\s+en\s+cuando|otra\s+vez|vuelve\s+a\s+fallar|de\s+forma\s+aleatoria)\b", "intermitencia"),
]

# 4. EVOLUCIÓN DINÁMICA Y RESPUESTA A ACCIONES (E)
PATRONES_EVOLUCION_RESPUESTA = [
    (r"\b(mejora\s+al|se\s+recupero|se\s+le\s+pasa|empareja\s+al|baje\s+la\s+velocidad|al\s+soltar\s+el\s+acelerador|al\s+apagar\s+y\s+prender|desaparece\s+al)\b", "mejora_accion"),
    (r"\b(empeora\s+al|falla\s+mas\s+al|aumenta\s+al|se\s+siente\s+mas|vuelve\s+a\s+fallar\s+al|no\s+pasa\s+de\s+\d+)\b", "empeora_accion"),
    (r"\b(con\s+el\s+aire|con\s+el\s+a/c|con\s+las\s+luces|tanque\s+medio|tanque\s+vacio|reserva|debajo\s+de\s+la\s+mitad|tanque\s+casi\s+vacio)\b", "carga_auxiliar_combustible"),
]

# 5. DISCRIMINADORES TÉCNICOS Y METROLOGÍA (D)
PATRONES_DISCRIMINADORES_TECNICOS = [
    (r"\b([pbcu]\d{4})\b", "codigo_dtc"),
    (r"\b(\d+(\.\d+)?\s*(psi|bar|v|volts|voltios|kpa|mm|ohms?|amperios|a|ma))\b", "medicion_metrologica"),
    (r"\b(cambie|bujias\s+nuevas|bomba\s+nueva|filtro\s+nuevo|probe|reemplace|ya\s+se\s+cambio|recien\s+cambiado|nuevo|nueva)\b", "descarte_reemplazo"),
    (r"\b(bornes|bobina|bujia|solenoide|sensor\s+\w+|egr|maf|map|iac|inyector|bomba\s+de\s+gasolina|cremallera|rotula|bieleta|palier|homocinetica|cvt|dsg|dpf|adblue|inversor|wastegate|maxi-brake|camara\s+de\s+aire|secador\s+de\s+aire|faja\s+de\s+distribucion|cadena\s+de\s+distribucion)\b", "pieza_especifica"),
]


def clasificar_ejemplo(texto: str):
    t = normalizar_texto(texto)

    sintomas = set()
    for pat, k in PATRONES_SINTOMAS:
        if re.search(pat, t):
            sintomas.add(k)

    cond_op = set()
    for pat, k in PATRONES_CONDICION_OPERACION:
        if re.search(pat, t):
            cond_op.add(k)

    temp_tiempo = set()
    for pat, k in PATRONES_TEMPERATURA_TIEMPO:
        if re.search(pat, t):
            temp_tiempo.add(k)

    evol_resp = set()
    for pat, k in PATRONES_EVOLUCION_RESPUESTA:
        if re.search(pat, t):
            evol_resp.add(k)

    disc_tec = set()
    for pat, k in PATRONES_DISCRIMINADORES_TECNICOS:
        if re.search(pat, t):
            disc_tec.add(k)

    num_s = len(sintomas)
    num_c = len(cond_op)
    num_t = len(temp_tiempo)
    num_e = len(evol_resp)
    num_d = len(disc_tec)

    total_contexto = num_c + num_t + num_e + num_d
    dimensiones_activas = sum([
        num_s > 0,
        num_c > 0,
        num_t > 0,
        num_e > 0,
        num_d > 0,
    ])

    # Clasificación formal basada en riqueza y diversidad diagnóstica:
    # L3: Específica ->
    #   - Al menos 3 dimensiones diagnósticas activas Y (presencia de condición o evolución o discriminador metrológico/DTC),
    #   - O múltiples síntomas combinados con condiciones operacionales y evolutivas específicas.
    if (dimensiones_activas >= 3 and (num_c > 0 or num_e > 0 or "codigo_dtc" in disc_tec or "medicion_metrologica" in disc_tec)) or (num_s >= 2 and total_contexto >= 3) or (num_c >= 1 and num_t >= 1 and num_e >= 1):
        nivel = "L3"
    # L1: Escasa ->
    #   - 1-2 síntomas aislados sin condición, sin temperatura, sin evolución, sin discriminadores (e.g. "no jala", "tiembla", "se apaga").
    #   - O síntoma puro sin contexto operacional (total_contexto == 0).
    #   - O texto muy conciso con solo una señal sintomática y sin discriminador técnico (total_contexto <= 1 con longitud <= 5 palabras y sin pieza técnica).
    elif total_contexto == 0:
        nivel = "L1"
    elif total_contexto == 1 and num_s <= 1 and num_d == 0 and len(t.split()) <= 7:
        nivel = "L1"
    # L2: Intermedia ->
    #   - Síntoma + una o dos condiciones/discriminadores (e.g. "pierde fuerza cuando calienta", "vibra a 80 km/h", "tiembla en ralentí").
    else:
        nivel = "L2"

    return {
        "nivel": nivel,
        "sintomas": list(sintomas),
        "cond_op": list(cond_op),
        "temp_tiempo": list(temp_tiempo),
        "evol_resp": list(evol_resp),
        "disc_tec": list(disc_tec),
        "dimensiones_activas": dimensiones_activas,
        "total_contexto": total_contexto,
    }


df["clasificacion"] = df["sintoma"].apply(clasificar_ejemplo)
df["nivel"] = df["clasificacion"].apply(lambda x: x["nivel"])

print("================ DISTRIBUCIÓN TRAIN (6,189 filas) ================")
vc = df["nivel"].value_counts()
vp = df["nivel"].value_counts(normalize=True) * 100
for k in ["L1", "L2", "L3"]:
    print(f"  {k}: {vc.get(k, 0):4d} ejemplos ({vp.get(k, 0.0):5.2f}%)")
