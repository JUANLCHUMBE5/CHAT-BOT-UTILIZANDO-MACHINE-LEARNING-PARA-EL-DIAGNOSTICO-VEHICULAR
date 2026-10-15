"""Expansión léxica del RAG, sin acceso al índice ni a documentos."""

import re


def expandir_consulta(consulta: str) -> str:
    """Expande la consulta del usuario incluyendo términos técnicos estandarizados y códigos DTC."""
    consulta_limpia = str(consulta or "").strip()[:4000]
    consulta_lower = consulta_limpia.lower()
    expansiones = []
    niega_vibracion_freno = bool(
        re.search(r"\b(?:al\s+frenar\s+no\s+vibra|al\s+pisar\s+el\s+freno\s+no\s+vibra|fren(?:ar|o|os)?\s+no\s+vibra|no\s+vibra\s+al\s+frenar)\b", consulta_lower)
    )
    vibracion_al_frenar = ("vibr" in consulta_lower and "fren" in consulta_lower) and not niega_vibracion_freno
    if vibracion_al_frenar:
        expansiones.append("vibracion pedal freno discos deformados durante frenado")
    elif niega_vibracion_freno:
        expansiones.append("balanceo dinamico ruedas alineacion direccion vibracion volante velocidad")


    diccionario_dtc = {
        "p0300": "bujias cascabeleo misfire encendido",
        "p0301": "bujias cascabeleo misfire encendido",
        "c0035": "pastillas de freno chillido disco",
        "c0040": "purga liquido de frenos pedal esponjoso fuga",
        "p0505": "valvula iac cuerpo de aceleracion ralenti minimo apaga",
        "p0562": "bateria voltaje arranque alternador bornes",
        "p0a80": "bateria alto voltaje hibrido prius celdas",
        "p2002": "filtro particulas dpf fap adblue escape",
        "p0087": "presion combustible riel common rail bomba alta",
        "p2135": "cuerpo de aceleracion mariposa electronica tps",
        "p0011": "valvula solenoide ocv sincronizacion variable vvt",
        "mezcla pobre": "P0171 P0174 mezcla pobre fuel trim STFT LTFT sensor oxigeno presion combustible caudal inyectores",
        "mezcla rica": "P0172 P0175 mezcla rica fuel trim STFT LTFT sensor oxigeno inyectores presion combustible",
        "inyectores no inyectan": "inyectores caudal flujo de combustible presion riel balance de cilindros circuito electrico inyector",
        "carga absoluta": (
            "sensor MAP presión absoluta del múltiple admisión carga absoluta P0105 P0106 "
            "lectura escáner baro colector admisión P0107 P0108 P0109 vacío señal voltaje frecuencia"
        ),
        "map": "sensor de presion absoluta del multiple admision carga absoluta P0105 P0106",
        "p0700": "transmision automatica cvt caja solenoide sobrecalentamiento",
        "p0841": "sensor presion fluido transmision cvt",
        "cvt": "transmision continuamente variable cvt poleas fluido ns3 nissan",
        "chillido": "pastillas de freno freno",
        "esponjoso": "liquido de frenos purga fuga bombin",
        "cascabelea": "bujias motor encendido ocv vvt",
        "cascabeleo": "bujias motor encendido ocv vvt",
        "se apaga": "valvula iac cuerpo aceleracion ralenti",
        "pestillo": "chapa cerradura puerta seguro pestillo mecanico",
        "elevalunas": "alzacristales vidrio guaya motor ventana",
        "alzacristales": "elevalunas vidrio guaya ventana",
        "limpiaparabrisas": "motor plumas varillaje limpiaparabrisas",
        "common rail": "diesel bomba alta presion inyectores scv",
        "dpf": "filtro particulas hollin adblue def regeneracion",
        "adblue": "urea def regeneracion dpf catalizador",
        "freno de aire": "camion neumatico valvula secador aps compresor",
        "inversor": "hibrido ev alto voltaje igbt bomba enfriamiento",
        "hibrido": "bateria alto voltaje inversor motor electrico ready",
        "valvolina": "caja cambios mecanica rodajes diferencial aceite",
        "gnv": "gas natural vehicular rampa reductor 5ta generacion gas",
        "glp": "gas licuado petroleo rampa reductor 5ta generacion gas",
        "desembraga": "embrague bombin plato prensa disco hidraulico",
        "puerta": "cierre centralizado actuador puerta seguro electrico chapa",
        "desbloquea": "cierre centralizado control remoto actuador puerta",
        "bloqueada": "cierre centralizado actuador puerta chapa cerradura",
        "chapa": "cerradura chapa pestillo puerta trinquete",
        "cerradura": "chapa cerradura pestillo puerta trinquete",
        "humo blanco": "empaquetadura culata refrigerante motor sobrecalentamiento",
        "humo negro": "mezcla rica inyectores filtro aire maf map sensor oxigeno",
        "sensor map": "baro presion absoluta colector admision p0105 p0106 p0107 p0108 p0109 vacio señal voltaje frecuencia",
        "presion absoluta": "sensor map baro colector admision p0105 p0106 p0107 p0108 p0109 vacio señal voltaje frecuencia",
        "vibra": "vibracion volante asiento pedal velocidad balanceo alineacion freno soportes",
        "pierde fuerza": "perdida potencia aceleracion subida combustible aire escape transmision",
        "pierde potencia": "perdida potencia aceleracion subida combustible aire escape transmision",
        "culata": "empaquetadura culata refrigerante motor sobrecalentamiento",
        "refrigerante": "termostato ventilador fuga refrigerante culata",
        "alternador": "alternador bateria sistema electrico carga bornes",
        "bateria": "bateria alternador voltaje arranque sistema electrico",
        "acople": "direccion asistida electrica eps mdps columna chasquido volante timon",
        "mariposa": "cuerpo de aceleracion electronico drive-by-wire marcha minima ralenti",
        "can bus": "red de comunicacion multiplexada can bus terminacion 60 ohms dlc osciloscopio",
        "can-h": "red can bus alta velocidad terminacion dlc obd2",
        "evap": "sistema evaporacion emisiones canister valvula purga fuga vacio tanque",
        "canister": "sistema evaporacion emisiones evap purga vacio tanque combustible",
        "sensor de oxigeno": "sonda lambda sensor aire combustible a/f banda ancha calefactor",
        "sensor a/f": "sensor relacion aire combustible banda ancha calefactor mezcla",
        "ibs": "sensor bateria corriente inteligente carga alternador pilotado",
        "termostato": "refrigeracion termostato purga temperatura sobrecalentamiento radiador",
        "p0128": "termostato refrigerante motor temperatura baja refrigeracion",
        "p0440": "sistema evap emisiones purga canister fuga tanque",
        "p0442": "sistema evap emisiones purga canister microfuga vacio",
        "p0455": "sistema evap emisiones purga canister fuga grande tapa tanque",
        "p0620": "circuito control alternador carga inteligente pilotado",
        "u0100": "red can bus perdida comunicacion ecm modulo motor",
        "u0101": "red can bus perdida comunicacion tcm transmision caja",
        "u0121": "red can bus perdida comunicacion abs frenos modulo",
        "abs": "modulo abs frenos purga electrovalvulas sensor rueda bomba escaner sangrado",
        "purgar": "purgado purga sangrado liquido frenos modulo abs aire",
        "gdi": "inyeccion directa gdi tsi bomba alta presion riel combustible hpfp",
        "tsi": "inyeccion directa gdi tsi bomba alta presion riel combustible hpfp",
        "turbo": "turboalimentador wastegate actuador sobrealimentacion intercooler soplido",
        "intercooler": "turbo sobrealimentacion fuga cañeria aire presion underboost",
        "dsg": "transmision doble embrague mecatronica dsg dct robotizada k1 k2",
        "dct": "transmision doble embrague mecatronica dsg dct robotizada k1 k2",
        "epb": "freno estacionamiento electrico epb servomotor caliper trasero modo servicio",
        "freno de mano electrico": "freno estacionamiento electrico epb servomotor caliper trasero modo servicio",
        "haldex": "traccion integral awd haldex acoplador multidisco diferencial trasero",
        "awd": "traccion integral awd haldex acoplador multidisco diferencial trasero",
        "sas": "sensor angulo direccion sas calibracion punto cero esp antiderrape",
        "scv": "valvula reguladora succion scv bomba common rail diesel presion riel",
        "p0299": "turbo sobrealimentacion baja underboost wastegate fuga intercooler",
        "p0234": "turbo sobrepresion overboost wastegate actuador regulador",
        "c1555": "freno estacionamiento electrico epb servomotor caliper motor",
        "c1260": "sensor angulo direccion sas calibracion punto cero esp",
        "retorno": "inyectores common rail retorno probetas valvula scv diesel riel bomba",
        "diesel": "diesel common rail bomba alta presion inyectores scv retorno dpf arranque",
        "arrancador": "motor de arranque solenoide carbones terminal 50 no da marcha clac seco",
        "clac": "motor de arranque solenoide clac seco carbones no da marcha terminal 50",
        "mudo": "motor de arranque solenoide no da marcha clac seco se queda mudo",
        "no da marcha": "motor de arranque solenoide carbones terminal 50 no da marcha clac seco",
        "no da arranque": "motor de arranque solenoide carbones terminal 50 no da marcha clac seco",
        "en caliente": "sensor de posicion cigueñal ckp efecto hall inductivo dilatacion termica bobina p0335 bomba gasolina",
        "calienta": "sensor de posicion cigueñal ckp efecto hall inductivo dilatacion termica bobina p0335 bomba gasolina",
        "enfrie": "sensor de posicion cigueñal ckp efecto hall inductivo dilatacion termica bobina p0335",
        "enfria": "sensor de posicion cigueñal ckp efecto hall inductivo dilatacion termica bobina p0335",
        "gira con fuerza": "arrancador operativo no enciende falta chispa pulso inyeccion sensor ckp cigueñal p0335",
        "no enciende": "sensor ckp cigueñal chispa pulso inyeccion bomba gasolina p0335",
        "cortaran la corriente": "sensor ckp cigueñal rele principal efi encendido p0335",
        "corta corriente": "sensor ckp cigueñal rele principal efi encendido p0335",
        "apaga de golpe": "sensor ckp cigueñal rele principal efi corte encendido p0335",
        "zumbido": "bomba de combustible tanque zumbido alta presion rampa caudal p0087",
        "asiento trasero": "bomba de combustible aforador tanque zumbido presion p0087",
        "asientos de atras": "bomba de combustible aforador tanque zumbido presion p0087",
        "asientos de atrás": "bomba de combustible aforador tanque zumbido presion p0087",
        "ahoga": "falta de combustible presion bomba caudal inyectores mezcla pobre p0171 p0087",
        "tironea": "tironeo perdida potencia combustible bujias bobinas presion caudal p0087 p0300",
        "tirones": "tironeo perdida potencia combustible bujias bobinas presion caudal p0087 p0300",
        "bomba de gasolina": "presion combustible riel caida caudal bajo carga tanque p0087",
        "silbido": "servofreno booster vacio pedal duro fuga linea de vacio multiple admision soplido",
        "servofreno": "booster servofreno linea de vacio pedal duro fuga vacio diafragma valvula check",
        "booster": "servofreno booster vacio pedal duro fuga diafragma retencion valvula check",
        "patina": "disco de embrague desgastado patinando prensa calado en 4ta marcha revoluciones suben sin velocidad",
        "patinando": "disco de embrague desgastado patinando prensa calado en 4ta marcha revoluciones suben sin velocidad",
        "asbesto": "disco de embrague desgastado patinando olor a quemado prensa calado",
        "wub-wub": "rodamiento de maza rodaje de rueda zumbido rodadura ruleman",
        "wub": "rodamiento de maza rodaje de rueda zumbido rodadura ruleman"
    }

    # Evitar falsos amigos cuando el motor de arranque sí gira con fuerza
    arranque_falla = any(x in consulta_lower for x in ["no da arranque", "no da marcha", "no gira el motor", "se queda mudo", "clac seco"])
    es_zumbido_mecanico = any(x in consulta_lower for x in ["rueda", "maza", "caja", "transmision", "rodamiento", "rodaje", "curva", "embrague"])

    for clave, valor in diccionario_dtc.items():
        if clave == "vibra" and vibracion_al_frenar:
            continue
        if clave in ["arrancador", "clac", "mudo", "no da marcha", "no da arranque"] and not arranque_falla and "gira con fuerza" in consulta_lower:
            continue
        if clave == "zumbido" and es_zumbido_mecanico:
            if any(x in consulta_lower for x in ["rueda", "maza", "curva"]):
                expansiones.append("rodamiento de maza rodaje de rueda zumbido rodadura alabeo")
            elif any(x in consulta_lower for x in ["caja", "transmision", "embrague", "neutro"]):
                expansiones.append("rodajes transmision manual eje primario crapodina collarin zumbido caja")
            continue
        if clave in consulta_lower:
            expansiones.append(valor)

    if expansiones:
        return f"{consulta_limpia} {' '.join(expansiones)}"
    return consulta_limpia
