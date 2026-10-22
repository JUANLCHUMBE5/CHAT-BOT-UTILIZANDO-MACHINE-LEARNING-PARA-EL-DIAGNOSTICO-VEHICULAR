import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import ts from 'typescript';
import { presentarConfianzaDiagnostico } from '../../src/utils/prediccionPresentation.ts';

const inherited = { confianza: 99, predicciones_ml: [] };
assert.equal(presentarConfianzaDiagnostico(inherited).etiqueta, 'Sin estimación');
const prediction = { orden: 1, falla: 'A', probabilidad: 99, statistical_probability: .42 };
assert.equal(presentarConfianzaDiagnostico({ predicciones_ml: [prediction] }).porcentaje, 42);
const detail = { estado: 'sin_estimacion', valor_svm: null, valor_operativo: .99 };
assert.equal(presentarConfianzaDiagnostico({ predicciones_ml: [prediction], confianza_detalle: detail }).porcentaje, null);
for (const value of [NaN, Infinity, -1, 1.1]) {
  assert.equal(presentarConfianzaDiagnostico({ confianza_detalle: { ...detail, estado: 'estimada_svm', valor_svm: value } }).porcentaje, null);
}
assert.equal(presentarConfianzaDiagnostico({ confianza_detalle: { ...detail, estado: 'estimada_svm', valor_svm: 0 } }).porcentaje, 0);
assert.equal(presentarConfianzaDiagnostico({ predicciones_ml: [{ ...prediction, prediction_source: 'REGLA' }] }).porcentaje, null);

const url = new URL('../../src/components/common/ConfianzaDiagnostico.tsx', import.meta.url);
const compiled = ts.transpileModule(readFileSync(url, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
}).outputText;
const component = { exports: {} };
const require = createRequire(url);
new Function('require', 'module', 'exports', compiled)(
  (id) => id.includes('prediccionPresentation') ? { presentarConfianzaDiagnostico } : require(id),
  component, component.exports,
);
const render = (diagnostico) => renderToStaticMarkup(React.createElement(component.exports.ConfianzaDiagnostico, { diagnostico }));
assert.ok(render(inherited).includes('Sin estimación'));
assert.ok(!render(inherited).includes('99%'));
assert.ok(render({ predicciones_ml: [prediction] }).includes('Est. SVM 42.0%'));
console.log('Confianza general: contrato y render del componente compartido aprobados.');
