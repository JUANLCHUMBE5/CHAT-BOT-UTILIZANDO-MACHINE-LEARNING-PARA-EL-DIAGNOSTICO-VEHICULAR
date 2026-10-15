import { useState } from 'react';
import { DATOS_SINTETICOS_DEMO_60 } from '../data/fichasTesisData';

export type FichaTipo = 'ficha1' | 'ficha2' | 'ficha3';
export type FaseTipo = 'post' | 'pre' | 'contraste';

export const useTesisStats = () => {
  const [seccionActiva, setSeccionActiva] = useState<'fichas' | 'tracker_vivo'>('fichas');
  const [fichaActiva, setFichaActiva] = useState<FichaTipo>('ficha1');
  const [faseActiva, setFaseActiva] = useState<FaseTipo>('post');

  const preCasos = DATOS_SINTETICOS_DEMO_60.filter((c) => c.fase === 'Pre-test');
  const postCasos = DATOS_SINTETICOS_DEMO_60.filter((c) => c.fase === 'Post-test');
  const casosVisibles = faseActiva === 'pre' ? preCasos : postCasos;

  // Ficha 1: PPCF
  const evaluarPrediccion = (c: (typeof preCasos)[number]) => Boolean(
    c.chatbot_prediccion?.trim() && c.falla_real?.trim() && (c.prediccion_correcta === 0 || c.prediccion_correcta === 1),
  );
  const prePredicciones = preCasos.filter(evaluarPrediccion);
  const postPredicciones = postCasos.filter(evaluarPrediccion);
  const prePPCFCount = prePredicciones.filter((c) => c.prediccion_correcta === 1).length;
  const postPPCFCount = postPredicciones.filter((c) => c.prediccion_correcta === 1).length;
  const prePPCFPct = prePredicciones.length ? (prePPCFCount / prePredicciones.length) * 100 : null;
  const postPPCFPct = postPredicciones.length ? (postPPCFCount / postPredicciones.length) * 100 : null;

  // Ficha 2: PRDC (8 campos completos)
  const prePRDCCount = preCasos.filter((c) => c.campos_completos === 1).length;
  const postPRDCCount = postCasos.filter((c) => c.campos_completos === 1).length;
  const preRegistrosEvaluados = preCasos.filter((c) => c.campos_completos === 0 || c.campos_completos === 1).length;
  const postRegistrosEvaluados = postCasos.filter((c) => c.campos_completos === 0 || c.campos_completos === 1).length;
  const prePRDCPct = preRegistrosEvaluados ? (prePRDCCount / preRegistrosEvaluados) * 100 : null;
  const postPRDCPct = postRegistrosEvaluados ? (postPRDCCount / postRegistrosEvaluados) * 100 : null;

  // Ficha 3: TPRD (Tiempos en minutos)
  const preTiempos = preCasos.map((c) => c.tiempo_diagnostico_minutos)
    .filter((tiempo): tiempo is number => tiempo !== null && Number.isFinite(tiempo) && tiempo > 0);
  const postTiempos = postCasos.map((c) => c.tiempo_diagnostico_minutos)
    .filter((tiempo): tiempo is number => tiempo !== null && Number.isFinite(tiempo) && tiempo > 0);
  const preTPRDSuma = preTiempos.reduce((acc, tiempo) => acc + tiempo, 0);
  const postTPRDSuma = postTiempos.reduce((acc, tiempo) => acc + tiempo, 0);
  const preTPRDProm = preTiempos.length ? preTPRDSuma / preTiempos.length : null;
  const postTPRDProm = postTiempos.length ? postTPRDSuma / postTiempos.length : null;
  const porcentaje = (valor: number | null) => valor === null ? 'Pendiente' : `${valor.toFixed(2)}%`;

  const infoFicha = {
    ficha1: {
      numero: 'Ficha de registro: Predicción de fallas vehiculares',
      codigo: 'Anexo 2 - Ficha 1',
      dimension: 'Predicción de fallas vehiculares',
      indicador: 'Porcentaje de predicción correcta de fallas vehiculares (PPCF)',
      medida: 'Porcentaje (%)',
      formula: 'PPCF = (N.° de predicciones correctas / Total de predicciones realizadas) × 100',
      preValor: porcentaje(prePPCFPct),
      postValor: porcentaje(postPPCFPct),
      preDetalle: `${prePPCFCount} de ${prePredicciones.length} predicciones evaluables correctas`,
      postDetalle: `${postPPCFCount} de ${postPredicciones.length} predicciones evaluables correctas`,
      mejora: prePPCFPct === null || postPPCFPct === null ? 'Pendiente' : `${(postPPCFPct - prePPCFPct).toFixed(2)} pp`,
      hipotesis: 'HE1: El chatbot con ML mejora significativamente la predicción de fallas vehiculares (prueba inferencial pendiente)',
      unidad: '%',
    },
    ficha2: {
      numero: 'Ficha de registro: Control de información diagnóstica vehicular',
      codigo: 'Anexo 2 - Ficha 2',
      dimension: 'Control de información diagnóstica vehicular',
      indicador: 'Porcentaje de registros diagnósticos completos (PRDC)',
      medida: 'Porcentaje (%)',
      formula: 'PRDC = (RC: Registros con los 8 campos completos / TRE: Total de registros evaluados) × 100',
      preValor: porcentaje(prePRDCPct),
      postValor: porcentaje(postPRDCPct),
      preDetalle: `${prePRDCCount} de ${preRegistrosEvaluados} evaluados con 8 campos completos`,
      postDetalle: `${postPRDCCount} de ${postRegistrosEvaluados} evaluados con 8 campos completos`,
      mejora: prePRDCPct === null || postPRDCPct === null ? 'Pendiente' : `${(postPRDCPct - prePRDCPct).toFixed(2)} pp`,
      hipotesis: 'HE2: El chatbot con ML mejora significativamente el control de información diagnóstica (prueba inferencial pendiente)',
      unidad: '%',
    },
    ficha3: {
      numero: 'Ficha de registro: Eficiencia del diagnóstico vehicular',
      codigo: 'Anexo 2 - Ficha 3',
      dimension: 'Eficiencia del diagnóstico vehicular',
      indicador: 'Tiempo promedio de respuesta diagnóstica (TPRD)',
      medida: 'Minutos',
      formula: 'TPRD = Suma total de tiempos de respuesta diagnóstica / Total de diagnósticos evaluados',
      preValor: preTPRDProm === null ? 'Pendiente' : `${preTPRDProm.toFixed(2)} min`,
      postValor: postTPRDProm === null ? 'Pendiente' : `${postTPRDProm.toFixed(2)} min`,
      preDetalle: `Suma: ${preTiempos.length ? `${preTPRDSuma.toFixed(1)} min en ${preTiempos.length} mediciones` : 'Pendiente'}`,
      postDetalle: `Suma: ${postTiempos.length ? `${postTPRDSuma.toFixed(1)} min en ${postTiempos.length} mediciones` : 'Pendiente'}`,
      mejora: preTPRDProm === null || postTPRDProm === null ? 'Pendiente' : `${(preTPRDProm - postTPRDProm).toFixed(2)} min`,
      hipotesis: 'HE3: El chatbot con ML reduce significativamente el tiempo de atención del diagnóstico vehicular (prueba inferencial pendiente)',
      unidad: ' min',
    },
  }[fichaActiva];

  const dataComparativaFichas = [
    { indicador: 'PPCF (% Acierto)', 'Pre-test (Manual)': prePPCFPct === null ? null : Number(prePPCFPct.toFixed(1)), 'Post-test (CarBot AI)': postPPCFPct === null ? null : Number(postPPCFPct.toFixed(1)) },
    { indicador: 'PRDC (% Campos 8/8)', 'Pre-test (Manual)': prePRDCPct === null ? null : Number(prePRDCPct.toFixed(1)), 'Post-test (CarBot AI)': postPRDCPct === null ? null : Number(postPRDCPct.toFixed(1)) },
    { indicador: 'TPRD (Minutos)', 'Pre-test (Manual)': preTPRDProm === null ? null : Number(preTPRDProm.toFixed(1)), 'Post-test (CarBot AI)': postTPRDProm === null ? null : Number(postTPRDProm.toFixed(1)) },
  ];

  const exportarCSV = () => {
    const headers = ['Item', 'Fase', 'Fecha', 'Placa', 'Marca_Modelo', 'Sintoma', 'Falla_Real', 'Chatbot_Prediccion', 'Campos_Completos', 'Tiempo_Minutos', 'Prediccion_Correcta'];
    const rows = DATOS_SINTETICOS_DEMO_60.map((r) => [
      r.item,
      r.fase,
      r.fecha,
      r.placa,
      `"${r.marca_modelo}"`,
      `"${r.sintoma}"`,
      `"${r.falla_real}"`,
      `"${r.chatbot_prediccion}"`,
      r.campos_completos,
      r.tiempo_diagnostico_minutos ?? 'Pendiente',
      r.prediccion_correcta,
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `DEMO_SINTETICO_Fichas_Tesis_UCV_CarBot_${fichaActiva}_N60.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return {
    seccionActiva,
    setSeccionActiva,
    fichaActiva,
    setFichaActiva,
    faseActiva,
    setFaseActiva,
    preCasos,
    postCasos,
    casosVisibles,
    infoFicha,
    dataComparativaFichas,
    exportarCSV,
    esModoDemostracion: true,
    avisoMetodologico: 'Trabajo de campo pendiente. Esta vista contiene datos sintéticos de demostración, excluidos de resultados y exportaciones oficiales.',
  };
};
