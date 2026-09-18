import sys

sys.path.insert(0, "backend")
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState
from src.core.conversacion.sintetizador_consulta import SintetizadorConsulta
from src.infrastructure.container import ServiceContainer

msg1 = '"Buenas, mi carro estaba normal hasta ayer. Hoy salí a la carretera y a los 20 minutos de manejar empecé a sentir que perdía fuerza, como que se ahogaba. Bajé la velocidad y se recuperó. Pero a los 5 minutos otra vez. Ya no puedo pasar de 80. ¿Qué será?'
msg2 = "Buenas, mi carro estaba normal hasta ayer. Hoy salí a la carretera y a los 20 minutos de manejar empecé a sentir que perdía fuerza, como que se ahogaba. Bajé la velocidad y se recuperó. Pero a los 5 minutos otra vez. Ya no puedo pasar de 80. ¿Qué será?"

st1 = ConversationState(session_id="s1")
h1 = ExtractorHechos.extraer_y_actualizar(st1, msg1)
print("Con comilla al inicio:", len(h1), [x["campo"] for x in h1])
print("Sintetizada 1:", SintetizadorConsulta.sintetizar(st1))

st2 = ConversationState(session_id="s2")
h2 = ExtractorHechos.extraer_y_actualizar(st2, msg2)
print("Sin comilla al inicio:", len(h2), [x["campo"] for x in h2])
print("Sintetizada 2:", SintetizadorConsulta.sintetizar(st2))
