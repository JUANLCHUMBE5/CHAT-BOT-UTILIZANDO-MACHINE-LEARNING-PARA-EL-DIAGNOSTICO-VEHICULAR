"""
Script de Evaluación y Validación Adversarial Ciega: FASE 11.6.2
Ejecuta 50 casos completamente inéditos a través del pipeline de CarBot
sin modificar ningún modelo, código, prompt, umbral ni regla heurística.
"""

import csv
import json
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from src.core.diagnostico.taxonomia_sistemas import obtener_macro_sistema
from src.core.gestor_diagnostico import GestorDiagnostico
from src.infrastructure.container import ServiceContainer

# 50 CASOS COMPLETAMENTE NUEVOS E INÉDITOS PARA FASE 11.6.2 BLIND
CASOS_BLIND_50 = [
    # ------------------------------------------------------------
    # 10 CASOS TÉCNICOS
    # ------------------------------------------------------------
    {
        "id": "BLIND_01",
        "tipo": "TECNICO",
        "texto": "Prueba de caudal de retorno en probetas graduadas arroja 85 ml/min en cilindro 4 frente a 15 ml/min en los restantes bajo presión de 1350 bar en rampa common rail.",
        "ground_truth": "Inyectores sucios o filtro de combustible obstruido",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_02",
        "tipo": "TECNICO",
        "texto": "Al bombear el pedal de freno con motor apagado la altura se mantiene, pero al encender el motor el pedal desciende gradualmente hasta el piso sin registrar fugas externas en tuberías ni mordazas.",
        "ground_truth": "Fuga hidraulica o aire en el sistema de frenos",
        "macro_esperado": "FRENOS",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_03",
        "tipo": "TECNICO",
        "texto": "En fosa de alineación con placas de holgura se evidencia juego axial de 3.5 mm en la rótula de suspensión inferior derecha al palanquear el brazo oscilante.",
        "ground_truth": "Amortiguadores reventados o bujes de suspension gastados",
        "macro_esperado": "SUSPENSION_CHASIS",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_04",
        "tipo": "TECNICO",
        "texto": "Prueba de conductancia con analizador digital de baterías reporta 210 CCA en batería etiquetada de 650 CCA con resistencia interna elevada a 28 miliohmios y 12.2V en reposo tras carga completa.",
        "ground_truth": "Bateria descargada o bornes sulfatados",
        "macro_esperado": "ELECTRICO",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_05",
        "tipo": "TECNICO",
        "texto": "El detector químico de fugas de combustión con líquido azul bromotimol vira a color amarillo verdoso en la boca de llenado del radiador al acelerar a 2000 RPM.",
        "ground_truth": "Empaque de culata soplado o danado",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_06",
        "tipo": "TECNICO",
        "texto": "Al drenar el lubricante de la transmisión manual se extrae apenas 600 ml de valvolina quemada con presencia visible de viruta metálica dorada de los anillos sincronizadores de segunda y tercera marcha.",
        "ground_truth": "Falta o degradacion de aceite de caja de cambios",
        "macro_esperado": "TRANSMISION",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_07",
        "tipo": "TECNICO",
        "texto": "El osciloscopio en el conector del motor paso a paso de ralentí IAC muestra pulso PWM constante pero el obturador cónico permanece atascado mecánicamente en su asiento por lodo aceitoso.",
        "ground_truth": "Cuerpo de aceleracion o valvula IAC sucia",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_08",
        "tipo": "TECNICO",
        "texto": "El vacuómetro conectado entre el múltiple de admisión y el servofreno booster marca 19 inHg estables, pero al pisar el pedal se oye escape de aire en el habitáculo y el vacío cae a cero.",
        "ground_truth": "Falla en servofreno (booster) o linea de vacio",
        "macro_esperado": "FRENOS",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_09",
        "tipo": "TECNICO",
        "texto": "Al registrar simultáneamente con osciloscopio la señal digital del CMP de árbol de levas y la rueda fónica del CKP se observa desfase de 18 grados por estiramiento de la cadena de distribución.",
        "ground_truth": "Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_10",
        "tipo": "TECNICO",
        "texto": "Caída de tensión entre terminal 30 y terminal M del solenoide de arranque mide 11.4V con llave en START pero el inducido del motor de arranque no gira y los carbones miden 3 mm de longitud.",
        "ground_truth": "Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)",
        "macro_esperado": "ELECTRICO",
        "dtc": "N/A"
    },

    # ------------------------------------------------------------
    # 10 CASOS COLOQUIALES
    # ------------------------------------------------------------
    {
        "id": "BLIND_11",
        "tipo": "COLOQUIAL",
        "texto": "Compadre, cada vez que salgo a la Panamericana y agarro entre 80 y 100 por hora el volante me tiembla como lavadora centrifugando, pero si bajo a 60 se calma solito.",
        "ground_truth": "Llantas desbalanceadas o desalineadas",
        "macro_esperado": "SUSPENSION_CHASIS",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_12",
        "tipo": "COLOQUIAL",
        "texto": "El carro anda en tres patas, tiembla todo el motor como si quisiera saltar del capot y cuando acelero huele a gasolina cruda por el tubo de escape.",
        "ground_truth": "Falla en bujias o bobinas de encendido (misfire)",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_13",
        "tipo": "COLOQUIAL",
        "texto": "Maestro, cuando voy a estacionar y piso despacito el freno suena como si estuviera afilando un cuchillo viejo, un chillido bien agudo que da vergüenza.",
        "ground_truth": "Desgaste de pastillas y zapatas de freno",
        "macro_esperado": "FRENOS",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_14",
        "tipo": "COLOQUIAL",
        "texto": "Quiero adelantar en una subida empinada, piso a fondo el acelerador, el motor ruge a todo dar pero el auto parece carreta y no tiene pique ni avanza.",
        "ground_truth": "Disco de embrague desgastado o patinando",
        "macro_esperado": "TRANSMISION",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_15",
        "tipo": "COLOQUIAL",
        "texto": "Si estoy andando rápido en pista libre la temperatura está en la mitad bien bonita, pero apenas me meto al tráfico pesado se dispara la aguja al rojo y bota agua.",
        "ground_truth": "Falla en termostato o motoventilador de radiador",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_16",
        "tipo": "COLOQUIAL",
        "texto": "De noche cuando prendo las luces y el aire el carro se siente pesado, la luz del tablero parpadea tenue y en la pantalla del estéreo sale aviso de batería.",
        "ground_truth": "Alternador defectuoso o placa de diodos quemada",
        "macro_esperado": "ELECTRICO",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_17",
        "tipo": "COLOQUIAL",
        "texto": "El carro me deja botado cuando le queda un cuarto de tanque en subidas, empieza a toser como si se quedara sin combustible y en los asientos de atrás se siente un zumbido fuerte.",
        "ground_truth": "Bomba de gasolina quemada o con baja presion",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_18",
        "tipo": "COLOQUIAL",
        "texto": "Después de manejar como media hora siento que la llanta delantera derecha echa un calor infernal y huele a balata quemada, como si se quedara frenada solita.",
        "ground_truth": "Caliper de freno trabado o mordaza pegada (piston agarrotado)",
        "macro_esperado": "FRENOS",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_19",
        "tipo": "COLOQUIAL",
        "texto": "Paso por cualquier rompemuelle o bache y la cola del carro parece bote en el mar, se queda rebotando cuatro veces arriba y abajo.",
        "ground_truth": "Amortiguadores reventados o bujes de suspension gastados",
        "macro_esperado": "SUSPENSION_CHASIS",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_20",
        "tipo": "COLOQUIAL",
        "texto": "Ayer lo dejé estacionado bien y hoy en la mañana al querer prender solo sonó un tac tac bien bajito y se apagaron hasta los números del reloj.",
        "ground_truth": "Bateria descargada o bornes sulfatados",
        "macro_esperado": "ELECTRICO",
        "dtc": "N/A"
    },

    # ------------------------------------------------------------
    # 10 CASOS AMBIGUOS
    # ------------------------------------------------------------
    {
        "id": "BLIND_21",
        "tipo": "AMBIGUO",
        "texto": "Siento que el auto no tiene la misma fuerza de antes, le cuesta levantar velocidad en las avenidas.",
        "ground_truth": "Inyectores sucios o filtro de combustible obstruido",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_22",
        "tipo": "AMBIGUO",
        "texto": "El carro no quiere encender hoy día en la cochera, le doy a la llave y no prende.",
        "ground_truth": "Bateria descargada o bornes sulfatados",
        "macro_esperado": "ELECTRICO",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_23",
        "tipo": "AMBIGUO",
        "texto": "Se siente un golpe seco en la parte de abajo cuando paso por pistas en mal estado.",
        "ground_truth": "Amortiguadores reventados o bujes de suspension gastados",
        "macro_esperado": "SUSPENSION_CHASIS",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_24",
        "tipo": "AMBIGUO",
        "texto": "A veces cuando voy despacio en segunda me da unos jalones suaves pero no pasa siempre.",
        "ground_truth": "Falla en bujias o bobinas de encendido (misfire)",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_25",
        "tipo": "AMBIGUO",
        "texto": "Hay un zumbido sordo en la parte delantera del vehículo que se nota cuando supero los 40 km/h.",
        "ground_truth": "Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura)",
        "macro_esperado": "SUSPENSION_CHASIS",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_26",
        "tipo": "AMBIGUO",
        "texto": "Cuando estoy parado en el semáforo siento que el motor no está serenito, vibra un poquito.",
        "ground_truth": "Cuerpo de aceleracion o valvula IAC sucia",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_27",
        "tipo": "AMBIGUO",
        "texto": "Noto una vibración molesta adelante pero no estoy seguro si viene de las ruedas o de los frenos.",
        "ground_truth": "Llantas desbalanceadas o desalineadas",
        "macro_esperado": "SUSPENSION_CHASIS",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_28",
        "tipo": "AMBIGUO",
        "texto": "El carro me está rindiendo muy pocos kilómetros por galón últimamente y huele raro el humo.",
        "ground_truth": "Falla en sensor de oxigeno o mezcla rica",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_29",
        "tipo": "AMBIGUO",
        "texto": "Tengo que rellenar el depósito de agua de vez en cuando porque se baja de nivel.",
        "ground_truth": "Fuga en mangueras de refrigerante o radiador picado",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_30",
        "tipo": "AMBIGUO",
        "texto": "A veces al subirme al vehículo siento un olor como a combustible pero no veo manchas abajo.",
        "ground_truth": "Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },

    # ------------------------------------------------------------
    # 10 CASOS CON DTC
    # ------------------------------------------------------------
    {
        "id": "BLIND_31",
        "tipo": "DTC",
        "texto": "Escáner OBD-II registra código de avería P0304 de forma permanente. Hay fallo de combustión confirmado en el cilindro 4 bajo aceleración sostenida.",
        "ground_truth": "Falla en bujias o bobinas de encendido (misfire)",
        "macro_esperado": "MOTOR",
        "dtc": "P0304"
    },
    {
        "id": "BLIND_32",
        "tipo": "DTC",
        "texto": "Luz de fallo motor encendida con código P0171 sistema demasiado pobre banco 1. El ajuste a largo plazo LTFT se sitúa en +22% en ralentí.",
        "ground_truth": "Falla en sensor de oxigeno o mezcla rica",
        "macro_esperado": "MOTOR",
        "dtc": "P0171"
    },
    {
        "id": "BLIND_33",
        "tipo": "DTC",
        "texto": "La memoria de la computadora reporta código DTC P0420 sobre baja eficiencia del convertidor catalítico en banco 1 tras prueba dinámica de gases.",
        "ground_truth": "Convertidor catalitico ineficiente u obstruido (DTC P0420 / P0430)",
        "macro_esperado": "MOTOR",
        "dtc": "P0420"
    },
    {
        "id": "BLIND_34",
        "tipo": "DTC",
        "texto": "Código DTC P0505 registrado en ECU con ralentí acelerado a 1400 RPM y fluctuaciones erráticas al conectar el aire acondicionado.",
        "ground_truth": "Cuerpo de aceleracion o valvula IAC sucia",
        "macro_esperado": "MOTOR",
        "dtc": "P0505"
    },
    {
        "id": "BLIND_35",
        "tipo": "DTC",
        "texto": "Código DTC P0335 activo en el módulo de motor. Se pierde la señal del sensor de posición de cigüeñal CKP cuando el bloque toma temperatura.",
        "ground_truth": "Falla en sensor de posicion de cigueñal (CKP) o arbol de levas (CMP)",
        "macro_esperado": "MOTOR",
        "dtc": "P0335"
    },
    {
        "id": "BLIND_36",
        "tipo": "DTC",
        "texto": "Escaneo automotriz arroja código de falla P0128. La temperatura de trabajo del motor no alcanza el umbral de regulación por termostato trabado abierto.",
        "ground_truth": "Falla en termostato o motoventilador de radiador",
        "macro_esperado": "MOTOR",
        "dtc": "P0128"
    },
    {
        "id": "BLIND_37",
        "tipo": "DTC",
        "texto": "Se detecta código de falla P0562 tensión de sistema baja. El regulador del alternador no suministra la tensión necesaria con cargas eléctricas activadas.",
        "ground_truth": "Alternador defectuoso o placa de diodos quemada",
        "macro_esperado": "ELECTRICO",
        "dtc": "P0562"
    },
    {
        "id": "BLIND_38",
        "tipo": "DTC",
        "texto": "Módulo electrónico de frenos ABS enciende testigo de avería con código de falla C0040 por circuito abierto en captador de velocidad de rueda.",
        "ground_truth": "Falla en sensor de velocidad de rueda ABS",
        "macro_esperado": "FRENOS",
        "dtc": "C0040"
    },
    {
        "id": "BLIND_39",
        "tipo": "DTC",
        "texto": "ECU de transmisión automática almacena código DTC P0730 relación de engranaje incorrecta. La caja patina severamente entre marchas.",
        "ground_truth": "Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
        "macro_esperado": "TRANSMISION",
        "dtc": "P0730"
    },
    {
        "id": "BLIND_40",
        "tipo": "DTC",
        "texto": "DTC P0442 registrado por microfuga detectada en el circuito de control de emisiones evaporativas EVAP mediante prueba de vacío de cánister.",
        "ground_truth": "Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)",
        "macro_esperado": "MOTOR",
        "dtc": "P0442"
    },

    # ------------------------------------------------------------
    # 10 CASOS DIFERENCIALES / ADVERSARIALES
    # ------------------------------------------------------------
    {
        "id": "BLIND_41",
        "tipo": "DIFERENCIAL",
        "texto": "A 100 km/h en autopista el timón vibra fuertemente en mis manos, pero al aplicar el pedal de freno la desaceleración es completamente lisa y no vibra para nada.",
        "ground_truth": "Llantas desbalanceadas o desalineadas",
        "macro_esperado": "SUSPENSION_CHASIS",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_42",
        "tipo": "DIFERENCIAL",
        "texto": "Se reemplazaron las bujías por unas nuevas de platino originales, pero el cilindro 2 sigue fallando sin chispa en la bobina individual.",
        "ground_truth": "Falla en bujias o bobinas de encendido (misfire)",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_43",
        "tipo": "DIFERENCIAL",
        "texto": "Manejando en quinta a 90 km/h en carretera despejada el motor perdió toda la fuerza y se atrancó de golpe al pisar el acelerador.",
        "ground_truth": "Bomba de gasolina quemada o con baja presion",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_44",
        "tipo": "DIFERENCIAL",
        "texto": "El carro se me apagó rodando en un semáforo y ahora que está completamente detenido le doy arranque y el arrancador no gira absolutamente nada, se quedó mudo.",
        "ground_truth": "Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)",
        "macro_esperado": "ELECTRICO",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_45",
        "tipo": "DIFERENCIAL",
        "texto": "El pedal de freno se va hasta el fondo con tacto esponjoso al frenar en las esquinas, pero el motor no presenta fugas de vacío y el booster mantiene su retención.",
        "ground_truth": "Fuga hidraulica o aire en el sistema de frenos",
        "macro_esperado": "FRENOS",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_46",
        "tipo": "DIFERENCIAL",
        "texto": "El manómetro acoplado a la línea de combustible marca apenas 22 psi bajo aceleración brusca, aunque la compresión de los cuatro cilindros está perfecta en 165 psi parejo.",
        "ground_truth": "Bomba de gasolina quemada o con baja presion",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_47",
        "tipo": "DIFERENCIAL",
        "texto": "Subiendo una cuesta en cuarta marcha el velocímetro se queda en 50 km/h mientras el tacómetro se dispara de 2200 a 4500 RPM sin acelerar el coche.",
        "ground_truth": "Disco de embrague desgastado o patinando",
        "macro_esperado": "TRANSMISION",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_48",
        "tipo": "DIFERENCIAL",
        "texto": "Presenta ralentí inestable que sube y baja con código de falla P0171, y al rociar limpiador de carburador en la manguera de vacío del múltiple el motor empareja de inmediato.",
        "ground_truth": "Falla en servofreno (booster) o linea de vacio",
        "macro_esperado": "FRENOS",
        "dtc": "P0171"
    },
    {
        "id": "BLIND_49",
        "tipo": "DIFERENCIAL",
        "texto": "El electroventilador enciende en alta velocidad continuamente y la manguera superior está caliente, pero el motor NO se calienta ni supera los 88 grados en el indicador.",
        "ground_truth": "Falla en termostato o motoventilador de radiador",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
    {
        "id": "BLIND_50",
        "tipo": "DIFERENCIAL",
        "texto": "El motor recalienta al exigirle carga en subida pero NO pierde refrigerante por ninguna manguera ni baja el nivel del radiador.",
        "ground_truth": "Falla en termostato o motoventilador de radiador",
        "macro_esperado": "MOTOR",
        "dtc": "N/A"
    },
]

KEYWORDS_RELEVANCIA = {
    "misfire": ["misfire", "bujia", "bobina", "p0300", "p0301", "p0302", "p0303", "p0304", "combustion"],
    "bujia": ["misfire", "bujia", "bobina", "p0300", "p0301", "p0302", "p0303", "p0304", "combustion"],
    "bomba de gasolina": ["bomba", "combustible", "presion", "tanque", "caudal", "p0087", "aforador"],
    "inyectores": ["inyector", "inyectores", "riel", "combustible", "limpieza", "filtro", "scv"],
    "sensor de oxigeno": ["sensor", "oxigeno", "mezcla", "lambda", "p0171", "p0172", "p0420", "catalizador", "maf", "map"],
    "catalizador": ["catalizador", "p0420", "contrapresion", "escape", "emisiones", "eficiencia"],
    "valvula iac": ["iac", "cuerpo de aceleracion", "ralenti", "marcha minima", "p0505", "p0506", "mariposa", "etcs"],
    "cuerpo de aceleracion": ["iac", "cuerpo de aceleracion", "ralenti", "marcha minima", "p0505", "p0506", "mariposa", "etcs"],
    "culata": ["culata", "empaque", "sobrecalentamiento", "co2", "refrigerante", "burbujas", "mayonesa"],
    "termostato": ["termostato", "motoventilador", "ventilador", "refrigeracion", "p0128", "temperatura", "purga", "radiador"],
    "aceite": ["aceite", "presion de aceite", "bomba de aceite", "taque", "punterias", "anillos", "retenes", "humo azul", "pcv"],
    "embrague": ["embrague", "clutch", "disco", "prensa", "bombin", "esclavo", "patina", "calado"],
    "freno": ["freno", "pastilla", "disco", "alabeo", "dtv", "liquido", "purga", "booster", "servofreno", "caliper"],
    "pastilla": ["freno", "pastilla", "disco", "alabeo", "dtv", "liquido", "purga", "booster", "servofreno", "caliper"],
    "caliper": ["caliper", "freno", "embolo", "traba", "pastilla", "mordaza"],
    "bateria": ["bateria", "arranque", "arrancador", "solenoide", "terminal 50", "clac", "alternador", "carga", "p0562"],
    "arranque": ["arranque", "arrancador", "solenoide", "terminal 50", "clac", "bateria"],
    "alternador": ["alternador", "carga", "diodos", "regulador", "lin", "p0562", "bateria", "voltaje"],
    "caja": ["caja", "transmision", "cvt", "dsg", "dualogic", "atf", "solenoide", "p0841", "p0700", "valvolina", "robotizada"],
    "transmision": ["caja", "transmision", "cvt", "dsg", "dualogic", "atf", "solenoide", "p0841", "p0700", "valvolina", "robotizada"],
    "suspension": ["amortiguador", "buje", "suspension", "llanta", "balanceo", "alineacion", "rebote", "trapecio", "rotula"],
    "amortiguador": ["amortiguador", "buje", "suspension", "llanta", "balanceo", "alineacion", "rebote", "trapecio", "rotula"],
    "llantas": ["balanceo", "alineacion", "llanta", "convergencia", "camber", "neumatico", "vibracion", "desbalance"],
    "desbalanceadas": ["balanceo", "alineacion", "llanta", "convergencia", "camber", "neumatico", "vibracion", "desbalance"],
    "abs": ["abs", "velocidad", "rueda", "c0035", "c0040", "c1101", "sensor"],
    "evap": ["evap", "canister", "purga", "valvula", "p0440", "p0442", "p0455", "emisiones"],
    "servofreno": ["servofreno", "booster", "vacio", "pedal duro", "diafragma"],
    "rodamiento": ["rodamiento", "rodaje", "maza", "rueda", "ruleman", "zumbido"],
    "ckp": ["ckp", "cmp", "cigueñal", "arbol de levas", "posicion", "p0335", "p0340"]
}

def es_doc_relevante(titulo: str, contenido: str, falla_esperada: str, dtc_esperado: str = "") -> bool:
    tit_low = titulo.lower()
    cont_low = (contenido or "")[:1500].lower()
    falla_low = falla_esperada.lower()

    if dtc_esperado and dtc_esperado != "N/A" and dtc_esperado.lower() in tit_low:
        return True

    for grupo, palabras in KEYWORDS_RELEVANCIA.items():
        if grupo in falla_low:
            if any(p in tit_low for p in palabras):
                return True
            coincidencias = sum(1 for p in palabras if p in cont_low)
            if coincidencias >= 2:
                return True
    return False


def ejecutar_validacion_blind_50():
    print("Iniciando FASE 11.6.2: Validación Adversarial Ciega Final...")
    gestor = GestorDiagnostico()
    motor_rag = ServiceContainer.get_motor_rag()

    resultados = []
    errores = []

    conteo_top1 = 0
    conteo_top3 = 0
    conteo_macro = 0
    suma_confianza = 0.0

    hit1_rag = 0
    hit3_rag = 0
    hit5_rag = 0
    suma_rr = 0.0

    categorias = ["TECNICO", "COLOQUIAL", "AMBIGUO", "DTC", "DIFERENCIAL"]
    stats_cat = {c: {"top1": 0, "top3": 0, "macro": 0, "total": 0} for c in categorias}

    for i, c in enumerate(CASOS_BLIND_50, start=1):
        cid = c["id"]
        tipo = c["tipo"]
        texto = c["texto"]
        gt = c["ground_truth"]
        macro_esp = c["macro_esperado"]
        dtc_esp = c["dtc"]

        stats_cat[tipo]["total"] += 1

        # Ejecución a través del pipeline completo de CarBot
        inicio_t = time.perf_counter()
        res = gestor.procesar_consulta_texto(texto, diferir_encolado_persistente=True)
        duracion_ms = int((time.perf_counter() - inicio_t) * 1000)

        top1_falla = res.diagnostico_ml
        conf1 = round(float(res.confianza_ml), 4)
        preds = res.predicciones_ml

        top2_falla = preds[1].falla if len(preds) > 1 else "DESCONOCIDO"
        conf2 = round(float(preds[1].probabilidad), 4) if len(preds) > 1 else 0.0
        top3_falla = preds[2].falla if len(preds) > 2 else "DESCONOCIDO"
        conf3 = round(float(preds[2].probabilidad), 4) if len(preds) > 2 else 0.0

        macro_pred = obtener_macro_sistema(top1_falla)

        top1_ok = 1 if (top1_falla == gt) else 0
        top3_ok = 1 if (gt in [top1_falla, top2_falla, top3_falla]) else 0
        macro_ok = 1 if (macro_pred == macro_esp) else 0

        if top1_ok:
            conteo_top1 += 1
            stats_cat[tipo]["top1"] += 1
        if top3_ok:
            conteo_top3 += 1
            stats_cat[tipo]["top3"] += 1
        if macro_ok:
            conteo_macro += 1
            stats_cat[tipo]["macro"] += 1

        suma_confianza += conf1

        # Evaluación RAG
        dtcs_in = [dtc_esp] if dtc_esp and dtc_esp != "N/A" else []
        top_fallas_rag = [{"falla": p.falla, "probabilidad": p.probabilidad} for p in preds]

        from src.infrastructure.rag.query_builder import construir_consulta_hibrida
        from src.infrastructure.rag.relevance_filter import reordenar_candidatos_rag

        consulta_hibrida = construir_consulta_hibrida(
            consulta_usuario=texto,
            macro_sistema=macro_pred,
            top_fallas=top_fallas_rag,
            codigos_dtc=dtcs_in,
        )
        consulta_expandida = motor_rag._expandir_consulta(consulta_hibrida)
        consulta_vec = motor_rag.vectorizador.transform([consulta_expandida]).toarray().astype("float32")
        import faiss
        faiss.normalize_L2(consulta_vec)
        sims_faiss, idxs_faiss = motor_rag.faiss_index.search(consulta_vec, k=15)

        cands = []
        for kidx in range(len(idxs_faiss[0])):
            didx = int(idxs_faiss[0][kidx])
            if 0 <= didx < len(motor_rag.documentos):
                cands.append({
                    "indice": didx,
                    "titulo": motor_rag.titulos[didx],
                    "documento": motor_rag.documentos[didx],
                    "similitud": float(sims_faiss[0][kidx]),
                    "metadatos": motor_rag.metadatos_procedimientos[didx] if didx < len(motor_rag.metadatos_procedimientos) else {}
                })
        cands_reord = reordenar_candidatos_rag(
            cands,
            macro_sistema=macro_pred,
            top_fallas=top_fallas_rag,
            codigos_dtc=dtcs_in,
            confianza_ml=conf1
        )

        rank_hit = None
        for rk, cand in enumerate(cands_reord[:5], start=1):
            if es_doc_relevante(cand["titulo"], cand["documento"], gt, dtc_esp):
                rank_hit = rk
                break

        h1 = 1 if (rank_hit == 1) else 0
        h3 = 1 if (rank_hit is not None and rank_hit <= 3) else 0
        h5 = 1 if (rank_hit is not None and rank_hit <= 5) else 0
        rr = (1.0 / rank_hit) if rank_hit is not None else 0.0

        if h1: hit1_rag += 1
        if h3: hit3_rag += 1
        if h5: hit5_rag += 1
        suma_rr += rr

        fila = {
            "id": cid,
            "tipo_caso": tipo,
            "texto_ingresado": texto,
            "ground_truth": gt,
            "macro_sistema_esperado": macro_esp,
            "top1_predicho": top1_falla,
            "confianza_top1": conf1,
            "top2_predicho": top2_falla,
            "confianza_top2": conf2,
            "top3_predicho": top3_falla,
            "confianza_top3": conf3,
            "macro_sistema_predicho": macro_pred,
            "top1_correcto": top1_ok,
            "top3_correcto": top3_ok,
            "macro_correcto": macro_ok,
            "dtc_codigo": dtc_esp,
            "rag_titulo": res.titulo_manual,
            "rag_similitud": round(res.similitud_rag, 4),
            "hit_1_rag": h1,
            "hit_3_rag": h3,
            "hit_5_rag": h5,
            "mrr_rag": round(rr, 4),
            "tiempo_ms": duracion_ms
        }
        resultados.append(fila)

        if not top1_ok:
            # Clasificación de causa del error
            if tipo == "AMBIGUO":
                causa_cat = "B) Ambigüedad legítima"
            elif dtc_esp and dtc_esp != "N/A" and top1_falla != gt:
                causa_cat = "E) Problema política de fusión"
            elif conf1 >= 0.75:
                causa_cat = "A) Limitación del dataset"
            else:
                causa_cat = "C) Problema TF-IDF/SVM"

            errores.append({
                "id": cid,
                "categoria": tipo,
                "consulta": texto,
                "ground_truth": gt,
                "top1_predicho": top1_falla,
                "confianza_top1": conf1,
                "top2_predicho": top2_falla,
                "confianza_top2": conf2,
                "top3_predicho": top3_falla,
                "confianza_top3": conf3,
                "macro_esperado": macro_esp,
                "macro_predicho": macro_pred,
                "rag_titulo": res.titulo_manual,
                "dtc_codigo": dtc_esp,
                "causa_clasificada": causa_cat
            })

    total = len(CASOS_BLIND_50)
    top1_pct = round(conteo_top1 / total * 100, 2)
    top3_pct = round(conteo_top3 / total * 100, 2)
    macro_pct = round(conteo_macro / total * 100, 2)
    conf_prom = round(suma_confianza / total, 4)
    err_75 = sum(1 for e in errores if e["confianza_top1"] >= 0.75)

    rag_h1_pct = round(hit1_rag / total * 100, 2)
    rag_h3_pct = round(hit3_rag / total * 100, 2)
    rag_h5_pct = round(hit5_rag / total * 100, 2)
    mrr_prom = round(suma_rr / total, 3)

    print("\n" + "="*60)
    print("RESULTADOS FASE 11.6.2 BLIND (50 CASOS INÉDITOS)")
    print("="*60)
    print(f"Top-1 Global:       {conteo_top1}/{total} ({top1_pct}%)")
    print(f"Top-3 Global:       {conteo_top3}/{total} ({top3_pct}%)")
    print(f"Macro-Sistema:      {conteo_macro}/{total} ({macro_pct}%)")
    print(f"Confianza Promedio: {conf_prom}")
    print(f"Errores >= 75%:     {err_75}")
    print(f"RAG Hit@1:          {hit1_rag}/{total} ({rag_h1_pct}%)")
    print(f"RAG Hit@3:          {hit3_rag}/{total} ({rag_h3_pct}%)")
    print(f"RAG Hit@5:          {hit5_rag}/{total} ({rag_h5_pct}%)")
    print(f"RAG MRR:            {mrr_prom}")

    print("\n--- DESGLOSE POR CATEGORÍA ---")
    for cat, st in stats_cat.items():
        t1 = st["top1"]
        t3 = st["top3"]
        tot = st["total"]
        print(f"{cat:12s}: Top-1 {t1}/{tot} ({t1/tot*100:.0f}%) | Top-3 {t3}/{tot} ({t3/tot*100:.0f}%) | Macro {st['macro']}/{tot}")

    # Guardar CSV de 50 Casos
    out_csv_50 = BASE_DIR / "docs" / "fase11_6" / "FASE11_6_2_50_CASOS.csv"
    with open(out_csv_50, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = list(resultados[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(resultados)
    print(f"\nArchivo guardado: {out_csv_50}")

    # Guardar CSV de Errores
    out_csv_err = BASE_DIR / "docs" / "fase11_6" / "FASE11_6_2_ERRORES.csv"
    with open(out_csv_err, "w", newline="", encoding="utf-8-sig") as f:
        if errores:
            fieldnames = list(errores[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(errores)
    print(f"Archivo guardado: {out_csv_err}")

    # Guardar JSON de Métricas
    metricas = {
        "fase": "FASE_11_6_2_BLIND",
        "fecha": "2026-09-19",
        "total_casos": total,
        "top1_global": conteo_top1,
        "top1_pct": top1_pct,
        "top3_global": conteo_top3,
        "top3_pct": top3_pct,
        "macro_sistema_global": conteo_macro,
        "macro_sistema_pct": macro_pct,
        "confianza_promedio": conf_prom,
        "errores_alta_confianza_75": err_75,
        "total_errores": len(errores),
        "rag": {
            "hit1": hit1_rag,
            "hit1_pct": rag_h1_pct,
            "hit3": hit3_rag,
            "hit3_pct": rag_h3_pct,
            "hit5": hit5_rag,
            "hit5_pct": rag_h5_pct,
            "mrr": mrr_prom
        },
        "por_categoria": stats_cat
    }
    out_json = BASE_DIR / "docs" / "fase11_6" / "FASE11_6_2_METRICAS.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)
    print(f"Archivo guardado: {out_json}")


if __name__ == "__main__":
    ejecutar_validacion_blind_50()
