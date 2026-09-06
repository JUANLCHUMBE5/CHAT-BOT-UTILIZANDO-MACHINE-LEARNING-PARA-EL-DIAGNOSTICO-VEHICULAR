import { Card } from '../../common/Card';
import type { MetricasValidacionDTO } from '../../../types/api';

export function ValidacionMetricasCards({ metricas }: { metricas: MetricasValidacionDTO | null }) {
  if (!metricas) return null;
  const pre = metricas.casos_pretest;
  const post = metricas.casos_posttest;
  const filas = [
    ['Ficha 1 · Predicciones correctas (PPCF)', metricas.tasa_acierto_pretest_porcentaje, metricas.tasa_acierto_posttest_porcentaje, '%'],
    ['Ficha 2 · Registros completos (PRDC)', metricas.registros_completos_pretest_porcentaje, metricas.registros_completos_posttest_porcentaje, '%'],
    ['Ficha 3 · Tiempo diagnóstico (TPRD)', metricas.tiempo_promedio_pretest_min, metricas.tiempo_promedio_posttest_min, 'min'],
  ] as const;
  return <Card>
    <h3 style={{ marginTop: 0 }}>Comparación del período</h3>
    <p style={{ fontSize: 12 }}>Preexperimental · {pre} registros pre-test y {post} post-test.</p>
    <div style={{ overflowX: 'auto' }}>
      <table className="tesis-comparacion">
        <thead><tr><th>Ficha</th><th>Pre-test</th><th>Post-test</th><th>Cambio post − pre</th></tr></thead>
        <tbody>{filas.map(([titulo, antes, despues, unidad]) => <tr key={titulo}>
          <th scope="row">{titulo}</th>
          <td data-label="Pre-test">{pre ? `${antes.toFixed(1)} ${unidad}` : 'Sin datos'}</td>
          <td data-label="Post-test">{post ? `${despues.toFixed(1)} ${unidad}` : 'Sin datos'}</td>
          <td data-label="Cambio post − pre">{pre && post ? `${despues - antes > 0 ? '+' : ''}${(despues - antes).toFixed(1)} ${unidad === '%' ? 'puntos porcentuales' : 'min'}` : 'Sin comparación'}</td>
        </tr>)}</tbody>
      </table>
    </div>
    <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
      Incluye todos los registros del período, no solo esta página. Pilotos excluidos de la comparación.
    </p>
  </Card>;
}
