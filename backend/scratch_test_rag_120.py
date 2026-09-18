import sys
sys.stdout.reconfigure(encoding='utf-8')
from src.infrastructure.container import ServiceContainer

rag = ServiceContainer.get_motor_rag()

queries = [
    'freno de mano electronico caliper motorizado trabado',
    'red can bus resistencias de terminacion 60 ohms pin 6 pin 14',
    'sensor angulo de direccion sas calibracion punto cero esp',
    'compresion de cilindros baja prueba leak down tester fugas de aire',
    'catalizador taponado contrapresion de escape manometro lambda p0420',
    'valvula pcv rota tapa de punterias succiona con silbido humo azul',
    'sensor tpms llanta testigo parpadea reaprendizaje id',
    'alternador voltaje carga ripple ac osciloscopio placa diodos'
]

print('=' * 80)
print('VALIDACIÓN DE RECUPERACIÓN RAG (120 PROCEDIMIENTOS INDEXADOS):')
print('=' * 80)
for q in queries:
    texto, titulo, score = rag.recuperar_contexto_con_similitud(q)
    print(f'Consulta: "{q}"')
    print(f' -> Procedimiento: {titulo}')
    print(f' -> Similitud Coseno: {score*100:.1f}%\n')
