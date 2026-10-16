import assert from 'node:assert/strict';
import {payload, summarize} from '../../lab/client.js';
assert.deepEqual(payload('yaris', '  P0301  '), {scenario:'yaris',message:'P0301'});
assert.deepEqual(payload('sentra', '0.12 mm'), {scenario:'sentra',message:'0.12 mm'});
for (const value of ['', ' '.repeat(10), 'x'.repeat(4001)]) assert.throws(() => payload('yaris',value));
assert.throws(() => payload('production', 'hola'));
assert.match(summarize({passed:false, failure:'<script>alert(1)</script>'}), /"passed": false/);
console.log('Laboratorio: 7 contratos frontend aprobados; no sustituye pruebas de navegador.');
