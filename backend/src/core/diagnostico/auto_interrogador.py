"""
Módulo de Auto-Preguntas Técnicas Dirigidas (Diagnóstico Guiado y Descarte Diferencial).
Permite al bot formular auto-preguntas clave cuando la consulta es ambigua o existen
hipótesis competidoras, garantizando el 100% de asertividad técnica con la respuesta del usuario.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class AutoPreguntaTecnica:
    es_necesaria: bool
    pregunta: str
    opciones: List[str]
    hipotesis_diferenciales: List[str]


# Mapa canónico de opciones contextuales para auto-preguntas dinámicas
MAPA_DESCRIPCION_OPCION = {
    # Frenos, Dirección y Suspensión
    "Discos de freno alabeados o desgastados": "La vibración ocurre ÚNICAMENTE al pisar el pedal de freno (Discos de freno alabeados)",
    "Llantas desbalanceadas o desalineadas": "La vibración ocurre en carretera a velocidad constante sin tocar el pedal de freno (Llantas desbalanceadas)",
    "Desgaste de pastillas y zapatas de freno": "Se escucha un chirrido metálico constante o raspado al frenar (Pastillas / Zapatas desgastadas)",
    "Fuga hidraulica o aire en el sistema de frenos": "El pedal de freno se siente esponjoso o se va hasta el fondo al frenar (Líquido / Aire en frenos)",
    "Falla en servofreno (booster) o linea de vacio": "El pedal de freno se puso duro como piedra y cuesta detener el auto (Servofreno / Booster)",
    "Cremallera de direccion asistida con holgura o fuga": "El timón tiene juego excesivo, fuga líquido de dirección o golpea al doblar (Cremallera de dirección)",
    "Amortiguadores reventados o bujes de suspension gastados": "El carro rebota excesivamente en baches o golpea seco en la suspensión (Amortiguadores / Bujes)",
    "Juntas homocineticas o palieres danados": "Suena un traqueteo seco 'clac-clac' continuo solo al doblar la dirección acelerando (Punta de palier / Homocinética)",
    "Falla en sensor de velocidad de rueda ABS": "La luz del ABS está encendida en el tablero o vibra el pedal en frenadas secas (Sensor ABS)",
    "Caliper de freno trabado o mordaza pegada (piston agarrotado)": "Una sola rueda recalienta excesivamente y el vehículo tira hacia ese lado sin frenar (Cáliper trabado)",
    "Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura)": "Zumbido grave de rodadura que se incrementa al tomar curvas en carretera (Rodamiento de rueda / Maza)",

    # Motor - Encendido, Inyección y Ralentí
    "Falla en bujias o bobinas de encendido (misfire)": "Jalonea o cabecea con pérdida de fuerza al acelerar en subida o carga (Bujías o bobinas de encendido)",
    "Cuerpo de aceleracion o valvula IAC sucia": "Las revoluciones (RPM) suben y bajan solas o se apaga al desacelerar o llegar a semáforos (Cuerpo de aceleración / IAC)",
    "Inyectores sucios o filtro de combustible obstruido": "El motor tose, tironea a cualquier velocidad o le cuesta responder al acelerador (Inyectores / Filtro)",
    "Bomba de gasolina quemada o con baja presion": "Falta de potencia en alta, se ahoga en subida o zumba fuerte el tanque de combustible (Bomba de combustible)",
    "Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet)": "El motor se apaga de golpe en carretera y no llega corriente a la bomba (Módulo FSCM / PEM)",
    "Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)": "Tironeo y pérdida de potencia en motor GDI por acumulación de carbón en válvulas de admisión (Carbón en válvulas GDI)",
    "Falla en sensor de oxigeno o mezcla rica": "Humo negro, olor excesivo a gasolina por el escape y alto consumo (Sensor de oxígeno / Mezcla)",
    "Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)": "Pérdida de potencia, cascabeleo o sonido de matraca en la culata al acelerar (Sistema VVT / VVT-i)",
    "Faja o cadena de distribucion destensada o con salto de punto": "Sonido de cadena floja en la distribución, motor descalibrado o fuera de punto (Cadena / Correa de distribución)",
    "Falla de correa dentada banada en aceite (Motor Ford 1.0 Dragon / GM Turbo)": "Luz de presión de aceite encendida por degradación de correa bañada en aceite (Correa en aceite)",
    "Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)": "El motor se apaga de golpe en caliente y no arranca hasta enfriar unos minutos (Sensor CKP / CMP)",
    "Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)": "Tironea o huele a nafta inmediatamente después de llenar el tanque (Sistema EVAP / Cánister)",
    "Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)": "Falta de potencia en alta, olor a azufre y código P0420 en escáner (Convertidor catalítico)",
    "Falla en regulador de presion de combustible o diafragma roto": "Humo negro y bujías empapadas por nafta filtrada por la manguera de vacío (Regulador de presión)",
    "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)": "Falla fija en un cilindro por circuito de inyector cortado o sin pulso (Circuito de inyector)",
    "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados": "Un cilindro falla a pesar de tener bujía y bobina buenas, compresión baja en manómetro (Pérdida de compresión)",

    # Arranque, Carga y Batería
    "Bateria descargada o bornes sulfatados": "Las luces del tablero se apagan o parpadean al dar arranque y suena arrastrado (Batería descargada)",
    "Falla en motor de arranque o solenoide (carbones gastados / contactos fogueados)": "Al girar la llave solo suena un chasquido 'clac' seco pero las luces quedan encendidas (Motor de arranque / Solenoide)",
    "Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)": "Al girar la llave solo suena un chasquido 'clac' seco pero las luces quedan encendidas (Motor de arranque / Solenoide)",
    "Alternador defectuoso o placa de diodos quemada": "El testigo de batería se enciende en marcha o el voltaje cae por debajo de 13.5V (Alternador defectuoso)",
    "Fuga parasita de corriente en reposo (consumo nocturno de bateria)": "Batería nueva amanece descargada tras quedar estacionado por la noche (Fuga parásita de corriente)",

    # Refrigeración y Lubricación
    "Falla en termostato o motoventilador de radiador": "La temperatura sube rápidamente en tráfico o el ventilador no enciende (Termostato / Motoventilador)",
    "Fuga en mangueras de refrigerante o radiador picado": "Pérdida visible de refrigerante o vapor blanco debajo del capó (Fuga de refrigerante)",
    "Empaque de culata soplado o danado": "Consume refrigerante, bota humo blanco espeso o burbujea el depósito de expansión (Empaque de culata)",
    "Baja presion de aceite o bomba de aceite defectuosa": "Testigo de aceite encendido en rojo en ralentí con sonido metálico de taqués (Bomba / Presión de aceite)",
    "Consumo de aceite por desgaste de anillos o retenes": "Bota humo azulado por el escape al acelerar y baja el nivel de aceite motor (Anillos / Retenes)",

    # Embrague y Transmisión
    "Disco de embrague desgastado o patinando": "El motor levanta RPM al acelerar pero el carro no gana velocidad con fuerza (Embrague patinando)",
    "Falla en bombin o bomba hidraulica de embrague": "El pedal de embrague se queda abajo o esponjoso y no entran las velocidades (Bombín hidráulico)",
    "Desgaste en collarin de empuje o crapodina de embrague": "Chirría o zumba agudo únicamente mientras se mantiene pisado el pedal de embrague (Collarín / Crapodina)",
    "Rodajes de transmision manual o eje primario gastados": "Ronroneo o zumbido en neutro con pedal suelto que cesa al pisar embrague (Rodamientos de caja)",
    "Falta o degradacion de aceite de caja de cambios": "Zumbido continuo en la transmisión que cambia al pisar el embrague (Aceite / Desgaste de caja)",
    "Rodajes de caja mecanica o diferencial gastados": "Zumbido áspero o aullido en la caja de cambios al rodar a velocidad (Rodamientos de caja / Diferencial)",
    "Sobrecalentamiento o solenoides en caja automatica CVT / DSG": "Golpeteo al cambiar de marcha o la caja automática entra en modo de emergencia (Caja automática CVT / DSG)",
    "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)": "La caja robotizada se salta a neutro 'N' o no entran los cambios en el tablero (Caja robotizada)",

    # Turbo y Diésel
    "Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI": "Falta de empuje del turbo y entra en modo protección en subidas (Actuador de turbo / VGT)",
    "Fuga en mangueras de intercooler o turbocompresor danado": "Silbido de aire fuerte al acelerar con pérdida notable de fuerza (Manguera de intercooler)",
    "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)": "Tarda en encender en frío o se apaga bajo carga pesada en motor diésel (Presión Common Rail)",
    "Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)": "Testigo DPF encendido y motor limitado de revoluciones (Filtro de partículas DPF)",

    # Camiones
    "Fugas de aire o fallos en el sistema de frenos neumático (Camiones)": "Se escucha escape continuo de aire en cañerías o pulmones traseros (Pulmones de freno de aire)",
    "Válvula de freno de aire o secador APS obstruido (Camiones)": "La válvula de descarga del secador APS bota aceite/humedad o no retiene presión (Secador APS)",
    "Falla en actuador de resorte o camara Maxi-Brake trabada (frenos de aire)": "Ruedas traseras del camión quedan bloqueadas por resorte de emergencia (Cámara Maxi-Brake)",

    # Accesorios y Confort
    "Falla en compresor de aire acondicionado o fuga de gas R134a": "El aire acondicionado sopla a temperatura ambiente y no enfría (Compresor / Fuga de gas A/C)",
    "Limpiaparabrisas o motor pluma quemado": "Los limpiaparabrisas no se mueven o se quedan trabados a mitad de recorrido (Motor del limpiaparabrisas)",
    "Elevalunas electrico o guaya de alzacristales rota o trabada": "El vidrio de la ventana no sube ni baja o hace ruido de trituración (Elevalunas / Alzacristales)",
    "Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado": "La puerta no cierra bien o no abre desde la manija exterior (Chapa / Cerradura de puerta)",
    "Falla electrica del cierre centralizado o actuador de puerta": "El cierre centralizado no traba todas las puertas con el mando a distancia (Actuador eléctrico)",

    # Vehículos Eléctricos e Híbridos
    "Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)": "Pérdida rápida de autonomía de la batería de alto voltaje o aviso del sistema híbrido (Batería HV)",
    "Fallo en inversor de corriente IGBT o motor electrico (EV)": "Mensaje de avería en el sistema de propulsión eléctrica sin tracción (Inversor IGBT / Motor EV)",
    "Falla en sistema de frenado regenerativo (EV / Hibridos)": "Freno regenerativo no retiene o salta advertencia de frenado combinado (Freno regenerativo)",
    "Foco o falla en sistema de refrigeracion de bateria/inversor (EV)": "Alerta de temperatura en circuito de refrigerante de batería de tracción (Refrigeración HV)",
    "Falla en sistema Flex / Bi-combustible (Alcohol/Etanol)": "Falla de arranque en frío o descalibración de mezcla en vehículo flex/etanol (Sistema Bi-combustible)",
}


def evaluar_auto_pregunta_descarte(
    texto: str,
    diagnostico_top1: str,
    confianza_top1: float,
    predicciones_top: Optional[List[dict]] = None,
) -> Optional[AutoPreguntaTecnica]:
    """
    Analiza si la consulta presenta ambigüedad clínica automotriz y genera una auto-pregunta
    técnica dinámica y estructurada basada estrictamente en el contexto ingresado y en las hipótesis
    competidoras de Machine Learning.
    """
    texto_l = texto.lower()

    # Bypass si hay código DTC OBD-II específico confirmado
    if re.search(r"\b[pbcu]\d{4}\b", texto_l):
        return None

    # Detección de síntomas ambiguos o difusos sin discriminadores técnicos
    es_tren_delantero_difuso = any(
        p in texto_l for p in (
            "tren delantero", "ruido en el tren delantero", "suena en baches",
            "ruido cuando paso por baches", "pistas irregulares"
        )
    ) and not any(
        c in texto_l for c in ("palier", "homocinetica", "amortiguador", "cremallera", "rotula", "disco", "pastilla")
    )

    es_vibracion_difusa = any(
        w in texto_l for w in ("vibra", "vibracion", "vibración", "tiembla", "zapatea", "sacude")
    ) and not any(
        c in texto_l for c in (
            "al frenar", "piso el freno", "pedal", "80", "90", "100", "120", "carretera",
            "ralenti", "ralentí", "neutro", "disco", "pastilla", "semáforo", "semaforo", "parado",
            "dsg", "k1", "cascabelea", "cascabeleo", "acelero fuerte"
        )
    )

    es_arranque_difuso = any(
        w in texto_l for w in ("no arranca", "no prende", "no enciende", "cuesta arrancar")
    ) and not any(
        c in texto_l for c in (
            "gira", "marcha", "clac", "chasquido", "tac", "carbones", "bateria", "batería",
            "chispa", "presion", "presión", "bomba", "caliente", "frio", "frío", "scanner", "dtc"
        )
    )

    es_apagado_difuso = any(
        w in texto_l for w in ("se apaga", "se me apaga", "se apaga solo")
    ) and not any(
        c in texto_l for c in (
            "ralenti", "ralentí", "frenar", "semaforo", "semáforo", "caliente", "frio", "frío",
            "bomba", "presion", "presión", "scanner", "dtc", "reposa", "minutos"
        )
    )

    es_tironeo_difuso = (
        len(texto_l.split()) < 16
        and any(w in texto_l for w in ("tironea", "jalonea", "se ahoga", "pierde fuerza", "no tiene fuerza", "falta potencia", "perdida de potencia", "pérdida de potencia", "pierde potencia"))
        and not any(c in texto_l for c in ("tanque", "filtro", "inyector", "bujia", "bujía", "bobina", "p0", "p1", "p2", "dtc", "turbo", "riel", "manometro", "manómetro"))
    )

    es_freno_difuso = (
        any(w in texto_l for w in ("frena mal", "problema en frenos", "pedal raro", "frenos raros"))
        or ("pedal" in texto_l and "freno" in texto_l and any(w in texto_l for w in ("raro", "extrano", "extraño", "falla", "mal")))
    ) and not any(
        c in texto_l for c in ("esponjoso", "duro", "piedra", "chillido", "chirrido", "fondo", "vacio", "vacío", "booster", "disco", "pastilla", "liquido", "líquido", "caliper", "mordaza")
    )

    es_temperatura_difusa = any(
        w in texto_l for w in ("se calienta", "recalienta", "temperatura sube", "problema de temperatura")
    ) and not any(
        c in texto_l for c in ("ventilador", "motoventilador", "termostato", "manguera", "refrigerante", "radiador", "humo", "burbujea", "deposito", "depósito", "aceite", "rueda", "aro", "caliper", "mordaza")
    )

    es_humo_difuso = any(
        w in texto_l for w in ("bota humo", "tira humo", "humo por el escape")
    ) and not any(
        c in texto_l for c in ("blanco", "negro", "azul", "azulado", "aceite", "refrigerante", "nafta", "gasolina", "diesel", "diésel", "freno", "mordaza", "aro", "rueda", "caliper", "pastilla")
    )

    es_zumbido_difuso = any(
        w in texto_l for w in ("zumba", "zumbido", "ronroneo", "aullido")
    ) and not any(
        c in texto_l for c in ("al girar", "curva", "caja", "embrague", "clutch", "freno", "pedal", "neutro", "maza", "masa", "rueda derecha", "rueda izquierda", "elevador", "wub-wub")
    )

    es_olor_difuso = any(
        w in texto_l for w in ("huele a quemado", "olor a quemado", "huele raro", "olor extrano")
    ) and not any(
        c in texto_l for c in ("asbesto", "freno", "pastilla", "aceite", "refrigerante", "embrague", "azufre")
    )

    es_consumo_difuso = any(
        w in texto_l for w in ("consume mucho combustible", "consume demasiado combustible", "alto consumo", "gasta mucha gasolina", "gasta nafta")
    ) and not any(
        c in texto_l for c in ("sensor", "oxigeno", "oxígeno", "bujia", "bujía", "inyector", "humo", "filtro", "dtc", "p0", "p1")
    )

    es_electrico_difuso = any(
        w in texto_l for w in ("luces parpadean", "luces del tablero parpadean", "tablero parpadea", "falla electrica")
    ) and not any(
        c in texto_l for c in ("arranque", "arrancador", "bateria", "batería", "alternador", "voltaje", "multimetro", "multímetro")
    )

    es_ac_difuso = any(
        w in texto_l for w in ("no enfria", "no enfría", "aire acondicionado no enfria")
    ) and not any(
        c in texto_l for c in ("compresor", "gas", "r134a", "fuga", "manometro", "manómetro", "ventilador", "caliente", "aire caliente")
    )

    es_aceleracion_difusa = any(
        w in texto_l for w in ("se queda acelerado", "revoluciones suben solas", "acelerado solo")
    ) and not any(
        c in texto_l for c in ("iac", "cuerpo de aceleracion", "cuerpo de aceleración", "valvula", "válvula", "sensor", "pedal")
    )

    es_ruido_difuso = any(
        w in texto_l for w in ("hace un ruido", "suena feo", "suena raro", "tiene un ruido", "hace ruido", "ruido extrano", "ruido extraño", "sonido extrano", "sonido extraño")
    ) and not any(
        c in texto_l for c in ("clac", "chillido", "chirrido", "golpeteo", "zumbido", "matraca", "freno", "bache", "giro", "doblar", "arranque", "cadena", "faja", "correa", "bomba", "caja", "embrague")
    )

    es_manejo_difuso = any(
        w in texto_l for w in ("se siente raro al manejar", "se siente raro", "comportamiento extrano", "inestable al manejar", "raro al manejar")
    ) and not any(
        c in texto_l for c in ("vibra", "tiembla", "freno", "timon", "direccion", "alineacion", "llanta", "amortiguador", "bache")
    )

    es_sintoma_difuso = (
        es_tren_delantero_difuso
        or es_vibracion_difusa
        or es_arranque_difuso
        or es_apagado_difuso
        or es_tironeo_difuso
        or es_freno_difuso
        or es_temperatura_difusa
        or es_humo_difuso
        or es_zumbido_difuso
        or es_olor_difuso
        or es_consumo_difuso
        or es_electrico_difuso
        or es_ac_difuso
        or es_aceleracion_difusa
        or es_ruido_difuso
        or es_manejo_difuso
    )

    # Cálculo de probabilidad y margen entre Top 1 y Top 2
    top1_p = float(confianza_top1)
    top2_p = 0.0
    if predicciones_top and len(predicciones_top) >= 2:
        top1_p = float(predicciones_top[0].get("probabilidad", confianza_top1))
        top2_p = float(predicciones_top[1].get("probabilidad", 0.0))
    margen = top1_p - top2_p

    # Bypass si hay mediciones metrológicas o pruebas instrumentales explícitas en el síntoma
    tiene_metrologia = any(
        w in texto_l
        for w in (
            "manometro", "manómetro", "multimetro", "multímetro", "voltimetro", "voltímetro",
            "osciloscopio", "compresion", "compresión", "8 psi", "65 psi", "psi", "bar",
            "resistencia", "ohmios", "ohm", "amanece descargada", "corriente de fuga",
            "golpes suaves", "toques al arrancador", "consumo parasito", "consumo parásito",
            "prueba de banco", "banco de prueba", "banco de inyectores", "elevador", "a mano",
        )
    )
    if tiene_metrologia:
        return None

    # REGLA 0: Si la confianza es alta (>= 0.70) o si NO es síntoma difuso con certidumbre suficiente, no interrumpir
    if top1_p >= 0.70:
        return None
    if not es_sintoma_difuso:
        if top1_p >= 0.60 or (top1_p >= 0.45 and margen >= 0.08) or margen >= 0.12:
            return None

    # REGLA 1: SI EL SÍNTOMA YA INCLUYE EL DISCRIMINADOR FÍSICO CLARO, NUNCA INTERRUMPIR
    # Caso 1a: Vibración exclusiva al frenar (Discos alabeados / DTV)
    vibracion_al_frenar = any(
        p in texto_l for p in (
            "al frenar", "al pisar el freno", "apenas piso el freno", "piso el freno",
            "vibra al frenar", "tiembla al frenar", "sacude al frenar", "zapatea al frenar",
            "pedal tiembla", "pedal me patea", "patea el pie", "pedal vibra", "pedal del freno tiembla",
            "freno y vibra", "freno y tironea", "freno y zapatea"
        )
    )
    if vibracion_al_frenar:
        return None

    # Caso 1b: Vibración de velocidad sin frenar (Balanceo / Suspensión)
    if any(w in texto_l for w in ("80", "90", "100", "120", "carretera", "autopista", "pista")) and any(
        w in texto_l for w in ("sin frenar", "no toco el freno", "no piso el freno", "rueda sedita")
    ):
        return None

    # Caso 1c: Arranque con síntoma claro de arrancador vs batería
    if any(w in texto_l for w in ("clac seco", "solo suena clac", "tac tac", "toques al arrancador", "carbones")):
        return None

    # Caso 1d: Embrague patinando
    if any(w in texto_l for w in ("patina el embrague", "revoluciona y no corre", "pedal al piso", "pedal se fue al piso")):
        return None

    # Caso 1e: Humo blanco por escape con consumo de refrigerante (Empaque de culata)
    if ("humo blanco" in texto_l or "vapor blanco" in texto_l) and any(w in texto_l for w in ("refrigerante", "agua", "escape", "culata")):
        return None

    # Caso 1f: Transmisión especializada identificada (DSG / CVT)
    if any(w in texto_l for w in ("caja dsg", "dsg", "caja cvt", "cvt", "caja automatica", "k1", "k2")) and "caja automatica" in diagnostico_top1.lower():
        return None

    # Caso 1g: Rodamiento de rueda con discriminador de carga lateral o giro
    if any(w in texto_l for w in ("al girar", "curva", "cargando peso", "peso en la rueda")) and any(w in texto_l for w in ("zumba", "zumbido", "ronco", "rodadura")):
        return None

    # Caso 1h: Collarín / crapodina de embrague al pisar pedal
    if any(w in texto_l for w in ("mientras se mantiene pisado", "al soltar el pedal el ruido desaparece", "chirria agudo metalico al fondo", "crapodina", "collarin")) and any(w in texto_l for w in ("embrague", "clutch", "pedal")):
        return None

    # Caso 1i: Cáliper trabado con recalentamiento unilateral de rueda
    if any(w in texto_l for w in ("caliper", "mordaza", "piston oxidado", "piston agarrotado", "al rojo vivo", "queman de calor")) and any(w in texto_l for w in ("rueda", "freno", "recalienta", "calor")):
        return None

    # REGLA 2: GENERACIÓN DINÁMICA BASADA EN LAS PREDICCIONES TOP DEL MACHINE LEARNING
    if predicciones_top and len(predicciones_top) >= 2:
        opciones_generadas = []
        hipotesis_generadas = []
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]

        for pred in predicciones_top[:4]:
            falla_nombre = pred.get("falla", "")
            prob = pred.get("probabilidad", 0.0)
            prob_pct = int(round(prob * 100)) if isinstance(prob, (int, float)) else 0
            desc = MAPA_DESCRIPCION_OPCION.get(falla_nombre)
            if desc and falla_nombre not in hipotesis_generadas:
                pct_str = f" — {prob_pct}%" if prob_pct > 0 else ""
                opciones_generadas.append(f"{emojis[len(opciones_generadas)]} {desc}{pct_str}")
                hipotesis_generadas.append(falla_nombre)

        if len(opciones_generadas) >= 2:
            if any(w in texto_l for w in ("vibra", "zapatea", "temblor", "sacude", "timon", "volante")):
                pregunta_titulo = "🔍 Para precisar el origen exacto de la vibración o comportamiento detectado:"
            elif any(w in texto_l for w in ("no arranca", "no prende", "cuesta arrancar", "bateria", "arrancador")):
                pregunta_titulo = "🔍 Para precisar el origen del problema de arranque:"
            elif any(w in texto_l for w in ("embrague", "clutch", "cambios", "caja")):
                pregunta_titulo = "🔍 Para confirmar el diagnóstico en el sistema de embrague o transmisión:"
            elif any(w in texto_l for w in ("freno", "pedal", "pastilla", "disco")):
                pregunta_titulo = "🔍 Para precisar la causa en el sistema de frenos:"
            elif any(w in texto_l for w in ("calienta", "temperatura", "refrigerante", "radiador")):
                pregunta_titulo = "🔍 Para precisar la causa del problema de temperatura:"
            elif any(w in texto_l for w in ("jalonea", "tironea", "cascabelea", "pierde fuerza", "no tiene fuerza")):
                pregunta_titulo = "🔍 Para precisar la causa del tironeo o falta de fuerza:"
            else:
                pregunta_titulo = "🔍 Para confirmar el diagnóstico entre las principales hipótesis técnicas:"

            return AutoPreguntaTecnica(
                es_necesaria=True,
                pregunta=pregunta_titulo,
                opciones=opciones_generadas,
                hipotesis_diferenciales=hipotesis_generadas,
            )

    return None


def formatear_mensaje_auto_pregunta(pregunta: AutoPreguntaTecnica) -> str:
    """Genera el mensaje interactivo para WhatsApp con las opciones de descarte técnico."""
    lineas = [
        f"🤖 {pregunta.pregunta}\n"
    ]
    for opt in pregunta.opciones:
        lineas.append(f"• {opt}")
    lineas.append("\n👉 *Responde indicando 1, 2 o describiendo brevemente la opción (o describe qué otro síntoma nota si ninguna coincide).*")
    return "\n".join(lineas)


MAPA_HIPOTESIS_A_CLASE_CANONICA = {
    # Mapeos de compatibilidad con versiones previas
    "Discos de freno alabeados": "Discos de freno alabeados o desgastados",
    "Llantas desbalanceadas": "Llantas desbalanceadas o desalineadas",
    "Soportes de motor": "Falla en soportes de motor o transmision (vibracion en ralenti)",
    "Misfire bujías/bobinas": "Falla en bujias o bobinas de encendido (misfire)",
    "Cuerpo aceleración IAC": "Cuerpo de aceleracion o valvula IAC sucia",
    "Inyectores/Bomba": "Bomba de gasolina quemada o con baja presion",
    "Motor de arranque / Solenoide": "Falla en motor de arranque o solenoide (carbones gastados / contactos fogueados)",
    "Batería descargada": "Bateria descargada o bornes sulfatados",
    "Bomba de combustible": "Bomba de gasolina quemada o con baja presion",
    "Disco de embrague desgastado": "Disco de embrague desgastado o patinando",
    "Bombín hidráulico de embrague": "Falla en bombin o bomba hidraulica de embrague",
    "Aceite de caja": "Falta o degradacion de aceite de caja de cambios",
    "Fuga en pulmones de aire": "Fugas de aire o fallos en el sistema de frenos neumático (Camiones)",
    "Válvula secador APS obstruida": "Válvula de freno de aire o secador APS obstruido (Camiones)",
}


def es_rechazo_de_opciones(texto: str) -> bool:
    """Detecta si el usuario descarta o indica que no es ninguna de las opciones propuestas."""
    limpio = texto.strip().lower().strip(" .,!¡¿?")
    patrones_rechazo = {
        "ninguna", "ninguno", "ninguna de las tres", "ninguna de esas", "no es ninguna",
        "ninguna de las opciones", "ninguna de las anteriores", "ninguna opcion", "ninguna opción",
        "no es ninguna de esas", "no es ninguna de las anteriores", "nada de eso", "otra",
        "otro", "ninguno de esos", "no pasa eso", "tampoco", "no es eso", "no coincide",
        "ninguna de ellas", "ninguna de las tres opciones", "ninguna de las opciones mencionadas",
    }
    if limpio in patrones_rechazo:
        return True
    return bool(re.search(r"\b(?:ningun[ao]s?|no\s+es\s+ningun[ao]|nada\s+de\s+eso|otra\s+cosa)\b", limpio))


def generar_pregunta_descarte_secundario(sintoma_base: str, hipotesis_descartadas: List[str]) -> str:
    """Genera una pregunta contextualizada cuando el usuario descarta las opciones iniciales."""
    sintoma_lower = sintoma_base.lower() if sintoma_base else ""

    nombres_descarte = []
    for h in hipotesis_descartadas[:3]:
        desc = MAPA_DESCRIPCION_OPCION.get(h, h)
        if "(" in desc and ")" in desc:
            corto = desc.split("(")[-1].split(")")[0]
            nombres_descarte.append(corto)
        else:
            nombres_descarte.append(h.split()[0])

    texto_descarte = (
        f"Entendido, descartamos: {', '.join(nombres_descarte)}."
        if nombres_descarte
        else "Entendido, descartamos las opciones anteriores."
    )

    if any(w in sintoma_lower for w in ("arranc", "prende", "partida", "marcha", "llave")):
        return (
            f"🔍 {texto_descarte}\n\n"
            "Para precisar la causa del problema de arranque:\n"
            "• ¿Al dar arranque el motor gira con fuerza pero no enciende (como si estuviera ahogado de combustible)?\n"
            "• ¿Tiene que pisar el acelerador a fondo para que logre arrancar?\n"
            "• ¿O el motor gira pesado, lento o se queda mudo al girar la llave?\n\n"
            "👉 *Describe qué comportamiento nota para identificar la causa exacta.*"
        )
    elif any(w in sintoma_lower for w in ("vibr", "tiembl", "zapate", "sacud", "timon", "volante")):
        return (
            f"🔍 {texto_descarte}\n\n"
            "Para precisar el origen exacto de la vibración:\n"
            "• ¿La vibración se siente en el timón, en el pedal o en todo el piso/asiento del auto?\n"
            "• ¿Ocurre a cierta velocidad constante (ej. 80-100 km/h) o al acelerar en subida?\n\n"
            "👉 *Describe el comportamiento que nota para precisar la causa.*"
        )
    elif any(w in sintoma_lower for w in ("fren", "pedal", "pastill", "disco", "liquido")):
        return (
            f"🔍 {texto_descarte}\n\n"
            "Para precisar la causa en el sistema de frenos:\n"
            "• ¿El pedal se siente esponjoso o se va al fondo, o por el contrario se puso duro como piedra?\n"
            "• ¿Se escucha algún chillido constante o el auto tira hacia un lado al frenar?\n\n"
            "👉 *Indica qué detalle adicional observa al frenar.*"
        )
    elif any(w in sintoma_lower for w in ("embrag", "clutch", "caja", "cambio", "marcha")):
        return (
            f"🔍 {texto_descarte}\n\n"
            "Para precisar la causa en el embrague o transmisión:\n"
            "• ¿Cuesta meter los cambios (o raspa la caja), o el pedal se queda pegado en el fondo?\n"
            "• ¿El motor acelera (suben las RPM) pero el vehículo no gana velocidad (patina)?\n\n"
            "👉 *Describe qué síntoma adicional nota en los cambios o el pedal.*"
        )
    elif any(w in sintoma_lower for w in ("calienta", "temperatura", "refrigerante", "radiador")):
        return (
            f"🔍 {texto_descarte}\n\n"
            "Para precisar la causa del problema de temperatura:\n"
            "• ¿La temperatura sube solo en tráfico lento o también a velocidad en carretera?\n"
            "• ¿Nota consumo/pérdida de refrigerante o el electroventilador no enciende?\n\n"
            "👉 *Describe qué comportamiento observa en la temperatura.*"
        )
    else:
        return (
            f"🔍 {texto_descarte}\n\n"
            "Para dar con el diagnóstico exacto:\n"
            "Por favor describe qué otro detalle o comportamiento específico nota en el vehículo "
            "(por ejemplo: ruidos particulares, cuándo comenzó la falla o qué ocurre exactamente al presentarse).\n\n"
            "👉 *Escribe los detalles adicionales.*"
        )


def resolver_respuesta_autopregunta(
    texto_usuario: str,
    opciones: List[str],
    hipotesis: List[str],
) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Determina si el texto del usuario responde a una auto-pregunta técnica previa.
    Retorna: (índice 0-based, texto_opcion, clase_canonica_ml).
    """
    if not opciones:
        return None, None, None

    texto_limpio = texto_usuario.strip().lower().strip(" .,!¡¿?")

    # 1. Detección directa por número o palabra de orden
    patrones_numericos = [
        (r"^(?:opci[oó]n\s*|la\s*)?1\b", 0),
        (r"^(?:opci[oó]n\s*|la\s*)?2\b", 1),
        (r"^(?:opci[oó]n\s*|la\s*)?3\b", 2),
        (r"^(?:opci[oó]n\s*|la\s*)?4\b", 3),
        (r"^(?:opci[oó]n\s*|la\s*)?5\b", 4),
        (r"\b(?:primera|uno|1️⃣)\b", 0),
        (r"\b(?:segunda|dos|2️⃣)\b", 1),
        (r"\b(?:tercera|tres|3️⃣)\b", 2),
        (r"\b(?:cuarta|cuatro|4️⃣)\b", 3),
        (r"\b(?:quinta|cinco|5️⃣)\b", 4),
    ]
    for patron, idx in patrones_numericos:
        if re.search(patron, texto_limpio):
            if idx < len(opciones):
                hip = hipotesis[idx] if idx < len(hipotesis) else ""
                clase = MAPA_HIPOTESIS_A_CLASE_CANONICA.get(hip, hip)
                return idx, opciones[idx], clase

    # 2. Detección por concordancia de contenido con las opciones
    mejor_idx = None
    mejor_score = 0
    for idx, opt in enumerate(opciones):
        palabras_opt = [p for p in re.findall(r"\w+", opt.lower()) if len(p) > 3]
        coincidencias = sum(1 for p in palabras_opt if p in texto_limpio)
        if coincidencias > mejor_score and coincidencias >= 2:
            mejor_score = coincidencias
            mejor_idx = idx

    if mejor_idx is not None:
        hip = hipotesis[mejor_idx] if mejor_idx < len(hipotesis) else ""
        clase = MAPA_HIPOTESIS_A_CLASE_CANONICA.get(hip, hip)
        return mejor_idx, opciones[mejor_idx], clase

    return None, None, None
