"""
Datos de Ground Truth a Priori para los 50 Casos de Taller (1er Grupo).
"""

from typing import Any, Dict, List

GROUND_TRUTH_50: List[Dict[str, Any]] = [
    {
        "id": "G1_01",
        "falla_esperada": "Falla en sensor de posicion de cigueñal (CKP) o bobinas por fatiga termica",
        "claves_estrictas": ["cigueñal", "ckp", "bujias o bobinas"],
        "claves_diferenciales": ["bomba de gasolina", "presion de combustible", "rele efi"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["985", "1600", "ohm", "3.1", "3.5", "bar"]
    },
    {
        "id": "G1_02",
        "falla_esperada": "Bomba de gasolina quemada o con baja presion",
        "claves_estrictas": ["bomba de gasolina", "baja presion"],
        "claves_diferenciales": ["inyectores", "filtro de combustible", "bujias"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": True,
        "valores_tolerancias_esperadas": ["bar", "psi", "l/min"]
    },
    {
        "id": "G1_03",
        "falla_esperada": "Cuerpo de aceleracion o valvula IAC sucia",
        "claves_estrictas": ["cuerpo de aceleracion", "iac"],
        "claves_diferenciales": ["servofreno", "vacio", "multiple", "canister"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["rpm", "reaprendizaje"]
    },
    {
        "id": "G1_04",
        "falla_esperada": "Inyectores sucios o filtro de combustible obstruido (falla termica de inyector)",
        "claves_estrictas": ["inyector", "inyectores"],
        "claves_diferenciales": ["valvula", "compresion", "bujias"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["12", "14", "ohm", "psi"]
    },
    {
        "id": "G1_05",
        "falla_esperada": "Falla en bujias o bobinas de encendido (misfire)",
        "claves_estrictas": ["bujias o bobinas", "misfire", "bobina"],
        "claves_diferenciales": ["inyectores", "gdi"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["p0303", "nm"]
    },
    {
        "id": "G1_06",
        "falla_esperada": "Falla en sensor de oxigeno o mezcla rica / Fuga de vacio en admision",
        "claves_estrictas": ["mezcla", "sensor de oxigeno", "vacio"],
        "claves_diferenciales": ["multiple", "inyectores", "cuerpo de aceleracion"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["p0171", "%", "rpm"]
    },
    {
        "id": "G1_07",
        "falla_esperada": "Falla en sistema EVAP / Valvula de purga del canister trabada abierta",
        "claves_estrictas": ["canister", "evap", "purga", "inyectores"],
        "claves_diferenciales": ["bomba de gasolina", "sensor de oxigeno"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": True,
        "valores_tolerancias_esperadas": ["vacio", "bar"]
    },
    {
        "id": "G1_08",
        "falla_esperada": "Fuga o baja presion en sistema Common Rail Diesel (retorno excesivo en inyector)",
        "claves_estrictas": ["common rail", "retorno", "inyector"],
        "claves_diferenciales": ["bomba", "filtro"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["bar", "ml", "min"]
    },
    {
        "id": "G1_09",
        "falla_esperada": "Inyectores goteando en reposo o Sensor ECT descalibrado",
        "claves_estrictas": ["inyectores", "sensor ect", "bomba de gasolina", "presion de combustible"],
        "claves_diferenciales": ["bujias", "cuerpo de aceleracion"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["bar", "min"]
    },
    {
        "id": "G1_10",
        "falla_esperada": "Faja o cadena de distribucion destensada o con salto de punto",
        "claves_estrictas": ["distribucion", "faja", "cadena"],
        "claves_diferenciales": ["sincronizacion variable", "vvt"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["diente", "marcas", "inhg"]
    },
    {
        "id": "G1_11",
        "falla_esperada": "Convertidor catalitico ineficiente o agotado",
        "claves_estrictas": ["catalizador", "catalitico", "p0420", "sensor de oxigeno"],
        "claves_diferenciales": ["mezcla", "inyectores"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["p0420", "v", "volt"]
    },
    {
        "id": "G1_12",
        "falla_esperada": "Perdida de compresion por valvula de escape quemada o anillos en cilindro 1",
        "claves_estrictas": ["compresion", "valvula", "anillos", "empaque de culata"],
        "claves_diferenciales": ["bujias o bobinas", "inyectores", "misfire"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["150", "90", "psi", "compresion"]
    },
    {
        "id": "G1_13",
        "falla_esperada": "Diafragma del regulador de presion de combustible roto / Mezcla rica",
        "claves_estrictas": ["regulador", "presion de combustible", "mezcla", "humo negro"],
        "claves_diferenciales": ["inyectores", "sensor de oxigeno"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["bar", "psi"]
    },
    {
        "id": "G1_14",
        "falla_esperada": "Bomba de gasolina quemada o con baja presion / filtro sumergido",
        "claves_estrictas": ["bomba de gasolina", "baja presion"],
        "claves_diferenciales": ["filtro de combustible", "inyectores"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": True,  # Falla dependiente del nivel de tanque
        "valores_tolerancias_esperadas": ["bar", "psi"]
    },
    {
        "id": "G1_15",
        "falla_esperada": "Falla en inyector 2 o circuito de cilindro 2",
        "claves_estrictas": ["inyector", "inyectores", "p0202"],
        "claves_diferenciales": ["bujias o bobinas", "compresion", "valvula"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["12", "14", "ohm", "ms"]
    },
    {
        "id": "G1_16",
        "falla_esperada": "Fuga interna o aire en el sistema de frenos / Cilindro maestro defectuoso",
        "claves_estrictas": ["fuga hidraulica o aire", "frenos", "cilindro maestro", "bomba de freno"],
        "claves_diferenciales": ["pastillas", "servofreno"],
        "macro_sistema": "FRENOS",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["purga", "presion"]
    },
    {
        "id": "G1_17",
        "falla_esperada": "Falla en servofreno (booster) o linea de vacio",
        "claves_estrictas": ["servofreno", "booster", "vacio"],
        "claves_diferenciales": ["fuga hidraulica", "pastillas"],
        "macro_sistema": "FRENOS",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["inhg", "vacio", "manguera"]
    },
    {
        "id": "G1_18",
        "falla_esperada": "Caliper trabado o flexible colapsado / Desgaste de pastillas y zapatas",
        "claves_estrictas": ["pastillas", "caliper", "frenos", "mordaza"],
        "claves_diferenciales": ["discos", "rodajes"],
        "macro_sistema": "FRENOS",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["purgador", "temperatura", "mm"]
    },
    {
        "id": "G1_19",
        "falla_esperada": "Discos de freno alabeados o desgastados",
        "claves_estrictas": ["discos de freno", "alabeados", "alabeo"],
        "claves_diferenciales": ["llantas desbalanceadas", "bujes"],
        "macro_sistema": "FRENOS",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["0.05", "mm", "reloj comparador"]
    },
    {
        "id": "G1_20",
        "falla_esperada": "Llantas desbalanceadas o desalineadas / Deformacion de neumatico",
        "claves_estrictas": ["llantas desbalanceadas", "desalineadas", "neumatico", "rin"],
        "claves_diferenciales": ["discos de freno", "amortiguadores"],
        "macro_sistema": "SUSPENSION_CHASIS",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["0.80", "mm", "gramos", "balanceo"]
    },
    {
        "id": "G1_21",
        "falla_esperada": "Falla en sensor de velocidad de rueda ABS",
        "claves_estrictas": ["sensor de velocidad", "abs", "rueda abs"],
        "claves_diferenciales": ["pastillas", "hidraulica"],
        "macro_sistema": "FRENOS",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["km/h", "mm", "entrehierro"]
    },
    {
        "id": "G1_22",
        "falla_esperada": "Fuga hidraulica o aire en el sistema de frenos (aire tras cambio de pastillas)",
        "claves_estrictas": ["fuga hidraulica o aire", "aire", "purga", "pastillas"],
        "claves_diferenciales": ["cilindro maestro", "servofreno"],
        "macro_sistema": "FRENOS",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["dot", "purga"]
    },
    {
        "id": "G1_23",
        "falla_esperada": "Falta o degradacion de aceite de caja de cambios / Sellos de reversa",
        "claves_estrictas": ["aceite de caja", "caja de cambios", "reversa", "automatica"],
        "claves_diferenciales": ["sobrecalentamiento", "solenoides"],
        "macro_sistema": "TRANSMISION",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["atf", "psi", "temperatura"]
    },
    {
        "id": "G1_24",
        "falla_esperada": "Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
        "claves_estrictas": ["cvt", "sobrecalentamiento", "solenoides", "p0841"],
        "claves_diferenciales": ["aceite de caja", "enfriador"],
        "macro_sistema": "TRANSMISION",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["p0841", "temperatura", "degradacion"]
    },
    {
        "id": "G1_25",
        "falla_esperada": "Sobrecalentamiento o solenoides en caja automatica CVT / DSG (embrague K1 desgastado)",
        "claves_estrictas": ["dsg", "sobrecalentamiento o solenoides", "embrague"],
        "claves_diferenciales": ["aceite de caja", "mecatronica"],
        "macro_sistema": "TRANSMISION",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["k1", "ajuste basico", "bar"]
    },
    {
        "id": "G1_26",
        "falla_esperada": "Falla en caja robotizada Dualogic / I-Motion / Easytronic (acumulador de presion)",
        "claves_estrictas": ["dualogic", "robotizada", "acumulador"],
        "claves_diferenciales": ["solenoides", "bomba"],
        "macro_sistema": "TRANSMISION",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["40", "50", "bar"]
    },
    {
        "id": "G1_27",
        "falla_esperada": "Disco de embrague desgastado o patinando",
        "claves_estrictas": ["disco de embrague", "patinando", "embrague"],
        "claves_diferenciales": ["bombin", "hidraulica"],
        "macro_sistema": "TRANSMISION",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["calado", "rpm"]
    },
    {
        "id": "G1_28",
        "falla_esperada": "Collarin de empuje o crapodina de embrague desgastada",
        "claves_estrictas": ["collarin", "embrague", "crapodina", "rodaje"],
        "claves_diferenciales": ["caja mecanica", "disco de embrague"],
        "macro_sistema": "TRANSMISION",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["pisar", "desmontar"]
    },
    {
        "id": "G1_29",
        "falla_esperada": "Rodajes de caja mecanica o diferencial gastados (rodamiento primario)",
        "claves_estrictas": ["rodajes de caja", "caja mecanica", "primario", "neutro"],
        "claves_diferenciales": ["embrague", "collarin"],
        "macro_sistema": "TRANSMISION",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["valvulina", "limalla"]
    },
    {
        "id": "G1_30",
        "falla_esperada": "Plato opresor alabeado o embrague zapateando",
        "claves_estrictas": ["embrague", "disco de embrague", "prensa", "zapatea"],
        "claves_diferenciales": ["soporte", "bujes"],
        "macro_sistema": "TRANSMISION",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["resortes", "volante"]
    },
    {
        "id": "G1_31",
        "falla_esperada": "Llantas desbalanceadas o desalineadas (desalineacion tras golpe)",
        "claves_estrictas": ["desalineadas", "alineacion", "llantas desbalanceadas"],
        "claves_diferenciales": ["amortiguadores", "cremallera"],
        "macro_sistema": "SUSPENSION_CHASIS",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["laser", "grados", "mm"]
    },
    {
        "id": "G1_32",
        "falla_esperada": "Juntas homocineticas o palieres dañados",
        "claves_estrictas": ["homocineticas", "palieres", "homocinetica"],
        "claves_diferenciales": ["amortiguadores", "bujes"],
        "macro_sistema": "SUSPENSION_CHASIS",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["grasa", "fuelle"]
    },
    {
        "id": "G1_33",
        "falla_esperada": "Rodamiento de rueda / maza delantera picado",
        "claves_estrictas": ["rodajes de caja o diferencial", "rodamiento", "maza", "rueda"],
        "claves_diferenciales": ["llantas desbalanceadas", "homocineticas"],
        "macro_sistema": "SUSPENSION_CHASIS",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["estetoscopio", "elevador"]
    },
    {
        "id": "G1_34",
        "falla_esperada": "Amortiguadores reventados o bujes de suspension gastados",
        "claves_estrictas": ["amortiguadores", "suspension", "bujes"],
        "claves_diferenciales": ["espirales", "llantas"],
        "macro_sistema": "SUSPENSION_CHASIS",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["rebote", "fuga"]
    },
    {
        "id": "G1_35",
        "falla_esperada": "Cremallera de direccion asistida con holgura o terminales axiales",
        "claves_estrictas": ["cremallera", "direccion asistida", "terminales"],
        "claves_diferenciales": ["llantas desbalanceadas", "bujes"],
        "macro_sistema": "SUSPENSION_CHASIS",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["juego libre", "mm"]
    },
    {
        "id": "G1_36",
        "falla_esperada": "Llantas desbalanceadas o desalineadas (divergencia / camber negativo)",
        "claves_estrictas": ["desalineadas", "alineacion", "llantas desbalanceadas"],
        "claves_diferenciales": ["amortiguadores", "bujes"],
        "macro_sistema": "SUSPENSION_CHASIS",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["0.10", "grados", "mm"]
    },
    {
        "id": "G1_37",
        "falla_esperada": "Falla en termostato o motoventilador de radiador (electroventilador quemado)",
        "claves_estrictas": ["motoventilador", "ventilador", "termostato", "refrigerante"],
        "claves_diferenciales": ["radiador", "bomba de agua"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["12", "voltios", "ect"]
    },
    {
        "id": "G1_38",
        "falla_esperada": "Falla en termostato o motoventilador de radiador (termostato trabado cerrado)",
        "claves_estrictas": ["termostato", "motoventilador", "refrigerante"],
        "claves_diferenciales": ["bomba de agua", "radiador"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["82", "95", "°c"]
    },
    {
        "id": "G1_39",
        "falla_esperada": "Empaque de culata soplado o dañado",
        "claves_estrictas": ["empaque de culata", "culata", "soplado"],
        "claves_diferenciales": ["refrigerante", "termostato"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": True,
        "valores_tolerancias_esperadas": ["co2", "reactivo", "burbujas"]
    },
    {
        "id": "G1_40",
        "falla_esperada": "Baja presion de aceite o bomba de aceite defectuosa",
        "claves_estrictas": ["presion de aceite", "bomba de aceite"],
        "claves_diferenciales": ["anillos", "metales"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["10", "15", "psi", "bar"]
    },
    {
        "id": "G1_41",
        "falla_esperada": "Taques / buzos hidraulicos descargados o baja presion de aceite",
        "claves_estrictas": ["presion de aceite", "taques", "buzos", "distribucion"],
        "claves_diferenciales": ["anillos", "aceite"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["viscosidad", "5w-30"]
    },
    {
        "id": "G1_42",
        "falla_esperada": "Alternador defectuoso o placa de diodos quemada (sobrevoltaje)",
        "claves_estrictas": ["alternador", "placa de diodos", "regulador"],
        "claves_diferenciales": ["bateria"],
        "macro_sistema": "ELECTRICO",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["13.8", "14.4", "16.1", "voltios"]
    },
    {
        "id": "G1_43",
        "falla_esperada": "Alternador defectuoso o placa de diodos quemada (baja carga P0562)",
        "claves_estrictas": ["alternador", "placa de diodos", "p0562"],
        "claves_diferenciales": ["bateria", "bornes"],
        "macro_sistema": "ELECTRICO",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["11.9", "12.3", "14", "voltios"]
    },
    {
        "id": "G1_44",
        "falla_esperada": "Motor de arranque o solenoide defectuoso (escobillas/carbones)",
        "claves_estrictas": ["arrancador", "motor de arranque", "solenoide", "carbones", "escobillas"],
        "claves_diferenciales": ["bateria", "bornes", "alternador"],
        "macro_sistema": "ELECTRICO",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["terminal 50", "carbones", "12.7"]
    },
    {
        "id": "G1_45",
        "falla_esperada": "Fuga parásita de corriente en reposo / Bateria descargada o bornes",
        "claves_estrictas": ["fuga parasita", "bateria descargada", "bornes"],
        "claves_diferenciales": ["alternador"],
        "macro_sistema": "ELECTRICO",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["50", "ma", "650"]
    },
    {
        "id": "G1_46",
        "falla_esperada": "Valvulas de compresor desgastadas / Fugas de aire o fallos en el sistema de frenos neumatico (Camiones)",
        "claves_estrictas": ["frenos neumatico", "compresor", "fugas de aire"],
        "claves_diferenciales": ["secador aps"],
        "macro_sistema": "CARROCERIA_NEUMATICA",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["bar", "psi"]
    },
    {
        "id": "G1_47",
        "falla_esperada": "Valvula de freno de aire o secador APS obstruido (Camiones)",
        "claves_estrictas": ["secador aps", "valvula de freno de aire", "gobernadora"],
        "claves_diferenciales": ["frenos neumatico"],
        "macro_sistema": "CARROCERIA_NEUMATICA",
        "requiere_auto_interrogador": True,
        "valores_tolerancias_esperadas": ["120", "125", "psi"]
    },
    {
        "id": "G1_48",
        "falla_esperada": "Fugas de aire o fallos en el sistema de frenos neumatico (Camiones - diafragma Maxi-Brake)",
        "claves_estrictas": ["frenos neumatico", "fugas de aire", "camara de freno", "maxi-brake"],
        "claves_diferenciales": ["secador aps"],
        "macro_sistema": "CARROCERIA_NEUMATICA",
        "requiere_auto_interrogador": False,
        "valores_tolerancias_esperadas": ["camara", "resorte"]
    },
    {
        "id": "G1_49",
        "falla_esperada": "Consulta termica ambigua de motor (Misfire / CKP / Bomba)",
        "claves_estrictas": ["bujias o bobinas", "cuerpo de aceleracion", "bomba de gasolina", "ckp"],
        "claves_diferenciales": ["temperatura", "inyeccion"],
        "macro_sistema": "MOTOR",
        "requiere_auto_interrogador": True,
        "valores_tolerancias_esperadas": []
    },
    {
        "id": "G1_50",
        "falla_esperada": "Consulta difusa en tren delantero (Rotula / Trapecio / Bieleta)",
        "claves_estrictas": ["rotula", "trapecio", "bieleta", "amortiguadores", "cremallera", "llantas desbalanceadas"],
        "claves_diferenciales": ["suspension", "direccion"],
        "macro_sistema": "SUSPENSION_CHASIS",
        "requiere_auto_interrogador": True,
        "valores_tolerancias_esperadas": []
    }
]
