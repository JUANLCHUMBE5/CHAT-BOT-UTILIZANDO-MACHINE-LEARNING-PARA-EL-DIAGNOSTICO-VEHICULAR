export interface CasoIndicadorTesis {
  chatbot_prediccion: string | null;
  falla_real: string | null;
  prediccion_correcta: number | null;
  campos_completos: number | null;
  tiempo_diagnostico_minutos: number | null;
}

export interface IndicadoresTesisFase {
  prediccionesEvaluadas: number;
  aciertos: number;
  ppcf: number | null;
  registrosEvaluados: number;
  registrosCompletos: number;
  prdc: number | null;
  tiemposEvaluados: number;
  tiempoSuma: number;
  tprd: number | null;
}

export interface CasoExportacionOficial {
  fase: 'Pre-test' | 'Post-test' | string;
  tipo_registro?: string | null;
  estado_registro?: string | null;
  falla_real?: string | null;
  metodo_confirmacion?: string | null;
  evidencia_ref?: string | null;
  validado_por_id?: string | null;
  fecha_validacion?: string | null;
}

export function validarCasosParaExportacionOficial(casos: CasoExportacionOficial[]): boolean {
  return casos.length > 0 && casos.every((caso) => {
    const faseValida = (caso.fase === 'Pre-test' && caso.tipo_registro === 'THESIS_PRETEST') ||
      (caso.fase === 'Post-test' && caso.tipo_registro === 'THESIS_POSTTEST');
    return faseValida && caso.estado_registro === 'verificado' && Boolean(caso.falla_real?.trim()) &&
      Boolean(caso.metodo_confirmacion?.trim()) && Boolean(caso.evidencia_ref?.trim()) &&
      Boolean(caso.validado_por_id?.trim()) && Boolean(caso.fecha_validacion);
  });
}

export function calcularIndicadoresTesisFase(casos: CasoIndicadorTesis[]): IndicadoresTesisFase {
  const predicciones = casos.filter(
    (caso) =>
      Boolean(caso.chatbot_prediccion?.trim()) &&
      Boolean(caso.falla_real?.trim()) &&
      (caso.prediccion_correcta === 0 || caso.prediccion_correcta === 1),
  );
  const registros = casos.filter((caso) => caso.campos_completos === 0 || caso.campos_completos === 1);
  const tiempos = casos
    .map((caso) => caso.tiempo_diagnostico_minutos)
    .filter((tiempo): tiempo is number => tiempo !== null && Number.isFinite(tiempo) && tiempo > 0);
  const aciertos = predicciones.filter((caso) => caso.prediccion_correcta === 1).length;
  const registrosCompletos = registros.filter((caso) => caso.campos_completos === 1).length;
  const tiempoSuma = tiempos.reduce((total, tiempo) => total + tiempo, 0);

  return {
    prediccionesEvaluadas: predicciones.length,
    aciertos,
    ppcf: predicciones.length ? (aciertos / predicciones.length) * 100 : null,
    registrosEvaluados: registros.length,
    registrosCompletos,
    prdc: registros.length ? (registrosCompletos / registros.length) * 100 : null,
    tiemposEvaluados: tiempos.length,
    tiempoSuma,
    tprd: tiempos.length ? tiempoSuma / tiempos.length : null,
  };
}
