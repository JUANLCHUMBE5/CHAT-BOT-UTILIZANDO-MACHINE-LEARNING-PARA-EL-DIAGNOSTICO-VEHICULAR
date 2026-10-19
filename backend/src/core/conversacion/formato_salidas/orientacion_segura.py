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
    elif any(p in texto for p in ("contrapresion", "manometro", "escape")):
        orientacion = (
            "La medicion de contrapresion de escape requiere el adaptador, punto de toma y procedimiento "
            "del fabricante. No indico umbrales sin respaldo para esta variante. Solicita la comprobacion "
            "a personal capacitado y evita tocar o desmontar componentes calientes."
        )
    elif any(p in texto for p in ("actuador", "solenoide", "turbo")):
        orientacion = (
            "No fuerces ni ajustes el actuador del turbo. Con el motor apagado y frio, limita la revision "
            "a observar desde fuera mangueras y conectores accesibles, sin desmontar. La prueba funcional "
            "requiere equipo y procedimiento OEM aplicables, ejecutados por personal capacitado."
        )
    elif any(p in texto for p in ("termostato", "electroventilador", "ventilador")):
        orientacion = (
            "Diferencia termostato y electroventilador con lectura de temperatura y activacion conforme "
            "al procedimiento OEM, sin asumir un umbral universal. No acerques las manos al ventilador ni "
            "abras el circuito de refrigeracion caliente; solicita la prueba en taller si no tienes equipo."
        )
    elif any(p in texto for p in ("culata", "torque", "apriete")):
        orientacion = (
            "No aflojes ni aprietes la culata con una secuencia generica. La secuencia, etapas y "
            "herramienta dependen del motor exacto; confirmalas en el manual de servicio aplicable antes "
            "de intervenir."
        )
    elif any(p in texto for p in ("refrigerante", "anticongelante", "agua de cano", "agua de caño")):
        orientacion = (
            "No mezcles refrigerante concentrado ni agua de cano sin confirmar el producto y la proporcion "
            "exigidos para esta variante. Contrasta la etiqueta y el manual aplicable; nunca abras el "
            "deposito cuando el sistema este caliente o presurizado."
        )
    elif any(p in texto for p in ("inyector", "common rail", "combustible", "retorno")):
        orientacion = (
            "Una prueba de retorno de inyectores con probetas requiere el kit, las condiciones y el "
            "procedimiento aplicables, ejecutados por personal capacitado. No abras ni aflojes circuitos "
            "presurizados con el motor funcionando. Registra sintomas y lecturas disponibles sin "
            "interpretarlas como una tolerancia OEM."
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
