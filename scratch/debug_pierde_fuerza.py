import sys
sys.path.insert(0, 'backend')
from src.infrastructure.container import ServiceContainer
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.diagnostic_cache import diagnostico_cache
from src.core.diagnostico.auto_interrogador import evaluar_auto_pregunta_descarte

diagnostico_cache.limpiar()
ServiceContainer.reset()
gd = GestorDiagnostico()

# Test raw auto_interrogador
ap = evaluar_auto_pregunta_descarte('pierde fuerza', 'Falla en bujias o bobinas de encendido (misfire)', 0.5668, [
    {'falla': 'Falla en bujias o bobinas de encendido (misfire)', 'probabilidad': 0.5668},
    {'falla': 'Inyectores sucios o filtro de combustible obstruido', 'probabilidad': 0.198},
    {'falla': 'Bomba de gasolina quemada o con baja presion', 'probabilidad': 0.1098}
])
print("AP raw es_necesaria:", ap.es_necesaria if ap else None)

# Run full flow
res = gd.procesar_consulta_texto('pierde fuerza', session_id='dbg_c10')
print("Full flow diagnostico_ml:", res.diagnostico_ml)
print("Full flow modo:", res.modo_diagnostico)
print("Full flow estado_sesion:", res.estado_sesion)
print("Full flow tipo_consulta:", res.tipo_consulta)
