"""Separar estimación SVM, prioridad operativa y ausencia de inferencia."""

import math


def dato(objeto, campo, defecto=None):
    return objeto.get(campo, defecto) if isinstance(objeto, dict) else getattr(objeto, campo, defecto)


def unitario(valor):
    if isinstance(valor, (float, int)) and math.isfinite(valor) and 0 <= valor <= 1:
        return float(valor)
    return None


def estimacion_svm(dto, falla):
    if dto is None:
        return None
    for p in getattr(dto, 'predicciones_svm_raw', []) or []:
        if dato(p, 'falla') == falla:
            return unitario(dato(p, 'probabilidad'))
    for p in getattr(dto, 'predicciones_ml', []) or []:
        if dato(p, 'falla') == falla and dato(p, 'origen_probabilidad') == 'SVM':
            value = dato(p, 'statistical_probability')
            if value is not None:
                return unitario(value)
    return None


def describir_confianza(resultado):
    """Contrato aditivo: cero heredado nunca se convierte en certeza inventada."""
    dto = resultado.get('dto')
    falla = resultado.get('diagnostico_ml')
    estimate = estimacion_svm(dto, falla)
    decision = resultado.get('decision', '')
    abstencion = bool(getattr(dto, 'motivo_abstencion', None))
    if decision in {'PREGUNTAR', 'ACLARAR', 'PENDIENTE_MEDICION', 'SEGURIDAD_CRITICA',
                    'ABSTENCION_OEM_TOLERANCIA', 'DATOS_INSUFICIENTES'} or abstencion:
        estimate = None
    return {
        'estado': 'estimada_svm' if estimate is not None else 'sin_estimacion',
        'valor_svm': estimate,
        'valor_operativo': float(resultado.get('confianza_ml') or 0),
        'diagnostico_confirmado_fisicamente': False,
        'motivo': getattr(dto, 'motivo_abstencion', None) or decision,
    }
