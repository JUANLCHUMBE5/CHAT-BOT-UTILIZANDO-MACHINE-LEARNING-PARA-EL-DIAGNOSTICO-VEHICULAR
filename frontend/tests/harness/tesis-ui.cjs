// Prueba de interfaz con API simulada. No inicia sesión ni escribe en el taller real.
const { chromium } = require(process.env.CARBOT_PLAYWRIGHT || 'playwright');
const assert = require('node:assert/strict');
const { mkdtemp } = require('node:fs/promises');
const { tmpdir } = require('node:os');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const capturas = await mkdtemp(path.join(tmpdir(), 'carbot-tesis-qa-'));
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  const errores = [];
  const requests = [];
  page.on('pageerror', e => errores.push(e.message));
  await context.addInitScript(() => localStorage.setItem('carbot_session', JSON.stringify({
    username: 'qa', nombre: 'Evaluador de prueba', rol: 'administrador', taller: 'Taller de prueba',
  })));
  const casos = Array.from({ length: 24 }, (_, i) => ({
    item: i + 1, fecha: '2026-09-04', fase: i < 12 ? 'Pre-test' : 'Post-test',
    placa_enmascarada: 'ABC-***', placa_hash: 'a'.repeat(64), marca_modelo: 'Vehículo de prueba',
    sintoma: 'Vibraciones al manejar', chatbot_prediccion: 'Desbalance de ruedas', falla_real: 'Desbalance de ruedas',
    campos_completos: i % 2, prediccion_correcta: i % 2, tiempo_diagnostico_minutos: 20,
    metodo_confirmacion: 'Inspección en taller', evidencia_ref: 'Caso QA',
  }));
  const metricas = { total_casos: 24, total_aciertos: 12, total_desaciertos: 12,
    casos_pretest: 12, casos_posttest: 12, tasa_acierto_pretest_porcentaje: 60, tasa_acierto_posttest_porcentaje: 50,
    registros_completos_pretest_porcentaje: 40, registros_completos_posttest_porcentaje: 50,
    tiempo_promedio_pretest_min: 20, tiempo_promedio_posttest_min: 30, reduccion_tiempo_porcentaje: -50,
    distribucion_marcas: [], top_fallas_reales: [] };
  await page.route('**/api/v1/**', async route => {
    const url = new URL(route.request().url()); requests.push(url);
    let json = [];
    if (url.pathname.endsWith('/validacion-taller/metricas')) json = metricas;
    else if (url.pathname.endsWith('/validacion-taller')) {
      const skip = Number(url.searchParams.get('skip') || 0);
      json = { total: 24, skip, limit: 10, casos: casos.slice(skip, skip + 10) };
    } else if (url.pathname.endsWith('/metricas/resumen')) json = {
      diagnosticos_realizados: 24, diagnosticos_mes: 24, diagnosticos_pendientes: 5, porcentaje_confirmados: 50,
      tiempo_promedio_ms: 200, actividad_diaria: [], fallas_frecuentes: [], distribucion_modos: [],
    };
    else if (url.pathname.endsWith('/metricas/colas')) json = { total: 0, pendientes: 0, procesando: 0, fallidos: 0 };
    await route.fulfill({ json, headers: { 'X-Total-Count': '0', 'Access-Control-Expose-Headers': 'X-Total-Count' } });
  });
  await page.route('**/health/ready', route => route.fulfill({ json: { status: 'ready' } }));
  try {
    await page.goto(process.env.CARBOT_QA_URL || 'http://127.0.0.1:5175/proyecto');
    await page.getByText('Ver registro #1', { exact: true }).waitFor();
    assert.equal(await page.getByRole('button', { name: /Ver registro #/ }).count(), 10);
    assert(await page.getByText('-10.0 puntos porcentuales', { exact: true }).isVisible());
    await page.getByRole('button', { name: 'Página siguiente' }).click();
    await page.getByText('Ver registro #11', { exact: true }).waitFor();
    assert(requests.some(u => u.searchParams.get('skip') === '10' && u.searchParams.get('limit') === '10'));
    await page.getByText('Ver registro #11', { exact: true }).click();
    await page.getByText('Hipótesis del mecánico', { exact: true }).waitFor();
    await page.keyboard.press('Escape');
    await page.getByRole('button', { name: 'Últimos 14 días', exact: true }).click();
    await page.getByText('Ver registro #1', { exact: true }).waitFor();
    assert(requests.some(u => u.pathname.endsWith('/validacion-taller/metricas') && u.searchParams.has('fecha_desde')));
    await page.screenshot({ path: path.join(capturas, 'tesis-desktop.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(capturas, 'tesis-mobile.png'), fullPage: true });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), 'La página no debe desbordar el móvil');
    await page.getByRole('button', { name: 'Consultas del bot', exact: true }).click();
    await page.getByText('Resumen de consultas del período').waitFor();
    await page.getByRole('button', { name: 'Todo', exact: true }).click();
    await page.waitForTimeout(600);
    assert(requests.some(u => u.pathname.endsWith('/metricas/resumen') && u.searchParams.get('todo') === 'true' && !u.searchParams.has('fecha_inicio')));
    assert.deepEqual(errores, []);
    console.log('Interfaz escritorio/móvil, detalle, paginación y fechas: correctos (API simulada).');
  } finally {
    await browser.close();
    console.log(`Capturas de revisión: ${capturas}`);
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
