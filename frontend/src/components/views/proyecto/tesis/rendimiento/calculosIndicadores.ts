import type { ResumenMetricas } from '../../../../../types';
import type { MetricasValidacionDTO } from '../../../../../types/api';

export interface IndicadoresVIResult {
  pctSintomas: string;
  pctProcesamiento: string;
  exactitudModelo: string;
  esMedicionPendiente: boolean;
  casosVerificados: number;
  notaMetodologica: string;
}

export function calcularIndicadoresVI(
  metricasValidacion: MetricasValidacionDTO | null
): IndicadoresVIResult {
  const vi = metricasValidacion?.variable_independiente;
  const casosVerificados = vi?.casos_verificados_evaluados ?? 0;

  const pctSintomas =
    vi?.indicador1_sintomas_correctos_pct !== null && vi?.indicador1_sintomas_correctos_pct !== undefined
      ? `${vi.indicador1_sintomas_correctos_pct}%`
      : 'Pendiente de medición';

  const pctProcesamiento =
    vi?.indicador2_procesamiento_correcto_pct !== null && vi?.indicador2_procesamiento_correcto_pct !== undefined
      ? `${vi.indicador2_procesamiento_correcto_pct}%`
      : 'Pendiente de medición';

  const exactitudModelo =
    vi?.indicador3_exactitud_ml_pct !== null && vi?.indicador3_exactitud_ml_pct !== undefined
      ? `${vi.indicador3_exactitud_ml_pct}%`
      : 'Pendiente de medición';

  const esMedicionPendiente = casosVerificados === 0;

  const notaMetodologica =
    vi?.nota_metodologica ||
    (esMedicionPendiente
      ? 'Pendiente de registro y verificación física de casos en taller.'
      : 'Cálculo exclusivo sobre casos con estado verificado con confirmación física en taller.');

  return {
    pctSintomas,
    pctProcesamiento,
    exactitudModelo,
    esMedicionPendiente,
    casosVerificados,
    notaMetodologica,
  };
}

export interface TelemetriaTecnicaResult {
  tiempoInferenciaMlTexto: string;
  tiempoTotalPipelineTexto: string;
  tiempoTotalSegundosTexto: string;
  totalConsultas: number;
}

export function calcularTelemetriaTecnica(
  metricas: ResumenMetricas | null,
  totalHistorial: number
): TelemetriaTecnicaResult {
  const totalConsultas = metricas?.diagnosticos_realizados ?? metricas?.diagnosticos_mes ?? totalHistorial;
  const tiempoTotalPipelineMs = metricas?.tiempo_promedio_ms ?? 0;

  // Medición dinámica real de inferencia ML (TF-IDF + Linear SVM).
  // NUNCA se estima con fórmulas arbitrarias (* 0.08). Si no hay medición en DB, muestra 'Sin medición'.
  const tiempoInferenciaMlMs = metricas?.tiempo_inferencia_ml_ms;
  const tiempoInferenciaMlTexto =
    tiempoInferenciaMlMs !== undefined && tiempoInferenciaMlMs !== null && tiempoInferenciaMlMs > 0
      ? `${tiempoInferenciaMlMs} ms`
      : 'Sin medición';

  const tiempoTotalPipelineTexto =
    tiempoTotalPipelineMs > 0 ? `${tiempoTotalPipelineMs} ms` : 'Sin medición';

  const tiempoTotalSegundosTexto =
    tiempoTotalPipelineMs > 0
      ? `${(tiempoTotalPipelineMs / 1000).toFixed(2)} s (Webhook -> Mensaje)`
      : 'Recepción a entrega';

  return {
    tiempoInferenciaMlTexto,
    tiempoTotalPipelineTexto,
    tiempoTotalSegundosTexto,
    totalConsultas,
  };
}
