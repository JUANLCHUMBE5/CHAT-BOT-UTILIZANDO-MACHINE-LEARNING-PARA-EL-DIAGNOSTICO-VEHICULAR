"""Acciones declaradas con antecedente inequívoco, nunca descartes implícitos."""
import re

from src.core.conversacion.evidencia_acciones import normalizar
from src.core.conversacion.models import FactType


def interpretar_accion_previa(estado, texto, pregunta):
    mensaje = normalizar(texto).strip().rstrip(".! ")
    reemplazo = re.fullmatch(
        r"(?:ya (?:lo|la|las|los) cambie|ya se cambiaron|recien puesto|es nuevo|son nuevas|son nuevos)",
        mensaje,
    )
    inspeccion = re.fullmatch(r"(?:ya (?:lo|la|las|los) revise|eso ya probe)", mensaje)
    if not reemplazo and not inspeccion:
        return None
    contexto = (pregunta or {}).get("texto", "")
    if not contexto:
        contexto = next((m for m in reversed(estado.historial_mensajes_usuario)
                         if normalizar(m).strip().rstrip(".! ") != mensaje), "")
    piezas = [p for p in ("bujias", "bobina", "pastillas", "bomba", "filtro", "termostato",
                          "bateria", "alternador", "arrancador")
              if re.search(rf"\b{p}s?\b", normalizar(contexto))]
    pieza = piezas[0] if len(piezas) == 1 else "componente no identificado"
    pieza = "bujías" if pieza == "bujias" else pieza
    accion = "reemplazado" if reemplazo else "inspeccionado"
    campo = f"{accion}_{pieza}"
    valor = f"{pieza}: {accion}, resultado no confirmado"
    hecho = estado.registrar_hecho(
        campo, valor, categoria="antecedente" if reemplazo else "prueba_realizada",
        texto_crudo=texto, tipo=FactType.CONDICION,
    )
    return {"categoria_respuesta": "COMPONENTE", "campo": campo,
            "valor": valor, "hecho": hecho.to_dict()}
