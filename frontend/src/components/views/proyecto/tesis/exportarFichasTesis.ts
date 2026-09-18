import { METADATA_TESIS, type RegistroTesis } from '../../../../data/fichasTesisData';

export function descargarFichasOficialesTesisCSV(casos: RegistroTesis[], esModoDemo = false) {
  const pre: RegistroTesis[] = casos.filter((c) => c.fase === 'Pre-test');
  const post: RegistroTesis[] = casos.filter((c) => c.fase === 'Post-test');

  // Cálculos Ficha 1 (PPCF)
  const preAciertos = pre.filter((c) => c.prediccion_correcta === 1).length;
  const postAciertos = post.filter((c) => c.prediccion_correcta === 1).length;
  const prePPCF = pre.length > 0 ? (preAciertos / pre.length) * 100 : 0;
  const postPPCF = post.length > 0 ? (postAciertos / post.length) * 100 : 0;

  // Cálculos Ficha 2 (PRDC)
  const preCompletos = pre.filter((c) => c.campos_completos === 1).length;
  const postCompletos = post.filter((c) => c.campos_completos === 1).length;
  const prePRDC = pre.length > 0 ? (preCompletos / pre.length) * 100 : 0;
  const postPRDC = post.length > 0 ? (postCompletos / post.length) * 100 : 0;

  // Cálculos Ficha 3 (TPRD)
  const preTiempoSuma = pre.reduce((acc: number, c: RegistroTesis) => acc + c.tiempo_diagnostico_minutos, 0);
  const postTiempoSuma = post.reduce((acc: number, c: RegistroTesis) => acc + c.tiempo_diagnostico_minutos, 0);
  const preTPRD = pre.length > 0 ? preTiempoSuma / pre.length : 0;
  const postTPRD = post.length > 0 ? postTiempoSuma / post.length : 0;

  const lines: string[] = [];

  const escapeCSV = (val: string | number) => {
    const s = String(val);
    if (s.includes(',') || s.includes('"') || s.includes('\n')) {
      return `"${s.replace(/"/g, '""')}"`;
    }
    return s;
  };

  const addRow = (...cells: (string | number)[]) => {
    lines.push(cells.map(escapeCSV).join(','));
  };

  // 1. Encabezado institucional UCV
  addRow('UNIVERSIDAD CÉSAR VALLEJO - ESCUELA PROFESIONAL DE INGENIERÍA DE SISTEMAS');
  addRow('PROYECTO DE TESIS:', METADATA_TESIS.titulo);
  addRow('AUTORES:', METADATA_TESIS.autores);
  addRow('SEDE / TALLER:', METADATA_TESIS.sede);
  addRow('DISEÑO EXPERIMENTAL:', METADATA_TESIS.diseno);

  if (esModoDemo) {
    addRow('');
    addRow('>>> ADVERTENCIA METODOLÓGICA: ESTE ARCHIVO FUE GENERADO EN MODO DEMOSTRACIÓN CON DATOS SINTÉTICOS. <<<');
    addRow('>>> ESTOS DATOS ESTÁN ESTRICTAMENTE EXCLUIDOS DE LOS RESULTADOS FINALES Y SUSTENTACIÓN DE TESIS. <<<');
    addRow('');
  } else {
    addRow('');
    addRow('ESTADO DE TRABAJO DE CAMPO:', `Avance actual: ${casos.length} de 60 casos reales registrados.`);
    addRow('NOTA:', 'Resultados oficiales sujetos a la recolección y verificación física en el taller.');
    addRow('');
  }

  // 2. Ficha 1 Pre-test
  addRow('========================================================================================================');
  addRow('ANEXO 2 - FICHA DE REGISTRO: PREDICCIÓN DE FALLAS VEHICULARES (PPCF) - FASE: PRE-TEST');
  addRow('Variable: Diagnóstico vehicular', 'Dimensión: Predicción de fallas vehiculares');
  addRow('Indicador: Porcentaje de predicción correcta de fallas vehiculares (PPCF)', 'Medida: Porcentaje (%)');
  addRow('Fórmula: PPCF = (N.° de predicciones correctas / Total de predicciones realizadas) × 100');
  addRow('');
  addRow(
    'Ítem',
    'Fecha',
    'Placa',
    'Marca / Modelo',
    'N.° Vehículos Atendidos',
    'Total Predicciones Realizadas',
    'N.° Predicciones Correctas',
    '% Predicción Correcta',
    'Síntoma Reportado',
    'Falla Real Confirmada',
    'Hipótesis Inicial del Mecánico'
  );
  if (pre.length === 0) {
    addRow('Sin registros', '-', '-', '-', 0, 0, 0, '0.00%', 'Pendiente de trabajo de campo', '-', '-');
  } else {
    pre.forEach((c: RegistroTesis, idx: number) => {
      addRow(
        idx + 1,
        c.fecha,
        c.placa,
        c.marca_modelo,
        1,
        1,
        c.prediccion_correcta,
        c.prediccion_correcta === 1 ? '100%' : '0%',
        c.sintoma,
        c.falla_real,
        c.chatbot_prediccion
      );
    });
  }
  addRow('TOTALES PRE-TEST', '', '', '', pre.length, pre.length, preAciertos, `${prePPCF.toFixed(2)}%`, '', '', '');
  addRow('PPCF PROMEDIO GENERAL PRE-TEST:', `${prePPCF.toFixed(2)}%`);
  addRow('');

  // 3. Ficha 1 Post-test
  addRow('========================================================================================================');
  addRow('ANEXO 2 - FICHA DE REGISTRO: PREDICCIÓN DE FALLAS VEHICULARES (PPCF) - FASE: POST-TEST (CARBOT AI)');
  addRow('Variable: Diagnóstico vehicular', 'Dimensión: Predicción de fallas vehiculares');
  addRow('Indicador: Porcentaje de predicción correcta de fallas vehiculares (PPCF)', 'Medida: Porcentaje (%)');
  addRow('Fórmula: PPCF = (N.° de predicciones correctas / Total de predicciones realizadas) × 100');
  addRow('');
  addRow(
    'Ítem',
    'Fecha',
    'Placa',
    'Marca / Modelo',
    'N.° Vehículos Atendidos',
    'Total Predicciones Realizadas',
    'N.° Predicciones Correctas',
    '% Predicción Correcta',
    'Síntoma Reportado',
    'Falla Real Confirmada',
    'Predicción Asistida por CarBot'
  );
  if (post.length === 0) {
    addRow('Sin registros', '-', '-', '-', 0, 0, 0, '0.00%', 'Pendiente de trabajo de campo', '-', '-');
  } else {
    post.forEach((c: RegistroTesis, idx: number) => {
      addRow(
        idx + 1,
        c.fecha,
        c.placa,
        c.marca_modelo,
        1,
        1,
        c.prediccion_correcta,
        c.prediccion_correcta === 1 ? '100%' : '0%',
        c.sintoma,
        c.falla_real,
        c.chatbot_prediccion
      );
    });
  }
  addRow('TOTALES POST-TEST', '', '', '', post.length, post.length, postAciertos, `${postPPCF.toFixed(2)}%`, '', '', '');
  addRow('PPCF PROMEDIO GENERAL POST-TEST:', `${postPPCF.toFixed(2)}%`);
  addRow('');

  // 4. Ficha 2 Pre-test
  addRow('========================================================================================================');
  addRow('ANEXO 2 - FICHA DE REGISTRO: CONTROL DE INFORMACIÓN DIAGNÓSTICA (PRDC) - FASE: PRE-TEST');
  addRow('Variable: Diagnóstico vehicular', 'Dimensión: Control de información diagnóstica vehicular');
  addRow('Indicador: Porcentaje de registros diagnósticos completos (PRDC)', 'Medida: Porcentaje (%)');
  addRow('Fórmula: PRDC = (Registros completos 8 campos / Total registros evaluados) × 100');
  addRow('');
  addRow(
    'Ítem',
    'Fecha',
    'Placa',
    'Marca / Modelo',
    'Total Registros Evaluados (TRE)',
    'Registros Completos (RC)',
    '% Registros Completos (PRDC)',
    'Observación'
  );
  if (pre.length === 0) {
    addRow('Sin registros', '-', '-', '-', 0, 0, '0.00%', 'Pendiente de trabajo de campo');
  } else {
    pre.forEach((c: RegistroTesis, idx: number) => {
      addRow(
        idx + 1,
        c.fecha,
        c.placa,
        c.marca_modelo,
        1,
        c.campos_completos,
        c.campos_completos === 1 ? '100%' : '0%',
        c.campos_completos === 1 ? '8/8 campos' : 'Incompleto'
      );
    });
  }
  addRow('TOTALES PRE-TEST', '', '', '', pre.length, preCompletos, `${prePRDC.toFixed(2)}%`, '');
  addRow('PRDC PROMEDIO GENERAL PRE-TEST:', `${prePRDC.toFixed(2)}%`);
  addRow('');

  // 5. Ficha 2 Post-test
  addRow('========================================================================================================');
  addRow('ANEXO 2 - FICHA DE REGISTRO: CONTROL DE INFORMACIÓN DIAGNÓSTICA (PRDC) - FASE: POST-TEST (CARBOT AI)');
  addRow('Variable: Diagnóstico vehicular', 'Dimensión: Control de información diagnóstica vehicular');
  addRow('Indicador: Porcentaje de registros diagnósticos completos (PRDC)', 'Medida: Porcentaje (%)');
  addRow('Fórmula: PRDC = (Registros completos 8 campos / Total registros evaluados) × 100');
  addRow('');
  addRow(
    'Ítem',
    'Fecha',
    'Placa',
    'Marca / Modelo',
    'Total Registros Evaluados (TRE)',
    'Registros Completos (RC)',
    '% Registros Completos (PRDC)',
    'Observación'
  );
  if (post.length === 0) {
    addRow('Sin registros', '-', '-', '-', 0, 0, '0.00%', 'Pendiente de trabajo de campo');
  } else {
    post.forEach((c: RegistroTesis, idx: number) => {
      addRow(
        idx + 1,
        c.fecha,
        c.placa,
        c.marca_modelo,
        1,
        c.campos_completos,
        c.campos_completos === 1 ? '100%' : '0%',
        c.campos_completos === 1 ? '8/8 campos' : 'Incompleto'
      );
    });
  }
  addRow('TOTALES POST-TEST', '', '', '', post.length, postCompletos, `${postPRDC.toFixed(2)}%`, '');
  addRow('PRDC PROMEDIO GENERAL POST-TEST:', `${postPRDC.toFixed(2)}%`);
  addRow('');

  // 6. Ficha 3 Pre-test
  addRow('========================================================================================================');
  addRow('ANEXO 2 - FICHA DE REGISTRO: EFICIENCIA DEL DIAGNÓSTICO (TPRD) - FASE: PRE-TEST');
  addRow('Variable: Diagnóstico vehicular', 'Dimensión: Eficiencia del diagnóstico vehicular');
  addRow('Indicador: Tiempo promedio de respuesta diagnóstica (TPRD)', 'Medida: Minutos');
  addRow('Fórmula: TPRD = Suma total de tiempos de respuesta / Total de diagnósticos evaluados');
  addRow('');
  addRow(
    'Ítem',
    'Fecha',
    'Placa',
    'Marca / Modelo',
    'N.° Diagnósticos Evaluados',
    'Suma Tiempos (min)',
    'Promedio (min)',
    'Síntoma',
    'Falla Confirmada'
  );
  if (pre.length === 0) {
    addRow('Sin registros', '-', '-', '-', 0, 0, 0, 'Pendiente de trabajo de campo', '-');
  } else {
    pre.forEach((c: RegistroTesis, idx: number) => {
      addRow(
        idx + 1,
        c.fecha,
        c.placa,
        c.marca_modelo,
        1,
        c.tiempo_diagnostico_minutos,
        c.tiempo_diagnostico_minutos,
        c.sintoma,
        c.falla_real
      );
    });
  }
  addRow('TOTALES PRE-TEST', '', '', '', pre.length, `${preTiempoSuma} min`, `${preTPRD.toFixed(2)} min`, '', '');
  addRow('TPRD PROMEDIO GENERAL PRE-TEST:', `${preTPRD.toFixed(2)} minutos`);
  addRow('');

  // 7. Ficha 3 Post-test
  addRow('========================================================================================================');
  addRow('ANEXO 2 - FICHA DE REGISTRO: EFICIENCIA DEL DIAGNÓSTICO (TPRD) - FASE: POST-TEST (CARBOT AI)');
  addRow('Variable: Diagnóstico vehicular', 'Dimensión: Eficiencia del diagnóstico vehicular');
  addRow('Indicador: Tiempo promedio de respuesta diagnóstica (TPRD)', 'Medida: Minutos');
  addRow('Fórmula: TPRD = Suma total de tiempos de respuesta / Total de diagnósticos evaluados');
  addRow('');
  addRow(
    'Ítem',
    'Fecha',
    'Placa',
    'Marca / Modelo',
    'N.° Diagnósticos Evaluados',
    'Suma Tiempos (min)',
    'Promedio (min)',
    'Síntoma',
    'Falla Confirmada'
  );
  if (post.length === 0) {
    addRow('Sin registros', '-', '-', '-', 0, 0, 0, 'Pendiente de trabajo de campo', '-');
  } else {
    post.forEach((c: RegistroTesis, idx: number) => {
      addRow(
        idx + 1,
        c.fecha,
        c.placa,
        c.marca_modelo,
        1,
        c.tiempo_diagnostico_minutos,
        c.tiempo_diagnostico_minutos,
        c.sintoma,
        c.falla_real
      );
    });
  }
  addRow('TOTALES POST-TEST', '', '', '', post.length, `${postTiempoSuma} min`, `${postTPRD.toFixed(2)} min`, '', '');
  addRow('TPRD PROMEDIO GENERAL POST-TEST:', `${postTPRD.toFixed(2)} minutos`);
  addRow('');

  // 8. Resumen Comparativo Pre vs Post y Estado Metodológico
  addRow('========================================================================================================');
  addRow('RESUMEN COMPARATIVO Y ESTADO METODOLÓGICO DE HIPÓTESIS');
  addRow('Indicador / Ficha', 'Pre-test', 'Post-test', 'Diferencia (Post - Pre)', 'Estado Metodológico');
  addRow(
    'Ficha 1 · Predicción de fallas vehiculares (PPCF)',
    pre.length > 0 ? `${prePPCF.toFixed(2)}%` : 'Sin datos',
    post.length > 0 ? `${postPPCF.toFixed(2)}%` : 'Sin datos',
    pre.length > 0 && post.length > 0 ? `${(postPPCF - prePPCF).toFixed(2)} pp` : 'Pendiente',
    'Contraste de hipótesis y prueba inferencial pendientes de completar el trabajo de campo de 60 registros reales y validación con el asesor estadístico (evaluar si corresponde prueba pareada o de muestras independientes).'
  );
  addRow(
    'Ficha 2 · Registros diagnósticos completos (PRDC)',
    pre.length > 0 ? `${prePRDC.toFixed(2)}%` : 'Sin datos',
    post.length > 0 ? `${postPRDC.toFixed(2)}%` : 'Sin datos',
    pre.length > 0 && post.length > 0 ? `${(postPRDC - prePRDC).toFixed(2)} pp` : 'Pendiente',
    'Contraste de hipótesis y prueba inferencial pendientes de completar el trabajo de campo de 60 registros reales y validación con el asesor estadístico (evaluar si corresponde prueba pareada o de muestras independientes).'
  );
  addRow(
    'Ficha 3 · Tiempo promedio de respuesta (TPRD)',
    pre.length > 0 ? `${preTPRD.toFixed(2)} min` : 'Sin datos',
    post.length > 0 ? `${postTPRD.toFixed(2)} min` : 'Sin datos',
    pre.length > 0 && post.length > 0 ? `${(preTPRD - postTPRD).toFixed(2)} min` : 'Pendiente',
    'Contraste de hipótesis y prueba inferencial pendientes de completar el trabajo de campo de 60 registros reales y validación con el asesor estadístico (evaluar si corresponde prueba pareada o de muestras independientes).'
  );

  // Descarga con UTF-8 BOM para compatibilidad total con Excel en español
  const blob = new Blob(['\uFEFF' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  const prefijo = esModoDemo ? 'DEMO_SINTETICO_Fichas_Tesis_UCV_' : 'OFICIAL_Fichas_Tesis_UCV_Anexo2_';
  link.setAttribute('href', url);
  link.setAttribute('download', `${prefijo}${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
