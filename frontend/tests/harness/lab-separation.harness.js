import assert from 'node:assert/strict';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const text = (p) => readFileSync(p, 'utf8');
for (const path of ['src/App.tsx', 'src/components/layout/Sidebar.tsx', 'src/utils/routing.ts', 'src/services/api.ts']) {
  assert.doesNotMatch(text(path), /laboratorio/i, `${path} debe permanecer ajeno al laboratorio`);
}
assert.match(text('src/laboratorio-local.tsx'), /LaboratorioView/);
assert.match(text('vite.laboratorio.config.ts'), /127\.0\.0\.1/);
assert.match(text('vite.laboratorio.config.ts'), /dist-laboratorio/);
assert.match(text('vite.laboratorio.config.ts'), /VITE_API_BASE_URL.*JSON\.stringify\('\/api\/v1'\)/);
function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? walk(path) : [path];
  });
}
const files = walk('dist');
assert.ok(files.some((p) => p.endsWith('index.html')));
for (const file of files) {
  assert.doesNotMatch(file, /laboratorio/i);
  if (/\.(js|html)$/.test(file)) {
    assert.doesNotMatch(text(file), /laboratorio\/mensaje|Laboratorio de Pruebas|lab_replay_/);
  }
}
console.log('Separación: build público sin navegación, endpoints ni componentes del laboratorio; entrada local preservada.');
