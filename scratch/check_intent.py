import sys

sys.path.insert(0, "backend")
from src.core.intent_classifier import clasificar_intencion_consulta

msg1 = '"Buenas, mi carro estaba normal hasta ayer. Hoy salí a la carretera y a los 20 minutos de manejar empecé a sentir que perdía fuerza, como que se ahogaba. Bajé la velocidad y se recuperó. Pero a los 5 minutos otra vez. Ya no puedo pasar de 80. ¿Qué será?'
print("Intencion con comilla:", clasificar_intencion_consulta(msg1))

msg2 = "Buenas, mi carro estaba normal hasta ayer. Hoy salí a la carretera y a los 20 minutos de manejar empecé a sentir que perdía fuerza, como que se ahogaba. Bajé la velocidad y se recuperó. Pero a los 5 minutos otra vez. Ya no puedo pasar de 80. ¿Qué será?"
print("Intencion sin comilla:", clasificar_intencion_consulta(msg2))
