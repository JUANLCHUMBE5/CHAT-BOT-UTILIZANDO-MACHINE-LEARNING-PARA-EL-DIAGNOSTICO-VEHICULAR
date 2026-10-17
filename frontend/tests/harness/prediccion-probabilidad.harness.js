import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import ts from 'typescript';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { presentarPrediccion } from '../../src/utils/prediccionPresentation.ts';

const base = { orden: 1, falla: 'Hipótesis', probabilidad: 99 };
assert.equal(presentarPrediccion({ ...base, statistical_probability: null }).probabilidadTexto,
  'Sin probabilidad estadística');
assert.equal(presentarPrediccion(base).porcentaje, null);
assert.equal(presentarPrediccion({ ...base, statistical_probability: 0 }).porcentaje, 0);
assert.equal(presentarPrediccion({ ...base, statistical_probability: 0.42 }).probabilidadTexto,
  'Probabilidad SVM: 42.0 %');
for (const value of [NaN, Infinity, -1, 2]) {
  assert.equal(presentarPrediccion({ ...base, statistical_probability: value }).porcentaje, null);
}
assert.equal(presentarPrediccion({ ...base, prediction_source: 'REGLA',
  statistical_probability: 0.9 }).porcentaje, null);
assert.equal(presentarPrediccion({ ...base, operational_score: 0.85 }).scoreTexto,
  'Score operativo: 0.850 (no es probabilidad)');

// Render the actual TSX component, without installing a second test framework.
const url = new URL('../../src/components/views/diagnosticos/modal/DiagnosticoMlSection.tsx', import.meta.url);
const compiled = ts.transpileModule(readFileSync(url, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
}).outputText;
const componentModule = { exports: {} };
const require = createRequire(url);
new Function('require', 'module', 'exports', compiled)(
  (id) => id.includes('prediccionPresentation') ? { presentarPrediccion } : require(id),
  componentModule, componentModule.exports,
);
const Component = componentModule.exports.DiagnosticoMlSection;
const render = (prediction) => renderToStaticMarkup(React.createElement(Component, {
  diagnostico: { predicciones_ml: [prediction], version_modelo_ml: 'C1' },
}));
const absent = render({ ...base, statistical_probability: null, operational_score: 0.85 });
assert.ok(absent.includes('Sin probabilidad estadística'));
assert.ok(absent.includes('Score operativo: 0.850 (no es probabilidad)'));
assert.ok(!absent.includes('0%') && !absent.includes('99%'));
assert.ok(!absent.includes('transition:width'));
const positive = render({ ...base, statistical_probability: 0.42, prediction_source: 'SVM_DTC' });
assert.ok(positive.includes('Probabilidad SVM: 42.0 %'));
assert.ok(positive.includes('width:42%'));
console.log('Presentación de probabilidades: contratos y render TSX aprobados.');
