"""Catálogo oficial y estructurado de taxonomía vehicular con códigos estables."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class FallaVehicularEstandar:
    codigo: str
    sistema: str
    falla_principal: str
    posibles_causas: List[str]
    severidad: str  # "alta" | "media" | "baja"
    tiempo_estimado_min: int
    urgencia: str


# Catálogo unificado y normalizado sin duplicados semánticos
CATALOGO_TAXONOMIA: Dict[str, FallaVehicularEstandar] = {
    "FRENO_001": FallaVehicularEstandar(
        codigo="FRENO_001",
        sistema="Frenos",
        falla_principal="Desgaste de pastillas y zapatas de freno",
        posibles_causas=["Fricción excesiva", "Pastillas cristalizadas", "Falta de cambio periódico"],
        severidad="alta",
        tiempo_estimado_min=45,
        urgencia="Inmediata"
    ),
    "FRENO_002": FallaVehicularEstandar(
        codigo="FRENO_002",
        sistema="Frenos",
        falla_principal="Fuga hidraulica o aire en el sistema de frenos",
        posibles_causas=["Fuga en bombines", "Latiguillos picados", "Aire en cañerías", "Líquido degradado"],
        severidad="alta",
        tiempo_estimado_min=60,
        urgencia="Crítica / Detención segura"
    ),
    "FRENO_003": FallaVehicularEstandar(
        codigo="FRENO_003",
        sistema="Frenos",
        falla_principal="Discos de freno alabeados o desgastados",
        posibles_causas=["Sobrecalentamiento por frenado brusco", "Grosor por debajo del mínimo", "Enfriamiento abrupto"],
        severidad="media",
        tiempo_estimado_min=60,
        urgencia="Media"
    ),
    "FRENO_004": FallaVehicularEstandar(
        codigo="FRENO_004",
        sistema="Frenos",
        falla_principal="Falla en servofreno (booster) o linea de vacio",
        posibles_causas=["Diafragma roto", "Manguera de vacío agrietada", "Válvula check trabada"],
        severidad="alta",
        tiempo_estimado_min=60,
        urgencia="Alta"
    ),
    "FRENO_005": FallaVehicularEstandar(
        codigo="FRENO_005",
        sistema="Frenos",
        falla_principal="Falla en sensor de velocidad de rueda ABS",
        posibles_causas=["Sensor sucio con viruta metálica", "Cable cortado", "Anillo reluctor roto"],
        severidad="media",
        tiempo_estimado_min=30,
        urgencia="Moderada"
    ),
    "MOTOR_001": FallaVehicularEstandar(
        codigo="MOTOR_001",
        sistema="Motor",
        falla_principal="Falla en bujias o bobinas de encendido (misfire)",
        posibles_causas=["Bujías gastadas", "Bobina quemada", "Cables de bujía sulfatados"],
        severidad="alta",
        tiempo_estimado_min=45,
        urgencia="Alta"
    ),
    "MOTOR_002": FallaVehicularEstandar(
        codigo="MOTOR_002",
        sistema="Motor",
        falla_principal="Consumo de aceite por desgaste de anillos o retenes",
        posibles_causas=["Anillos de pistón pegados/gastados", "Retenes de válvula tostados", "Guías de válvula con holgura"],
        severidad="alta",
        tiempo_estimado_min=180,
        urgencia="Alta"
    ),
    "MOTOR_003": FallaVehicularEstandar(
        codigo="MOTOR_003",
        sistema="Motor",
        falla_principal="Empaque de culata soplado o danado",
        posibles_causas=["Sobrecalentamiento previo", "Pernos de culata estirados", "Deformación del bloque"],
        severidad="alta",
        tiempo_estimado_min=240,
        urgencia="Crítica / Detener motor"
    ),
    "MOTOR_004": FallaVehicularEstandar(
        codigo="MOTOR_004",
        sistema="Motor",
        falla_principal="Baja presion de aceite o bomba de aceite defectuosa",
        posibles_causas=["Cédula de bomba de aceite tapada", "Metales de biela con holgura", "Válvula de alivio atascada"],
        severidad="alta",
        tiempo_estimado_min=120,
        urgencia="Crítica"
    ),
    "MOTOR_005": FallaVehicularEstandar(
        codigo="MOTOR_005",
        sistema="Motor",
        falla_principal="Faja o cadena de distribucion destensada o con salto de punto",
        posibles_causas=["Tensor desgastado", "Faja vencida por kilometraje", "Guías partidas"],
        severidad="alta",
        tiempo_estimado_min=120,
        urgencia="Crítica"
    ),
    "COMBUSTIBLE_001": FallaVehicularEstandar(
        codigo="COMBUSTIBLE_001",
        sistema="Inyección de Combustible",
        falla_principal="Inyectores sucios o filtro de combustible obstruido",
        posibles_causas=["Gasolina de baja calidad", "Filtro saturado", "Sedimentos en riel"],
        severidad="media",
        tiempo_estimado_min=60,
        urgencia="Media"
    ),
    "COMBUSTIBLE_002": FallaVehicularEstandar(
        codigo="COMBUSTIBLE_002",
        sistema="Inyección de Combustible",
        falla_principal="Bomba de gasolina quemada o con baja presion",
        posibles_causas=["Pila de bomba sobrecalentada", "Válvula de retención con fuga", "Filtro colador tupido"],
        severidad="alta",
        tiempo_estimado_min=60,
        urgencia="Alta"
    ),
    "COMBUSTIBLE_003": FallaVehicularEstandar(
        codigo="COMBUSTIBLE_003",
        sistema="Inyección de Combustible",
        falla_principal="Cuerpo de aceleracion o valvula IAC sucia",
        posibles_causas=["Acumulación de carbón en mariposa", "Actuador IAC pegado", "Entrada de aire falso"],
        severidad="media",
        tiempo_estimado_min=30,
        urgencia="Moderada"
    ),
    "COMBUSTIBLE_004": FallaVehicularEstandar(
        codigo="COMBUSTIBLE_004",
        sistema="Inyección de Combustible",
        falla_principal="Falla en sensor de oxigeno o mezcla rica",
        posibles_causas=["Sensor lambda envejecido", "Sensor de temperatura de refrigerante ECT trabado", "Inyector goteando"],
        severidad="media",
        tiempo_estimado_min=45,
        urgencia="Media"
    ),
    "EMBRAGUE_001": FallaVehicularEstandar(
        codigo="EMBRAGUE_001",
        sistema="Transmisión y Embrague",
        falla_principal="Disco de embrague desgastado o patinando",
        posibles_causas=["Material de fricción agotado", "Plato opresor sin fuerza", "Aceite en disco por fuga de retén"],
        severidad="alta",
        tiempo_estimado_min=180,
        urgencia="Alta"
    ),
    "EMBRAGUE_002": FallaVehicularEstandar(
        codigo="EMBRAGUE_002",
        sistema="Transmisión y Embrague",
        falla_principal="Falla en bombin o bomba hidraulica de embrague",
        posibles_causas=["Retén interno gastado", "Pérdida de presión hidráulica", "Aire en circuito"],
        severidad="alta",
        tiempo_estimado_min=60,
        urgencia="Alta"
    ),
    "TRANSMISION_001": FallaVehicularEstandar(
        codigo="TRANSMISION_001",
        sistema="Transmisión y Embrague",
        falla_principal="Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
        posibles_causas=["Fluido ATF/CVT degradado", "Solenoide de presión pegado", "Filtro de transmisión tapado"],
        severidad="alta",
        tiempo_estimado_min=120,
        urgencia="Alta"
    ),
    "REFRIGERACION_001": FallaVehicularEstandar(
        codigo="REFRIGERACION_001",
        sistema="Refrigeración",
        falla_principal="Falla en termostato o motoventilador de radiador",
        posibles_causas=["Termostato trabado cerrado", "Relé de ventilador quemado", "Motor de electroventilador fundido"],
        severidad="alta",
        tiempo_estimado_min=45,
        urgencia="Crítica"
    ),
    "REFRIGERACION_002": FallaVehicularEstandar(
        codigo="REFRIGERACION_002",
        sistema="Refrigeración",
        falla_principal="Fuga en mangueras de refrigerante o radiador picado",
        posibles_causas=["Fisura en tanque plástico", "Abrazadera suelta", "Tapa de radiador sin sello"],
        severidad="alta",
        tiempo_estimado_min=45,
        urgencia="Alta"
    ),
    "ELECTRICO_001": FallaVehicularEstandar(
        codigo="ELECTRICO_001",
        sistema="Sistema Eléctrico y Carga",
        falla_principal="Alternador defectuoso o placa de diodos quemada",
        posibles_causas=["Regulador de voltaje en corto", "Escobillas de carbón gastadas", "Diodos rectificadores abiertos"],
        severidad="alta",
        tiempo_estimado_min=60,
        urgencia="Alta"
    ),
    "ELECTRICO_002": FallaVehicularEstandar(
        codigo="ELECTRICO_002",
        sistema="Sistema Eléctrico y Carga",
        falla_principal="Bateria descargada o bornes sulfatados",
        posibles_causas=["Batería cumplió vida útil", "Consumo parásito en reposo", "Bornes con óxido"],
        severidad="media",
        tiempo_estimado_min=20,
        urgencia="Media"
    ),
    "SUSPENSION_001": FallaVehicularEstandar(
        codigo="SUSPENSION_001",
        sistema="Suspensión y Dirección",
        falla_principal="Amortiguadores reventados o bujes de suspension gastados",
        posibles_causas=["Retén de amortiguador roto", "Bocinas de trapecio rajadas", "Cazoletas con juego"],
        severidad="media",
        tiempo_estimado_min=90,
        urgencia="Media"
    ),
    "SUSPENSION_002": FallaVehicularEstandar(
        codigo="SUSPENSION_002",
        sistema="Suspensión y Dirección",
        falla_principal="Juntas homocineticas o palieres danados",
        posibles_causas=["Fuelle de jebe roto", "Pérdida de grasa grafitada", "Tripoide o canastilla con desgaste"],
        severidad="alta",
        tiempo_estimado_min=75,
        urgencia="Alta"
    ),
    "SUSPENSION_003": FallaVehicularEstandar(
        codigo="SUSPENSION_003",
        sistema="Suspensión y Dirección",
        falla_principal="Cremallera de direccion asistida con holgura o fuga",
        posibles_causas=["Retenes de cremallera gastados", "Terminales de dirección con juego", "Bomba hidráulica desgastada"],
        severidad="alta",
        tiempo_estimado_min=120,
        urgencia="Alta"
    ),
    "SUSPENSION_004": FallaVehicularEstandar(
        codigo="SUSPENSION_004",
        sistema="Suspensión y Dirección",
        falla_principal="Llantas desbalanceadas o desalineadas",
        posibles_causas=["Pérdida de plomos de balanceo", "Aro golpeado", "Desgaste irregular de banda"],
        severidad="baja",
        tiempo_estimado_min=30,
        urgencia="Baja"
    ),
    "CLIMA_001": FallaVehicularEstandar(
        codigo="CLIMA_001",
        sistema="Climatización y Confort",
        falla_principal="Falla en compresor de aire acondicionado o fuga de gas R134a",
        posibles_causas=["Sello de compresor seco", "Condensador perforado por piedra", "Embrague magnético quemado"],
        severidad="baja",
        tiempo_estimado_min=60,
        urgencia="Baja"
    ),
    "TURBO_001": FallaVehicularEstandar(
        codigo="TURBO_001",
        sistema="Sobrealimentación y Turbo",
        falla_principal="Fuga en mangueras de intercooler o turbocompresor danado",
        posibles_causas=["Abrazadera de turbo suelta", "Manguera de intercooler rajada", "Holgura en eje de turbina"],
        severidad="alta",
        tiempo_estimado_min=90,
        urgencia="Alta"
    ),
}

# Mapa de normalización de etiquetas antiguas/ambiguas hacia la taxonomía estándar
MAPA_UNIFICACION_ETIQUETAS: Dict[str, str] = {
    # Alternador / Carga
    "Alternador defectuoso o faja suelta": "ELECTRICO_001",
    "Alternador defectuoso o placa de diodos quemada": "ELECTRICO_001",
    "Bateria descargada o arrancador defectuoso": "ELECTRICO_002",
    "Motor de arrancador / solenoide pegado": "ELECTRICO_002",
    
    # Frenos
    "Pastillas de freno desgastadas": "FRENO_001",
    "Pastillas o zapatas de freno totalmente desgastadas": "FRENO_001",
    "Fuga de liquido de frenos o aire en el sistema": "FRENO_002",
    "Fuga de liquido de frenos o aire en cañerias": "FRENO_002",
    "Fuga de liquido de frenos o aire en caerias": "FRENO_002",
    "Discos de freno deformados o alabeados": "FRENO_003",
    "Discos de freno rectificados en exceso o alabeados": "FRENO_003",
    "Fallo en el servo freno (booster)": "FRENO_004",
    "Sensor de velocidad ABS de rueda sucio o dañado": "FRENO_005",
    "Sensor de velocidad ABS de rueda sucio o daado": "FRENO_005",

    # Motor y Encendido
    "Bujias desgastadas o bobina de encendido defectuosa": "MOTOR_001",
    "Bujias desgastadas o gasolina de bajo octanaje (preignicion)": "MOTOR_001",
    "Consumo de aceite por anillos de piston gastados": "MOTOR_002",
    "El motor esta consumiendo aceite (anillos de piston gastados)": "MOTOR_002",
    "Empaque de culata soplado": "MOTOR_003",
    "Soplo de empaque de culata": "MOTOR_003",
    "Soplo de empaque de culata (ingreso de refrigerante al motor)": "MOTOR_003",
    "Bomba de aceite defectuosa o baja presion de lubricacion": "MOTOR_004",
    "Faja de distribucion / tiempo destensada o rota": "MOTOR_005",

    # Inyección y Combustible
    "Filtro de combustible obstruido o inyectores sucios": "COMBUSTIBLE_001",
    "Filtro de combustible o inyectores sucios": "COMBUSTIBLE_001",
    "Bomba de gasolina / combustible quemada o sin presion": "COMBUSTIBLE_002",
    "Valvula IAC sucia u obstruida (control de minimo)": "COMBUSTIBLE_003",
    "Valvula IAC sucia u obstruida (minimo)": "COMBUSTIBLE_003",
    "Falla de cuerpo de aceleracion electronico TAC (Drive-by-Wire)": "COMBUSTIBLE_003",
    "Sensor de oxigeno defectuoso": "COMBUSTIBLE_004",
    "Sensor de oxigeno defectuoso o bujias en mal estado": "COMBUSTIBLE_004",
    "Mezcla rica (demasiado combustible / falla de sensor de oxigeno)": "COMBUSTIBLE_004",

    # Embrague y Transmisión
    "Disco de embrague (clutch) desgastado o patinando": "EMBRAGUE_001",
    "Disco de embrague (clutch) gastado o patinando": "EMBRAGUE_001",
    "Bombin o cable de embrague desajustado": "EMBRAGUE_002",
    "Caja automatica CVT o DSG con sobrecalentamiento / solenoide trancado": "TRANSMISION_001",

    # Refrigeración
    "Falla en el rele o motor del ventilador del radiador": "REFRIGERACION_001",
    "Fuga en mangueras de refrigerante o radiador picado": "REFRIGERACION_002",

    # Suspensión y Dirección
    "Amortiguadores reventados o bujes de suspension gastados": "SUSPENSION_001",
    "Amortiguadores reventados o bujes de muelles gastados": "SUSPENSION_001",
    "Juntas homocineticas (palieres) dañadas": "SUSPENSION_002",
    "Juntas homocineticas (palieres) daadas": "SUSPENSION_002",
    "Junta homocinetica / palier con tripoide destruido": "SUSPENSION_002",
    "Cremallera de direccion asistida (EPS o Hidraulica) con juego o fuga": "SUSPENSION_003",
    "Caja o cremallera de direccion asistida con fuga": "SUSPENSION_003",
    "Llantas desalineadas, desbalanceadas o deformadas": "SUSPENSION_004",

    # Climatización y Turbo
    "Compresor de aire acondicionado (A/C) trabado o fuga de gas R134a": "CLIMA_001",
    "Turbocompresor picado o fuga en el Intercooler (Diésel)": "TURBO_001",
    "Turbocompresor picado o fuga en el Intercooler (Disel)": "TURBO_001",
}
