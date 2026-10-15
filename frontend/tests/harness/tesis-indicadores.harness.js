import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { calcularIndicadoresTesisFase, validarCasosParaExportacionOficial } from '../../src/utils/tesisIndicadores.ts';

const resultado = calcularIndicadoresTesisFase([
  { chatbot_prediccion: 'Hipótesis', falla_real: 'Confirmada', prediccion_correcta: 1, campos_completos: 1, tiempo_diagnostico_minutos: 20 },
  { chatbot_prediccion: 'Hipótesis', falla_real: 'Confirmada', prediccion_correcta: 0, campos_completos: 0, tiempo_diagnostico_minutos: null },
  { chatbot_prediccion: null, falla_real: 'Confirmada', prediccion_correcta: 1, campos_completos: null, tiempo_diagnostico_minutos: 0 },
]);

assert.equal(resultado.prediccionesEvaluadas, 2);
assert.equal(resultado.aciertos, 1);
assert.equal(resultado.ppcf, 50);
assert.equal(resultado.registrosEvaluados, 2);
assert.equal(resultado.registrosCompletos, 1);
assert.equal(resultado.prdc, 50);
assert.equal(resultado.tiemposEvaluados, 1);
assert.equal(resultado.tiempoSuma, 20);
assert.equal(resultado.tprd, 20);

const vacio = calcularIndicadoresTesisFase([
  { chatbot_prediccion: null, falla_real: null, prediccion_correcta: null, campos_completos: null, tiempo_diagnostico_minutos: null },
]);
assert.equal(vacio.ppcf, null);
assert.equal(vacio.prdc, null);
assert.equal(vacio.tprd, null);
assert.equal(vacio.tiemposEvaluados, 0);

const trazabilidadCompleta = {
  fase: 'Post-test', tipo_registro: 'THESIS_POSTTEST', estado_registro: 'verificado',
  falla_real: 'Falla confirmada', metodo_confirmacion: 'Inspección física', evidencia_ref: 'OT-001',
  validado_por_id: 'mecanico-1', fecha_validacion: '2026-10-14T10:00:00Z',
};
assert.equal(validarCasosParaExportacionOficial([trazabilidadCompleta]), true);
assert.equal(validarCasosParaExportacionOficial([]), false);
assert.equal(validarCasosParaExportacionOficial([{ ...trazabilidadCompleta, evidencia_ref: ' ' }]), false);
assert.equal(validarCasosParaExportacionOficial([{ ...trazabilidadCompleta, tipo_registro: 'DEVELOPMENT' }]), false);
const exportador = readFileSync(new URL('../../src/components/views/proyecto/tesis/exportarFichasTesis.ts', import.meta.url), 'utf8');
assert.match(exportador, /validarCasosParaExportacionOficial\(casos\)/);
assert.match(exportador, /DEMO_SINTETICO_Fichas_Tesis_UCV_/);

console.log('Indicadores de tesis: denominadores observados y faltantes pendientes verificados.');
