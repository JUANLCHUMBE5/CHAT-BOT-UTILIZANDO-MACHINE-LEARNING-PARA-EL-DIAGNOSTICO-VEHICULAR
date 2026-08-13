import logging
import sys

# Definición del formato personalizado con timestamp y niveles
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name: str = "ChatbotVehicular", level: int = logging.INFO) -> logging.Logger:
    """
    Crea y configura un logger profesional estructurado para el sistema.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Evitar duplicación de handlers si ya fue configurado
    if not logger.handlers:
        # Handler para la consola de comandos
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # Formateador con timestamps estandarizados
        formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger

# Instancia por defecto del logger principal
logger = setup_logger()
