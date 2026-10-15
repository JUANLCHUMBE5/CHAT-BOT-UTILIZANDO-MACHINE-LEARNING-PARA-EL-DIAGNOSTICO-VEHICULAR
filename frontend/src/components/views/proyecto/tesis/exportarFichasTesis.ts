import { METADATA_TESIS, type RegistroTesis } from '../../../../data/fichasTesisData';
import { calcularIndicadoresTesisFase, validarCasosParaExportacionOficial } from '../../../../utils/tesisIndicadores';

export function descargarFichasOficialesTesisCSV(
  casos: RegistroTesis[],
  modo: 'demostracion' | 'oficial',
) {
  const pre: RegistroTesis[] = casos.filter((c) => c.fase === 'Pre-test');
  const post: RegistroTesis[] = casos.filter((c) => c.fase === 'Post-test');
  if (modo === 'oficial' && !validarCasosParaExportacionOficial(casos)) {
    throw new Error('La exportación oficial requiere casos oficiales verificados con trazabilidad humana completa.');
  }

  const preMetricas = calcularIndicadoresTesisFase(pre);
  const postMetricas = calcularIndicadoresTesisFase(post);
  const { aciertos: preAciertos, ppcf: prePPCF, registrosCompletos: preCompletos,
    prdc: prePRDC, tiempoSuma: preTiempoSuma, tprd: preTPRD } = preMetricas;
  const { aciertos: postAciertos, ppcf: postPPCF, registrosCompletos: postCompletos,
    prdc: postPRDC, tiempoSuma: postTiempoSuma, tprd: postTPRD } = postMetricas;
  const porcentaje = (valor: number | null) => valor === null ? 'Pendiente' : `${valor.toFixed(2)}%`;
  const promedioTiempo = (valor: number | null) => valor === null ? 'Pendiente' : `${valor.toFixed(2)}`;

  const lines: string[] = [];

  const escapeCSV = (val: string | number | null) => {
    const s = val === null ? 'Pendiente' : String(val);
    if (s.includes(',') || s.includes('"') || s.includes('\n')) {
      return `"${s.replace(/"/g, '""')}"`;
    }
    return s;
  };

  const addRow = (...cells: (string | number | null)[]) => {
    lines.push(cells.map(escapeCSV).join(','));
  };

  // 1. Encabezado institucional UCV
  addRow('UNIVERSIDAD CÉSAR VALLEJO - ESCUELA PROFESIONAL DE INGENIERÍA DE SISTEMAS');
  addRow('PROYECTO DE TESIS:', METADATA_TESIS.titulo);
  addRow('AUTORES:', METADATA_TESIS.autores);
  addRow('SEDE / TALLER:', METADATA_TESIS.sede);
  addRow('DISEÑO EXPERIMENTAL:', METADATA_TESIS.diseno);

  if (modo === 'demostracion') {
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
    addRow('Sin registros', '-', '-', '-', 0, 0, 0, 'Pendiente', 'Pendiente de trabajo de campo', '-', '-');
  } else {
    pre.forEach((c: RegistroTesis, idx: number) => {
      addRow(
        idx + 1,
        c.fecha,
        c.placa,
        c.marca_modelo,
        1,
        c.chatbot_prediccion?.trim() && c.falla_real?.trim() && [0, 1].includes(c.prediccion_correcta ?? -1) ? 1 : 0,
        c.prediccion_correcta,
        c.prediccion_correcta === null ? 'Pendiente' : c.prediccion_correcta === 1 ? '100%' : '0%',
        c.sintoma,
        c.falla_real,
        c.chatbot_prediccion
      );
    });
  }
  addRow('TOTALES PRE-TEST', '', '', '', pre.length, preMetricas.prediccionesEvaluadas, preAciertos, porcentaje(prePPCF), '', '', '');
  addRow('PPCF PROMEDIO GENERAL PRE-TEST:', porcentaje(prePPCF));
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
    addRow('Sin registros', '-', '-', '-', 0, 0, 0, 'Pendiente', 'Pendiente de trabajo de campo', '-', '-');
  } else {
    post.forEach((c: RegistroTesis, idx: number) => {
      addRow(
        idx + 1,
        c.fecha,
        c.placa,
        c.marca_modelo,
        1,
        c.chatbot_prediccion?.trim() && c.falla_real?.trim() && [0, 1].includes(c.prediccion_correcta ?? -1) ? 1 : 0,
        c.prediccion_correcta,
        c.prediccion_correcta === null ? 'Pendiente' : c.prediccion_correcta === 1 ? '100%' : '0%',
        c.sintoma,
        c.falla_real,
        c.chatbot_prediccion
      );
    });
  }
  addRow('TOTALES POST-TEST', '', '', '', post.length, postMetricas.prediccionesEvaluadas, postAciertos, porcentaje(postPPCF), '', '', '');
  addRow('PPCF PROMEDIO GENERAL POST-TEST:', porcentaje(postPPCF));
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
    addRow('Sin registros', '-', '-', '-', 0, 0, 'Pendiente', 'Pendiente de trabajo de campo');
  } else {
    pre.forEach((c: RegistroTesis, idx: number) => {
      addRow(
        idx + 1,
        c.fecha,
        c.placa,
        c.marca_modelo,
        c.campos_completos === null ? 0 : 1,
        c.campos_completos,
        c.campos_completos === null ? 'Pendiente' : c.campos_completos === 1 ? '100%' : '0%',
        c.campos_completos === null ? 'Pendiente de evaluación' : c.campos_completos === 1 ? '8/8 campos' : 'Incompleto'
      );
    });
  }
  addRow('TOTALES PRE-TEST', '', '', '', preMetricas.registrosEvaluados, preCompletos, porcentaje(prePRDC), '');
  addRow('PRDC PROMEDIO GENERAL PRE-TEST:', porcentaje(prePRDC));
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
    addRow('Sin registros', '-', '-', '-', 0, 0, 'Pendiente', 'Pendiente de trabajo de campo');
  } else {
    post.forEach((c: RegistroTesis, idx: number) => {
      addRow(
        idx + 1,
        c.fecha,
        c.placa,
        c.marca_modelo,
        c.campos_completos === null ? 0 : 1,
        c.campos_completos,
        c.campos_completos === null ? 'Pendiente' : c.campos_completos === 1 ? '100%' : '0%',
        c.campos_completos === null ? 'Pendiente de evaluación' : c.campos_completos === 1 ? '8/8 campos' : 'Incompleto'
      );
    });
  }
  addRow('TOTALES POST-TEST', '', '', '', postMetricas.registrosEvaluados, postCompletos, porcentaje(postPRDC), '');
  addRow('PRDC PROMEDIO GENERAL POST-TEST:', porcentaje(postPRDC));
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
    addRow('Sin registros', '-', '-', '-', 0, 'Pendiente', 'Pendiente', 'Pendiente de trabajo de campo', '-');
  } else {
    pre.forEach((c: RegistroTesis, idx: number) => {
      addRow(
        idx + 1,
        c.fecha,
        c.placa,
        c.marca_modelo,
        c.tiempo_diagnostico_minutos !== null && Number.isFinite(c.tiempo_diagnostico_minutos) && c.tiempo_diagnostico_minutos > 0 ? 1 : 0,
        c.tiempo_diagnostico_minutos !== null && Number.isFinite(c.tiempo_diagnostico_minutos) && c.tiempo_diagnostico_minutos > 0 ? c.tiempo_diagnostico_minutos : null,
        c.tiempo_diagnostico_minutos !== null && Number.isFinite(c.tiempo_diagnostico_minutos) && c.tiempo_diagnostico_minutos > 0 ? c.tiempo_diagnostico_minutos : null,
        c.sintoma,
        c.falla_real
      );
    });
  }
  addRow('TOTALES PRE-TEST', '', '', '', preMetricas.tiemposEvaluados,
    preMetricas.tiemposEvaluados ? `${preTiempoSuma} min` : 'Pendiente', `${promedioTiempo(preTPRD)} min`, '', '');
  addRow('TPRD PROMEDIO GENERAL PRE-TEST:', `${promedioTiempo(preTPRD)} minutos`);
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
    addRow('Sin registros', '-', '-', '-', 0, 'Pendiente', 'Pendiente', 'Pendiente de trabajo de campo', '-');
  } else {
    post.forEach((c: RegistroTesis, idx: number) => {
      addRow(
        idx + 1,
        c.fecha,
        c.placa,
        c.marca_modelo,
        c.tiempo_diagnostico_minutos !== null && Number.isFinite(c.tiempo_diagnostico_minutos) && c.tiempo_diagnostico_minutos > 0 ? 1 : 0,
        c.tiempo_diagnostico_minutos !== null && Number.isFinite(c.tiempo_diagnostico_minutos) && c.tiempo_diagnostico_minutos > 0 ? c.tiempo_diagnostico_minutos : null,
        c.tiempo_diagnostico_minutos !== null && Number.isFinite(c.tiempo_diagnostico_minutos) && c.tiempo_diagnostico_minutos > 0 ? c.tiempo_diagnostico_minutos : null,
        c.sintoma,
        c.falla_real
      );
    });
  }
  addRow('TOTALES POST-TEST', '', '', '', postMetricas.tiemposEvaluados,
    postMetricas.tiemposEvaluados ? `${postTiempoSuma} min` : 'Pendiente', `${promedioTiempo(postTPRD)} min`, '', '');
  addRow('TPRD PROMEDIO GENERAL POST-TEST:', `${promedioTiempo(postTPRD)} minutos`);
  addRow('');

  // 8. Resumen Comparativo Pre vs Post y Estado Metodológico
  addRow('========================================================================================================');
  addRow('RESUMEN COMPARATIVO Y ESTADO METODOLÓGICO DE HIPÓTESIS');
  addRow('Indicador / Ficha', 'Pre-test', 'Post-test', 'Diferencia (Post - Pre)', 'Estado Metodológico');
  addRow(
    'Ficha 1 · Predicción de fallas vehiculares (PPCF)',
    porcentaje(prePPCF),
    porcentaje(postPPCF),
    prePPCF !== null && postPPCF !== null ? `${(postPPCF - prePPCF).toFixed(2)} pp` : 'Pendiente',
    'Contraste de hipótesis y prueba inferencial pendientes de completar el trabajo de campo de 60 registros reales y validación con el asesor estadístico (evaluar si corresponde prueba pareada o de muestras independientes).'
  );
  addRow(
    'Ficha 2 · Registros diagnósticos completos (PRDC)',
    porcentaje(prePRDC),
    porcentaje(postPRDC),
    prePRDC !== null && postPRDC !== null ? `${(postPRDC - prePRDC).toFixed(2)} pp` : 'Pendiente',
    'Contraste de hipótesis y prueba inferencial pendientes de completar el trabajo de campo de 60 registros reales y validación con el asesor estadístico (evaluar si corresponde prueba pareada o de muestras independientes).'
  );
  addRow(
    'Ficha 3 · Tiempo promedio de respuesta (TPRD)',
    preTPRD !== null ? `${preTPRD.toFixed(2)} min` : 'Pendiente',
    postTPRD !== null ? `${postTPRD.toFixed(2)} min` : 'Pendiente',
    preTPRD !== null && postTPRD !== null ? `${(preTPRD - postTPRD).toFixed(2)} min` : 'Pendiente',
    'Contraste de hipótesis y prueba inferencial pendientes de completar el trabajo de campo de 60 registros reales y validación con el asesor estadístico (evaluar si corresponde prueba pareada o de muestras independientes).'
  );

  // Descarga con UTF-8 BOM para compatibilidad total con Excel en español
  const blob = new Blob(['\uFEFF' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  const prefijo = modo === 'demostracion' ? 'DEMO_SINTETICO_Fichas_Tesis_UCV_' : 'OFICIAL_Fichas_Tesis_UCV_Anexo2_';
  link.setAttribute('href', url);
  link.setAttribute('download', `${prefijo}${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
