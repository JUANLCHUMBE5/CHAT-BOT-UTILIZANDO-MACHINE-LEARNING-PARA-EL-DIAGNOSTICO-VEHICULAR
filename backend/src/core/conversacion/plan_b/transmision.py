"""Alternativas del embrague manual sin confundirlo con discos de freno."""
from src.core.conversacion.models import QuestionIntent


def alternativa_embrague(estado):
    if estado.ya_preguntado_texto("motor apagado, el pedal de embrague"):
        return (
            "comprobación del mando de embrague pendiente; no repetir pruebas no disponibles.",
            "Conservo la hipótesis pendiente sin confirmar. No insistiré en esa prueba; mantenemos la orientación provisional hasta una revisión presencial en taller.",
            QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
        )
    return (
        "inspección del retorno del pedal y fugas visibles del mando de embrague con motor apagado.",
        "Con el motor apagado, realiza una inspección visual: el pedal de embrague ¿retorna completamente y presenta juego libre? "
        "Indica también si observas una fuga visible en el mando hidráulico, sin desmontar ni arrancar.",
        QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
    )
