import assert from 'node:assert/strict';
import { periodoDias, limitesDiagnosticos } from '../../src/utils/periodo.ts';

assert.deepEqual(periodoDias(7, new Date('2026-09-04T15:00:00Z')), {
  fecha_desde: '2026-08-29', fecha_hasta: '2026-09-04',
});
assert.deepEqual(periodoDias(14, new Date('2026-09-04T15:00:00Z')), {
  fecha_desde: '2026-08-22', fecha_hasta: '2026-09-04',
});
assert.equal(periodoDias(7, new Date('2026-09-04T02:00:00Z')).fecha_hasta, '2026-09-03');
assert.deepEqual(limitesDiagnosticos({ fecha_desde: '2026-08-29', fecha_hasta: '2026-09-04' }), {
  fecha_desde: '2026-08-29T00:00:00-05:00', fecha_hasta: '2026-09-05T05:00:00.000Z',
});
assert.deepEqual(limitesDiagnosticos({}), { fecha_desde: undefined, fecha_hasta: undefined });
console.log('Períodos de 7/14 días y límites inclusivos en Lima: correctos.');
