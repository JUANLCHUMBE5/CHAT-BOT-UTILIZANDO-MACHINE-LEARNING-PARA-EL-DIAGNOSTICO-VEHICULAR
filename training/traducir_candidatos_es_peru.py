"""Traduce candidatos auditados a español técnico usado en talleres de Perú.

No agrega filas al dataset de entrenamiento. La traducción queda marcada como
pendiente hasta que un mecánico valide síntoma y etiqueta canónica.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


TRADUCCIONES_ES_PERU: dict[str, str] = {
    "ABS warning light on": "La luz de advertencia del ABS permanece encendida",
    "ABS light stays on": "La luz de ABS permanece encendida",
    "Erratic speedometer": "El velocímetro marca de forma errática",
    "Spongy brake pedal": "El pedal de freno se siente esponjoso",
    "Hard brake pedal": "El pedal de freno está duro",
    "Brake fluid leak": "Hay fuga de líquido de frenos",
    "Brake fluid leaks": "Hay fugas de líquido de frenos",
    "Soft brake pedal": "El pedal de freno está demasiado suave",
    "Squealing brakes": "Los frenos chillan al frenar",
    "Brake pedal pulsation": "El pedal de freno pulsa al frenar",
    "Steering wheel vibration": "El timón vibra",
    "Brake dragging": "El freno queda frenado o pegado",
    "No cold air from vents": "No sale aire frío por las rejillas",
    "Loud noise when AC is on": "El aire acondicionado hace un ruido fuerte al encenderlo",
    "Engine overheating": "El motor se recalienta",
    "Coolant leaks under the vehicle": "Hay fuga de refrigerante debajo del vehículo",
    "Visible coolant puddle under vehicle": "Se forma un charco de refrigerante debajo del vehículo",
    "Coolant odor in cabin": "Se siente olor a refrigerante dentro de la cabina",
    "Temperature gauge in red zone": "La aguja de temperatura llega a la zona roja",
    "AC not cooling at idle": "El aire acondicionado no enfría cuando el motor está en mínimo",
    "Coolant leak under vehicle": "Hay fuga de refrigerante debajo del vehículo",
    "Visible wear/cracks on hoses": "Las mangueras están cuarteadas o rajadas",
    "Coolant leak near front of engine": "Hay fuga de refrigerante en la parte delantera del motor",
    "Whining noise from drivetrain": "Se escucha un zumbido en la transmisión",
    "Difficulty shifting gears": "Cuesta pasar los cambios",
    "Clutch pedal feels loose": "El pedal de embrague se siente flojo",
    "Difficulty engaging gears": "Cuesta engranar los cambios",
    "Clutch pedal feels spongy": "El pedal de embrague se siente esponjoso",
    "Fluid leak near clutch pedal": "Hay fuga de líquido cerca del pedal de embrague",
    "Whining noise from rear end": "Se escucha un zumbido en la parte posterior",
    "Vehicle vibration at high speeds": "El vehículo vibra a alta velocidad",
    "Transmission slipping": "La caja automática patina",
    "Delay in gear engagement": "La caja demora en acoplar el cambio",
    "Engine cranks slowly": "El motor de arranque gira lento",
    "Clicking sound when starting": "Se escucha un clic al intentar arrancar",
    "Battery warning light on": "La luz de batería permanece encendida",
    "Dim headlights": "Las luces delanteras alumbran con poca intensidad",
    "Window does not move": "El vidrio eléctrico no sube ni baja",
    "Window moves intermittently": "El vidrio eléctrico funciona por momentos",
    "Window off track": "El vidrio de la puerta se salió de la guía",
    "Window stuck in one position": "El vidrio de la puerta quedó trabado",
    "Engine misfires": "El motor falla y trabaja disparejo",
    "Difficulty starting engine": "Al motor le cuesta arrancar",
    "Poor fuel economy": "El vehículo consume demasiado combustible",
    "Door lock not responding": "El seguro eléctrico de la puerta no responde",
    "Clicking sound from door": "Se escucha un clic dentro de la puerta",
    "Engine does not crank": "El motor de arranque no gira",
    "Clicking sound when key is turned": "Al girar la llave solo se escucha un clic",
    "Wipers not working": "Los limpiaparabrisas no funcionan",
    "Wipers operate intermittently": "Los limpiaparabrisas funcionan por momentos",
    "Check engine light on": "La luz Check Engine permanece encendida",
    "Loss of power": "El vehículo pierde fuerza",
    "Turbo lag": "El turbo demora en cargar y responder",
    "Black smoke from exhaust": "Sale humo negro por el escape",
    "Erratic idle speed": "Las revoluciones varían cuando el motor está en mínimo",
    "Stalling at idle": "El motor se apaga cuando está en mínimo",
    "Low oil pressure warning light": "Se enciende la luz de baja presión de aceite",
    "Engine knocking noise": "Se escucha un golpeteo metálico en el motor",
    "Blue smoke from exhaust": "Sale humo azul por el escape",
    "Loss of engine power": "El motor pierde fuerza",
    "Engine won't start": "El motor no arranca",
    "Low voltage": "El sistema eléctrico tiene bajo voltaje",
    "Loud engine noise": "El motor hace un ruido fuerte",
    "Engine stalls at high speeds": "El motor se apaga al circular a alta velocidad",
    "Poor acceleration": "El vehículo acelera con poca fuerza",
    "Engine sputters at high speeds": "El motor tironea y falla a alta velocidad",
    "Soft clutch pedal": "El pedal de embrague está demasiado suave",
    "Clutch slipping": "El embrague patina al acelerar",
    "Gears slipping": "Los cambios patinan",
    "Transmission overheating": "La caja de cambios se recalienta",
    "Delayed shifting": "La caja demora en realizar los cambios",
    "Erratic shifting": "La caja realiza cambios bruscos o erráticos",
    "Transmission won't shift gears": "La caja no realiza los cambios",
    "Brake pulling to one side": "El vehículo jala hacia un lado al frenar",
    "Warm air from AC vents": "Sale aire tibio por las rejillas del aire acondicionado",
    "AC system not cooling": "El aire acondicionado no enfría",
    "Musty odor from vents": "Sale olor a humedad por las rejillas",
    "Weak airflow from vents": "Sale poco aire por las rejillas",
    "Warm air from vents": "Sale aire tibio por las rejillas",
    "Low AC system pressure": "El sistema de aire acondicionado tiene baja presión",
    "AC system not working": "El aire acondicionado no funciona",
    "Unusual noise from AC system": "El aire acondicionado hace un ruido anormal",
    "Reduced airflow from vents": "Disminuyó el flujo de aire por las rejillas",
    "No air from vents": "No sale aire por las rejillas",
    "Loud noise from HVAC system": "El sistema de ventilación hace un ruido fuerte",
    "HVAC fan speed erratic": "La velocidad del ventilador de cabina varía de forma errática",
    "HVAC fan only works on certain settings": "El ventilador de cabina solo funciona en algunas velocidades",
    "No heat from vents": "No sale aire caliente por las rejillas",
    "Sweet smell in cabin": "Se siente un olor dulce a refrigerante dentro de la cabina",
    "Visible coolant leak under vehicle": "Se observa una fuga de refrigerante debajo del vehículo",
    "Vehicle binding on turns": "La transmisión se amarra al girar",
    "Noise from drivetrain while turning": "La transmisión hace ruido al girar",
    "Axle noise while turning": "El eje hace ruido al girar",
    "Vehicle leans to one side": "El vehículo queda inclinado hacia un lado",
    "Vehicle bounces over bumps": "El vehículo rebota demasiado al pasar baches",
    "Loud noise from rear axle": "El eje posterior hace un ruido fuerte",
    "Driveline vibration": "La línea de transmisión vibra",
    "Clunking noise when shifting": "Se escucha un golpe al realizar los cambios",
    "Vehicle binding during turns": "La transmisión se amarra durante los giros",
    "Poor engine performance": "El motor tiene bajo rendimiento",
    "Headlight not working": "Una luz delantera no funciona",
    "Dim headlight": "Una luz delantera alumbra con poca intensidad",
    "No washer fluid spray": "No sale líquido del lavaparabrisas",
    "Weak washer fluid spray": "El líquido del lavaparabrisas sale con poca presión",
    "Rough idle": "El motor trabaja inestable en mínimo",
    "Rotten egg smell from exhaust": "Sale olor a huevo podrido por el escape",
    "Fuel odor from vehicle": "Se siente olor a combustible alrededor del vehículo",
    "Loud exhaust noise": "El escape hace un ruido fuerte",
    "Exhaust smell in cabin": "Se siente olor a gases de escape dentro de la cabina",
    "Visible exhaust leaks": "Se observa una fuga de gases en el escape",
    "Gas cap warning light": "Se enciende la advertencia de tapa de combustible",
    "Engine knocking/pinging": "El motor cascabelea o pistonea",
    "Engine vibration": "El motor vibra demasiado",
    "Hard starting in cold weather": "Al motor le cuesta arrancar en frío",
    "Glow plug indicator light stays on": "La luz de precalentamiento diésel permanece encendida",
    "Excessive engine movement": "El motor se mueve demasiado",
    "Clunking noise when accelerating": "Se escucha un golpe al acelerar",
    "Oil leak around valve cover": "Hay fuga de aceite alrededor de la tapa de válvulas",
    "Burning oil smell from engine bay": "Se siente olor a aceite quemado en el compartimiento del motor",
    "Squealing noise from engine bay": "Se escucha un chillido en el compartimiento del motor",
    "No sound when horn button pressed": "El claxon no suena al presionar el botón",
    "Engine performance issues": "El motor presenta bajo rendimiento",
    "Noise when turning steering wheel": "Se escucha ruido al girar el timón",
    "Uneven tire wear": "Las llantas presentan desgaste irregular",
    "Vibration while driving": "El vehículo vibra al circular",
    "Decreased engine performance": "Disminuyó el rendimiento del motor",
    "Oil leaks": "Hay fugas de aceite",
    "Engine stalls": "El motor se apaga",
    "Fuel odor inside vehicle": "Se siente olor a combustible dentro del vehículo",
    "Visible fuel leak under vehicle": "Se observa una fuga de combustible debajo del vehículo",
    "Engine hesitates on acceleration": "El motor se aguanta o demora en responder al acelerar",
    "Brake warning light on": "La luz de advertencia de frenos permanece encendida",
    "Low coolant warning light": "Se enciende la advertencia de nivel bajo de refrigerante",
    "Whining noise when turning": "Se escucha un zumbido al girar el timón",
    "Stiff steering wheel": "El timón está duro",
    "Coolant leak": "Hay fuga de refrigerante",
    "Slipping gears": "Los cambios patinan",
    "Shuddering during acceleration": "El vehículo tironea o tiembla al acelerar",
    "Grinding noise from wheels": "Se escucha un ruido de raspado en las ruedas",
    "TPMS warning light on": "La luz de presión de llantas TPMS permanece encendida",
    "Low tire pressure": "Una o más llantas tienen baja presión",
    "Clicking or popping noise when turning": "Se escucha un clac clac al girar",
    "Wheel wobbling": "La rueda tiene juego o bambolea",
}


def traducir(entrada: Path, salida: Path) -> tuple[int, int]:
    with entrada.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    if not filas:
        raise ValueError("El archivo de candidatos está vacío.")

    traducidas = 0
    faltantes = 0
    for fila in filas:
        traduccion = TRADUCCIONES_ES_PERU.get(fila["sintoma_fuente_ingles"], "")
        fila["sintoma_es_peru_candidato"] = traduccion
        if traduccion:
            fila["estado_traduccion"] = "PENDIENTE_VALIDACION_MECANICO"
            traducidas += 1
        else:
            fila["estado_traduccion"] = "SIN_TRADUCIR"
            faltantes += 1

    campos = list(filas[0])
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(filas)
    return traducidas, faltantes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "entrada",
        type=Path,
        nargs="?",
        default=Path("data/candidatos_revision/zenodo_15626055.csv"),
    )
    parser.add_argument(
        "--salida",
        type=Path,
        default=Path("data/candidatos_revision/zenodo_15626055_es_peru.csv"),
    )
    args = parser.parse_args()
    traducidas, faltantes = traducir(args.entrada, args.salida)
    print(f"Traducciones generadas: {traducidas}; pendientes: {faltantes}")


if __name__ == "__main__":
    main()
