"""Orientación sin fuente aplicable: observación, registro y abstención técnica."""

from src.infrastructure.rag.documental_salida import normalizar


def orientar_sin_manual(consulta: str) -> str:
    texto = normalizar(consulta)
    if any(p in texto for p in ("mariposa", "reaprendizaje", "aceleracion", "pedal")):
        orientacion = (
            "El reaprendizaje del cuerpo de mariposa y pedal depende del motor y la ECU. "
            "No repitas una secuencia de contacto/pedal de otra variante ni fuerces el actuador. "
            "Registra códigos y antecedentes; solicita el procedimiento de adaptación aplicable."
        )
    elif any(p in texto for p in ("disco", "alabeo", "volante de inercia", "comparador")):
        orientacion = (
            "La comprobación de alabeo de disco, bocín o volante de inercia requiere reloj comparador "
            "y montaje específico para la superficie según el fabricante. "
            "Registra el recorrido observado, la superficie medida y el estado de apoyo. "
            "No deduzcas rectificado ni reemplazo de una referencia genérica."
        )
    elif any(p in texto for p in ("inyector", "common rail", "combustible", "retorno")):
        orientacion = (
            "Registra síntomas y lecturas de combustible disponibles. No abras ni aflojes circuitos "
            "presurizados con el motor funcionando; una prueba de retorno requiere el kit, "
            "condiciones y procedimiento aplicables, ejecutados por personal capacitado."
        )
    elif any(p in texto for p in ("multimetro", "consumo", "electrico", "incandescente")):
        orientacion = (
            "Inspecciona visualmente conexiones con el equipo aislado según el fabricante. "
            "Registra la lectura del multímetro con unidad, punto de toma y estado del circuito. "
            "No conectes un amperímetro directamente entre los bornes ni midas resistencia en un circuito energizado."
        )
    else:
        orientacion = (
            "Puedes registrar una inspección visual externa con el vehículo inmovilizado y en condiciones seguras. "
            "Anota lo observado y los instrumentos disponibles para elegir una comprobación discriminante."
        )
    return (
        "1. Identifica componente y variante; prepara el vehículo inmovilizado y en condiciones seguras.\n"
        "2. " + orientacion + "\n3. No dispongo de documentación OEM validada para indicar tolerancias, "
        "secuencias de adaptación ni autorizar intervención. Confirma componente, motor, mercado "
        "y página del manual aplicable. (corpus_validado=False)."
    )
