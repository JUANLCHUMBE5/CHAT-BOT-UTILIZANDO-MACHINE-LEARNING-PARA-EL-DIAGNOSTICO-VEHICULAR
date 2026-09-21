import { useState } from 'react';
import { Card } from '../../common/Card';
import type { MetricasValidacionDTO } from '../../../types/api';
import { CheckCircle2 } from 'lucide-react';

export function ValidacionMetricasCards({ metricas }: { metricas: MetricasValidacionDTO | null }) {
  const [modoDemo, setModoDemo] = useState(false);

  // Muestra real procedente de PostgreSQL
  const preReal = metricas?.casos_pretest ?? 0;
  const postReal = metricas?.casos_posttest ?? 0;
  const totalReales = preReal + postReal;
  const pilotoReal = metricas?.casos_piloto ?? 0;

  // Valores de maqueta / demo sintética (estrictamente aislados)
  const filasDemo = [
    {
      titulo: 'Ficha 1 · Predicciones correctas (PPCF)',
      antes: 56.7,
      despues: 93.3,
      unidad: '%',
      esMenorMejor: false,
    },
    {
      titulo: 'Ficha 2 · Registros completos (PRDC)',
      antes: 40.0,
      despues: 96.7,
      unidad: '%',
      esMenorMejor: false,
    },
    {
      titulo: 'Ficha 3 · Tiempo diagnóstico (TPRD)',
      antes: 38.5,
      despues: 11.2,
      unidad: 'min',
      esMenorMejor: true,
    },
  ];

  const filasReales = [
    {
      titulo: 'Ficha 1 · Predicciones correctas (PPCF)',
      antes: metricas?.tasa_acierto_pretest_porcentaje ?? 0,
      despues: metricas?.tasa_acierto_posttest_porcentaje ?? 0,
      unidad: '%',
      esMenorMejor: false,
    },
    {
      titulo: 'Ficha 2 · Registros completos (PRDC)',
      antes: metricas?.registros_completos_pretest_porcentaje ?? 0,
      despues: metricas?.registros_completos_posttest_porcentaje ?? 0,
      unidad: '%',
      esMenorMejor: false,
    },
    {
      titulo: 'Ficha 3 · Tiempo diagnóstico (TPRD)',
      antes: metricas?.tiempo_promedio_pretest_min ?? 0,
      despues: metricas?.tiempo_promedio_posttest_min ?? 0,
      unidad: 'min',
      esMenorMejor: true,
    },
  ];

  const pre = modoDemo ? 30 : preReal;
  const post = modoDemo ? 30 : postReal;
  const filas = modoDemo ? filasDemo : filasReales;

  return (
    <Card>
      {/* Banner Metodológico Compacto */}
      <div
        style={{
          padding: '8px 14px',
          borderRadius: '8px',
          marginBottom: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          backgroundColor: '#f8fafc',
          border: '1px solid #e2e8f0',
        }}
      >
        <CheckCircle2 size={16} style={{ color: '#059669', flexShrink: 0 }} />
        <div style={{ fontSize: '12px', color: '#334155' }}>
          <strong>Trabajo de campo pendiente.</strong> Los resultados pretest y postest se calcularán exclusivamente con registros reales recopilados y verificados durante la aplicación de los instrumentos. <strong>Avance actual: {totalReales} de 60 registros.</strong>
        </div>
      </div>

      {/* Contadores Separados: Piloto vs Muestra Oficial */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '10px',
          marginBottom: '14px',
        }}
      >
        <div style={{ backgroundColor: '#fffbeb', border: '1px solid #fde68a', borderRadius: '8px', padding: '10px 12px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#92400e', textTransform: 'uppercase' }}>
            Piloto
          </div>
          <div style={{ fontSize: '18px', fontWeight: 800, color: '#b45309', marginTop: '2px' }}>
            {pilotoReal} registros
          </div>
          <div style={{ fontSize: '10.5px', color: '#78350f', marginTop: '2px' }}>
            Prueba independiente
          </div>
        </div>

        <div style={{ backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', padding: '10px 12px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#166534', textTransform: 'uppercase' }}>
            Oficial: Pre-test
          </div>
          <div style={{ fontSize: '18px', fontWeight: 800, color: '#15803d', marginTop: '2px' }}>
            {preReal} / 30
          </div>
          <div style={{ fontSize: '10.5px', color: '#166534', marginTop: '2px' }}>
            Diagnóstico Tradicional
          </div>
        </div>

        <div style={{ backgroundColor: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '8px', padding: '10px 12px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#1e40af', textTransform: 'uppercase' }}>
            Oficial: Post-test
          </div>
          <div style={{ fontSize: '18px', fontWeight: 800, color: '#1d4ed8', marginTop: '2px' }}>
            {postReal} / 30
          </div>
          <div style={{ fontSize: '10.5px', color: '#1e40af', marginTop: '2px' }}>
            Asistido por CarBot ML
          </div>
        </div>

        <div style={{ backgroundColor: '#faf5ff', border: '1px solid #e9d5ff', borderRadius: '8px', padding: '10px 12px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#6b21a8', textTransform: 'uppercase' }}>
            Muestra Oficial Total
          </div>
          <div style={{ fontSize: '18px', fontWeight: 800, color: '#7e22ce', marginTop: '2px' }}>
            {totalReales} / 60
          </div>
          <div style={{ fontSize: '10.5px', color: '#6b21a8', marginTop: '2px' }}>
            Meta de Investigación
          </div>
        </div>
      </div>

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px',
          marginBottom: '12px',
        }}
      >
        <div>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: 'var(--text-main)' }}>
            Comparación de Indicadores de Tesis
          </h3>
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Muestra evaluada:{' '}
            <strong style={{ color: 'var(--text-main)' }}>{pre}</strong> pre-test ·{' '}
            <strong style={{ color: 'var(--primary)' }}>{post}</strong> post-test{' '}
            {!modoDemo && (
              <span style={{ color: '#059669', fontWeight: 600 }}>(Registros reales PostgreSQL)</span>
            )}
          </span>
        </div>

        {/* Selector de Modo de Muestra: Real vs Demostración */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            backgroundColor: '#f1f5f9',
            padding: '2px',
            borderRadius: '6px',
            gap: '2px',
          }}
        >
          <button
            type="button"
            onClick={() => setModoDemo(false)}
            style={{
              padding: '5px 10px',
              fontSize: '11px',
              fontWeight: 700,
              borderRadius: '5px',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: !modoDemo ? '#ffffff' : 'transparent',
              color: !modoDemo ? '#059669' : 'var(--text-muted)',
              boxShadow: !modoDemo ? '0 1px 2px rgba(0,0,0,0.06)' : 'none',
            }}
          >
            Registros Reales ({totalReales}/60)
          </button>
          <button
            type="button"
            onClick={() => setModoDemo(true)}
            style={{
              padding: '5px 10px',
              fontSize: '11px',
              fontWeight: 700,
              borderRadius: '5px',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: modoDemo ? '#ffffff' : 'transparent',
              color: modoDemo ? '#d97706' : 'var(--text-muted)',
              boxShadow: modoDemo ? '0 1px 2px rgba(0,0,0,0.06)' : 'none',
            }}
          >
            Modo Demo (Sintético)
          </button>
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table className="tesis-comparacion">
          <thead>
            <tr
              style={{
                backgroundColor: 'var(--bg-subtle)',
                borderBottom: '1px solid var(--border-color)',
                fontSize: '11px',
                fontWeight: 700,
                color: 'var(--text-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              <th style={{ padding: '10px 14px' }}>Indicador / Ficha</th>
              <th style={{ padding: '10px 14px' }}>Pre-test (Manual)</th>
              <th style={{ padding: '10px 14px' }}>Post-test (CarBot)</th>
              <th style={{ padding: '10px 14px' }}>Cambio post − pre</th>
            </tr>
          </thead>
          <tbody>
            {filas.map(({ titulo, antes, despues, unidad, esMenorMejor }) => {
              const tieneDatosPre = pre > 0;
              const tieneDatosPost = post > 0;
              const delta = despues - antes;
              const mejora = esMenorMejor ? delta < 0 : delta > 0;
              const deltaTexto = delta > 0 ? `+${delta.toFixed(1)}` : delta.toFixed(1);
              const unidadTexto = unidad === '%' ? 'puntos porcentuales' : 'min';

              return (
                <tr key={titulo}>
                  <th scope="row" style={{ fontWeight: 600, color: 'var(--text-main)', padding: '12px 14px' }}>
                    {titulo}
                  </th>
                  <td data-label="Pre-test (Manual)" style={{ padding: '12px 14px' }}>
                    {tieneDatosPre ? `${antes.toFixed(1)} ${unidad}` : 'Pendiente de datos'}
                  </td>
                  <td
                    data-label="Post-test (CarBot)"
                    style={{ padding: '12px 14px', fontWeight: 700, color: 'var(--primary)' }}
                  >
                    {tieneDatosPost ? `${despues.toFixed(1)} ${unidad}` : 'Pendiente de datos'}
                  </td>
                  <td data-label="Cambio post − pre" style={{ padding: '12px 14px' }}>
                    {tieneDatosPre && tieneDatosPost ? (
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          fontWeight: 600,
                          padding: '3px 8px',
                          borderRadius: '4px',
                          fontSize: '12px',
                          backgroundColor: mejora ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.1)',
                          color: mejora ? '#059669' : '#dc2626',
                        }}
                      >
                        {deltaTexto} {unidadTexto}
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)', fontSize: '13px', fontWeight: 600 }}>
                        —
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
