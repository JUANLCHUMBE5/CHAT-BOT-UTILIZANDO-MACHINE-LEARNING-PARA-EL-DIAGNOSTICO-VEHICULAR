import type { PrediccionML } from '../types/domain';

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
