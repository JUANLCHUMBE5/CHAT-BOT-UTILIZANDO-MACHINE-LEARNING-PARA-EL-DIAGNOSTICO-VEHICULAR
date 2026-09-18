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
  const prePPCFCount = preCasos.filter((c) => c.prediccion_correcta === 1).length;
  const postPPCFCount = postCasos.filter((c) => c.prediccion_correcta === 1).length;
  const prePPCFPct = (prePPCFCount / preCasos.length) * 100;
  const postPPCFPct = (postPPCFCount / postCasos.length) * 100;

  // Ficha 2: PRDC (8 campos completos)
  const prePRDCCount = preCasos.filter((c) => c.campos_completos === 1).length;
  const postPRDCCount = postCasos.filter((c) => c.campos_completos === 1).length;
  const prePRDCPct = (prePRDCCount / preCasos.length) * 100;
  const postPRDCPct = (postPRDCCount / postCasos.length) * 100;

  // Ficha 3: TPRD (Tiempos en minutos)
  const preTPRDSuma = preCasos.reduce((acc, c) => acc + c.tiempo_diagnostico_minutos, 0);
  const postTPRDSuma = postCasos.reduce((acc, c) => acc + c.tiempo_diagnostico_minutos, 0);
  const preTPRDProm = preTPRDSuma / preCasos.length;
  const postTPRDProm = postTPRDSuma / postCasos.length;

  const infoFicha = {
    ficha1: {
      numero: 'Ficha de registro: Predicción de fallas vehiculares',
      codigo: 'Anexo 2 - Ficha 1',
      dimension: 'Predicción de fallas vehiculares',
      indicador: 'Porcentaje de predicción correcta de fallas vehiculares (PPCF)',
      medida: 'Porcentaje (%)',
      formula: 'PPCF = (N.° de predicciones correctas / Total de predicciones realizadas) × 100',
      preValor: `${prePPCFPct.toFixed(2)}%`,
      postValor: `${postPPCFPct.toFixed(2)}%`,
      preDetalle: `${prePPCFCount} de ${preCasos.length} predicciones correctas`,
      postDetalle: `${postPPCFCount} de ${postCasos.length} predicciones correctas`,
      mejora: `+${(postPPCFPct - prePPCFPct).toFixed(2)}% de incremento de exactitud`,
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
      preValor: `${prePRDCPct.toFixed(2)}%`,
      postValor: `${postPRDCPct.toFixed(2)}%`,
      preDetalle: `${prePRDCCount} de ${preCasos.length} con 8 campos completos`,
      postDetalle: `${postPRDCCount} de ${postCasos.length} con 8 campos completos`,
      mejora: `+${(postPRDCPct - prePRDCPct).toFixed(2)}% de incremento en calidad de datos`,
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
      preValor: `${preTPRDProm.toFixed(2)} min`,
      postValor: `${postTPRDProm.toFixed(2)} min`,
      preDetalle: `Suma: ${preTPRDSuma.toFixed(1)} min en 30 atenciones`,
      postDetalle: `Suma: ${postTPRDSuma.toFixed(1)} min en 30 atenciones`,
      mejora: `-${(preTPRDProm - postTPRDProm).toFixed(2)} min/auto (${(((preTPRDProm - postTPRDProm) / preTPRDProm) * 100).toFixed(1)}% ahorro de tiempo)`,
      hipotesis: 'HE3: El chatbot con ML reduce significativamente el tiempo de atención del diagnóstico vehicular (prueba inferencial pendiente)',
      unidad: ' min',
    },
  }[fichaActiva];

  const dataComparativaFichas = [
    { indicador: 'PPCF (% Acierto)', 'Pre-test (Manual)': Number(prePPCFPct.toFixed(1)), 'Post-test (CarBot AI)': Number(postPPCFPct.toFixed(1)) },
    { indicador: 'PRDC (% Campos 8/8)', 'Pre-test (Manual)': Number(prePRDCPct.toFixed(1)), 'Post-test (CarBot AI)': Number(postPRDCPct.toFixed(1)) },
    { indicador: 'TPRD (Minutos)', 'Pre-test (Manual)': Number(preTPRDProm.toFixed(1)), 'Post-test (CarBot AI)': Number(postTPRDProm.toFixed(1)) },
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
      r.tiempo_diagnostico_minutos,
      r.prediccion_correcta,
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `Fichas_Tesis_UCV_CarBot_${fichaActiva}_N60.csv`);
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
  };
};
