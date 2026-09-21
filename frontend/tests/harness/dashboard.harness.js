import assert from 'node:assert/strict';
import {
  obtenerPeriodosComparativa,
  calcularVariacion,
  calcularVariacionPendientes,
} from '../../src/utils/dashboardComparador.ts';

console.log('=== TEST SUITE: Dashboard Operativo Comparativas & Periodos ===');

// 1. Preset 'hoy'
const refHoy = new Date('2026-09-20T17:00:00Z'); // 12:00 en Lima
const p_hoy = obtenerPeriodosComparativa('hoy', undefined, undefined, refHoy);
assert.equal(p_hoy.actual.inicio, '2026-09-20');
assert.equal(p_hoy.actual.fin, '2026-09-20');
assert.equal(p_hoy.anterior?.inicio, '2026-09-19');
assert.equal(p_hoy.anterior?.fin, '2026-09-19');
assert.equal(p_hoy.etiquetaActual, 'Hoy');
assert.equal(p_hoy.etiquetaAnterior, 'Ayer');
console.log('✔ Preset Hoy verificado');

// 2. Preset '7dias'
const p_7dias = obtenerPeriodosComparativa('7dias', undefined, undefined, refHoy);
assert.equal(p_7dias.actual.inicio, '2026-09-14');
assert.equal(p_7dias.actual.fin, '2026-09-20');
assert.equal(p_7dias.anterior?.inicio, '2026-09-07');
assert.equal(p_7dias.anterior?.fin, '2026-09-13');
console.log('✔ Preset 7 días verificado');

// 3. Preset 'esteMes'
const p_esteMes = obtenerPeriodosComparativa('esteMes', undefined, undefined, refHoy);
assert.equal(p_esteMes.actual.inicio, '2026-09-01');
assert.equal(p_esteMes.actual.fin, '2026-09-20');
assert.equal(p_esteMes.anterior?.inicio, '2026-08-01');
assert.equal(p_esteMes.anterior?.fin, '2026-08-20');
console.log('✔ Preset Este mes verificado');

// 4. Preset 'custom'
const p_custom = obtenerPeriodosComparativa('custom', '2026-09-10', '2026-09-15');
assert.equal(p_custom.actual.inicio, '2026-09-10');
assert.equal(p_custom.actual.fin, '2026-09-15');
// 6 días de duración -> anterior: 2026-09-04 a 2026-09-09
assert.equal(p_custom.anterior?.inicio, '2026-09-04');
assert.equal(p_custom.anterior?.fin, '2026-09-09');
console.log('✔ Preset Rango personalizado verificado');

// 5. Cálculo de Variaciones Estándar
const v_aumento = calcularVariacion(100, 80);
assert.equal(v_aumento.porcentaje, 25);
assert.equal(v_aumento.texto, '+25.0%');
assert.equal(v_aumento.positiva, true);

const v_descenso = calcularVariacion(60, 80);
assert.equal(v_descenso.porcentaje, -25);
assert.equal(v_descenso.texto, '-25.0%');
assert.equal(v_descenso.positiva, false);

const v_sin_anterior = calcularVariacion(50, null);
assert.equal(v_sin_anterior.texto, 'Sin período anterior');
assert.equal(v_sin_anterior.neutra, true);

const v_cero_a_positivo = calcularVariacion(10, 0);
assert.equal(v_cero_a_positivo.texto, '+10 nuevos');
assert.equal(v_cero_a_positivo.positiva, true);
console.log('✔ Variaciones estándar verificadas');

// 6. Variación Semántica para Pendientes (menos es mejor)
const v_pend_baja = calcularVariacionPendientes(5, 10);
assert.equal(v_pend_baja.positiva, true); // positivo porque se redujo backlog

const v_pend_sube = calcularVariacionPendientes(15, 10);
assert.equal(v_pend_sube.positiva, false); // advertencia porque subió backlog
console.log('✔ Variaciones semánticas de pendientes verificadas');

console.log('🎉 TODOS LOS TESTS DE COMPARATIVAS DEL DASHBOARD PASARON!');
