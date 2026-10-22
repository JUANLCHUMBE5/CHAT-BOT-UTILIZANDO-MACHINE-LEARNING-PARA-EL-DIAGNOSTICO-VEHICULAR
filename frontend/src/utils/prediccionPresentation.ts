import type { Diagnostico, PrediccionML } from '../types/domain';

function valorUnitario(value: number | null | undefined): number | null {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1
    ? value
    : null;
}

/** No inferir probabilidad a partir del score heredado ni de una regla. */
export function presentarPrediccion(prediccion: PrediccionML) {
  const fuente = prediccion.prediction_source ?? prediccion.origen_probabilidad;
  const probabilidad = fuente?.startsWith('REGLA')
    ? null
    : valorUnitario(prediccion.statistical_probability);
  const score = valorUnitario(prediccion.operational_score);
  const porcentaje = probabilidad === null ? null : probabilidad * 100;
  return {
    porcentaje,
    probabilidadTexto: porcentaje === null
      ? 'Sin probabilidad estadística'
      : `Probabilidad SVM: ${porcentaje.toFixed(1)} %`,
    scoreTexto: score === null ? null : `Score operativo: ${score.toFixed(3)} (no es probabilidad)`,
  };
}

/** Una aclaración o abstención no es un diagnóstico con probabilidad cero. */
export function presentarConfianzaDiagnostico(diagnostico: Pick<Diagnostico, 'confianza_detalle' | 'predicciones_ml'>) {
  const detalle = diagnostico.confianza_detalle;
  const principal = diagnostico.predicciones_ml?.find((p) => p.orden === 1)
    ?? diagnostico.predicciones_ml?.[0];
  const valor = detalle && Object.keys(detalle).length > 0
    ? (detalle.estado === 'estimada_svm' ? valorUnitario(detalle.valor_svm) : null)
    : (principal ? presentarPrediccion(principal).porcentaje : null);
  const porcentaje = detalle && Object.keys(detalle).length > 0
    ? (valor === null ? null : valor * 100) : valor;
  return {
    porcentaje,
    etiqueta: porcentaje === null ? 'Sin estimación' : `Est. SVM ${porcentaje.toFixed(1)}%`,
    titulo: porcentaje === null
      ? 'Aún no existe una estimación SVM verificable para esta respuesta.'
      : 'Estimación del clasificador SVM; no confirma una avería física ni equivale al puntaje operativo.',
  };
}
