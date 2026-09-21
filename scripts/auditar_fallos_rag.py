import json
from pathlib import Path

data = json.load(open('docs/graficas/evaluacion_relevancia_rag.json', encoding='utf-8'))
fallos = [d for d in data['detalles'] if d['rank_relevante'] != 1]
print(f'Total fallos Hit@1: {len(fallos)}')
counts = {}
for d in data['detalles']:
    r = d['rank_relevante']
    counts[r] = counts.get(r, 0) + 1
print('Distribucion de ranks (0=no encontrado en top 5):', sorted(counts.items()))

print('\nDetalle de fallos:')
for f in fallos:
    idx = f['idx']
    esp = f['falla_esperada']
    rank = f['rank_relevante']
    top1 = f['candidatos_top5'][0]['titulo'] if f['candidatos_top5'] else 'NINGUNO'
    print(f"#{idx:02d} [Rank {rank}] Esp: {esp[:45]}")
    print(f"    Top1: {top1[:65]}")
