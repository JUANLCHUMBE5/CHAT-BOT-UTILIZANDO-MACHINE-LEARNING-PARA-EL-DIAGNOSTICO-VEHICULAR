import json
import unicodedata

def norm(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')

data = json.load(open('machine_learning/manuals/metadatos_manuales.json', encoding='utf-8'))
terminos = ['balanceo', 'alineacion', 'embrague', 'suspension', 'homocinetica', 'palier', 'distribucion', 'cadena', 'dualogic', 'frenos de aire', 'compresor', 'amortiguador', 'caja', 'aceite', 'bomba']
for t in terminos:
    encontrados = [d['titulo'] for d in data if norm(t) in norm(d['titulo'])]
    print(f'Termino "{t}": {len(encontrados)} procedimientos')
    for tit in encontrados[:3]:
        print(f'   - {tit[:80]}')
