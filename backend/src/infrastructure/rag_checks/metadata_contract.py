"""Adapta nombres del catálogo histórico sin ampliar su aplicabilidad documental."""
from src.infrastructure.rag.documental_tipos import normalizar_texto


def adaptar_metadata_historica(item: dict) -> dict:
    meta = dict(item)
    if meta.get('id_procedimiento'):
        meta.setdefault('doc_id', meta['id_procedimiento'])
    marca = str(meta.get('marca') or '')
    universal = any(t in normalizar_texto(marca) for t in ('universal', 'multimarca'))
    if universal:
        meta.setdefault('vehicle_scope', 'UNIVERSAL')
    elif marca:
        meta.setdefault('make', marca)
        meta.setdefault('model', meta.get('modelo'))
        meta.setdefault('vehicle_scope', 'SPECIFIC')
    return meta
