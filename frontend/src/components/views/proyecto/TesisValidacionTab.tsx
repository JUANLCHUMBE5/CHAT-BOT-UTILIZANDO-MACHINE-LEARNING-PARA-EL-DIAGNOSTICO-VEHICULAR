import React, { useState } from 'react';
import {
  GraduationCap,
  Download,
  FlaskConical,
} from 'lucide-react';
import { Card } from '../../common/Card';
import { REGISTROS_TESIS_60, METADATA_TESIS } from '../../../data/fichasTesisData';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';
import { ValidacionTallerView } from '../ValidacionTallerView';

export const TesisValidacionTab: React.FC = () => {
  // Pestaña interna: 'fichas' (60 casos oficiales de la tesis) vs 'tracker_vivo' (registro en vivo del taller)
  const [seccionActiva, setSeccionActiva] = useState<'fichas' | 'tracker_vivo'>('fichas');

  // Pestaña de Ficha seleccionada: 'ficha1' | 'ficha2' | 'ficha3'
  const [fichaActiva, setFichaActiva] = useState<'ficha1' | 'ficha2' | 'ficha3'>('ficha1');
  // Fase seleccionada: 'post' | 'pre' | 'contraste'
  const [faseActiva, setFaseActiva] = useState<'post' | 'pre' | 'contraste'>('post');

  const preCasos = REGISTROS_TESIS_60.filter((c) => c.fase === 'Pre-test');
  const postCasos = REGISTROS_TESIS_60.filter((c) => c.fase === 'Post-test');
  const casosVisibles = faseActiva === 'pre' ? preCasos : postCasos;

  // ================= CÁLCULOS ESTADÍSTICOS EN VIVO =================
  // Ficha 1: PPCF
  const prePPCFCount = preCasos.filter((c) => c.prediccion_correcta === 1).length;
  const postPPCFCount = postCasos.filter((c) => c.prediccion_correcta === 1).length;
  const prePPCFPct = (prePPCFCount / preCasos.length) * 100;
  const postPPCFPct = (postPPCFCount / postCasos.length) * 100;

  // Ficha 2: PRDC (8 campos completos)
  const prePRDCCount = preCasos.filter((c) => c.campos_completos === 1).length;
  const postPRDCCount = postCasos.filter((c) => c.campos_completos === 1).length;
  const prePRDCPct = (prePRDCCount / preCasos.length) * 100;
  const postPRDCPct = (postPRDCCount / postCasos.length) * 100;

  // Ficha 3: TPRD (Tiempos en minutos)
  const preTPRDSuma = preCasos.reduce((acc, c) => acc + c.tiempo_diagnostico_minutos, 0);
  const postTPRDSuma = postCasos.reduce((acc, c) => acc + c.tiempo_diagnostico_minutos, 0);
  const preTPRDProm = preTPRDSuma / preCasos.length;
  const postTPRDProm = postTPRDSuma / postCasos.length;

  // Metadata de la Ficha seleccionada
  const infoFicha = {
    ficha1: {
      numero: 'Ficha de registro: Predicción de fallas vehiculares',
      codigo: 'Anexo 2 - Ficha 1',
      dimension: 'Predicción de fallas vehiculares',
      indicador: 'Porcentaje de predicción correcta de fallas vehiculares (PPCF)',
      medida: 'Porcentaje (%)',
      formula: 'PPCF = (N.° de predicciones correctas / Total de predicciones realizadas) × 100',
      preValor: `${prePPCFPct.toFixed(2)}%`,
      postValor: `${postPPCFPct.toFixed(2)}%`,
      preDetalle: `${prePPCFCount} de ${preCasos.length} predicciones correctas`,
      postDetalle: `${postPPCFCount} de ${postCasos.length} predicciones correctas`,
      mejora: `+${(postPPCFPct - prePPCFPct).toFixed(2)}% de incremento de exactitud`,
      hipotesis: 'HE1: El chatbot con ML mejora significativamente la predicción de fallas vehiculares (p < 0.001)',
      unidad: '%',
    },
    ficha2: {
      numero: 'Ficha de registro: Control de información diagnóstica vehicular',
      codigo: 'Anexo 2 - Ficha 2',
      dimension: 'Control de información diagnóstica vehicular',
      indicador: 'Porcentaje de registros diagnósticos completos (PRDC)',
      medida: 'Porcentaje (%)',
      formula: 'PRDC = (RC: Registros con los 8 campos completos / TRE: Total de registros evaluados) × 100',
      preValor: `${prePRDCPct.toFixed(2)}%`,
      postValor: `${postPRDCPct.toFixed(2)}%`,
      preDetalle: `${prePRDCCount} de ${preCasos.length} con 8 campos completos`,
      postDetalle: `${postPRDCCount} de ${postCasos.length} con 8 campos completos`,
      mejora: `+${(postPRDCPct - prePRDCPct).toFixed(2)}% de incremento en calidad de datos`,
      hipotesis: 'HE2: El chatbot con ML mejora significativamente el control de información diagnóstica (p < 0.001)',
      unidad: '%',
    },
    ficha3: {
      numero: 'Ficha de registro: Eficiencia del diagnóstico vehicular',
      codigo: 'Anexo 2 - Ficha 3',
      dimension: 'Eficiencia del diagnóstico vehicular',
      indicador: 'Tiempo promedio de respuesta diagnóstica (TPRD)',
      medida: 'Minutos',
      formula: 'TPRD = Suma total de tiempos de respuesta diagnóstica / Total de diagnósticos evaluados',
      preValor: `${preTPRDProm.toFixed(2)} min`,
      postValor: `${postTPRDProm.toFixed(2)} min`,
      preDetalle: `Suma: ${preTPRDSuma.toFixed(1)} min en 30 atenciones`,
      postDetalle: `Suma: ${postTPRDSuma.toFixed(1)} min en 30 atenciones`,
      mejora: `-${(preTPRDProm - postTPRDProm).toFixed(2)} min/auto (${(((preTPRDProm - postTPRDProm) / preTPRDProm) * 100).toFixed(1)}% ahorro de tiempo)`,
      hipotesis: 'HE3: El chatbot con ML reduce significativamente el tiempo de atención del diagnóstico vehicular (p < 0.001)',
      unidad: ' min',
    },
  }[fichaActiva];

  // Datos para gráfico comparativo general de las 3 fichas
  const dataComparativaFichas = [
    { indicador: 'PPCF (% Acierto)', 'Pre-test (Manual)': Number(prePPCFPct.toFixed(1)), 'Post-test (CarBot AI)': Number(postPPCFPct.toFixed(1)) },
    { indicador: 'PRDC (% Campos 8/8)', 'Pre-test (Manual)': Number(prePRDCPct.toFixed(1)), 'Post-test (CarBot AI)': Number(postPRDCPct.toFixed(1)) },
    { indicador: 'TPRD (Minutos)', 'Pre-test (Manual)': Number(preTPRDProm.toFixed(1)), 'Post-test (CarBot AI)': Number(postTPRDProm.toFixed(1)) },
  ];

  const exportarCSV = () => {
    const headers = ['Item', 'Fase', 'Fecha', 'Placa', 'Marca_Modelo', 'Sintoma', 'Falla_Real', 'Chatbot_Prediccion', 'Campos_Completos', 'Tiempo_Minutos', 'Prediccion_Correcta'];
    const rows = REGISTROS_TESIS_60.map((r) => [
      r.item,
      r.fase,
      r.fecha,
      r.placa,
      `"${r.marca_modelo}"`,
      `"${r.sintoma}"`,
      `"${r.falla_real}"`,
      `"${r.chatbot_prediccion}"`,
      r.campos_completos,
      r.tiempo_diagnostico_minutos,
      r.prediccion_correcta,
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `Fichas_Tesis_UCV_CarBot_${fichaActiva}_N60.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Sub-navigation Switcher: Fichas Oficiales N=60 vs Tracker Experimental en Vivo */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '10px',
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            backgroundColor: '#f1f5f9',
            padding: '4px',
            borderRadius: '8px',
            gap: '4px',
          }}
        >
          <button
            type="button"
            onClick={() => setSeccionActiva('fichas')}
            style={{
              padding: '7px 14px',
              fontSize: '12px',
              fontWeight: 700,
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: seccionActiva === 'fichas' ? '#059669' : 'transparent',
              color: seccionActiva === 'fichas' ? '#ffffff' : 'var(--text-secondary)',
              boxShadow: seccionActiva === 'fichas' ? '0 1px 3px rgba(5,150,105,0.25)' : 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <GraduationCap size={15} />
            <span>Fichas de Tesis Oficiales (N=60)</span>
          </button>

          <button
            type="button"
            onClick={() => setSeccionActiva('tracker_vivo')}
            style={{
              padding: '7px 14px',
              fontSize: '12px',
              fontWeight: 700,
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: seccionActiva === 'tracker_vivo' ? 'var(--primary)' : 'transparent',
              color: seccionActiva === 'tracker_vivo' ? '#ffffff' : 'var(--text-secondary)',
              boxShadow: seccionActiva === 'tracker_vivo' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <FlaskConical size={15} />
            <span>Tracker Experimental en Vivo (DB)</span>
          </button>
        </div>

        {seccionActiva === 'fichas' && (
          <button
            type="button"
            onClick={exportarCSV}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '7px 14px',
              backgroundColor: '#ffffff',
              border: '1px solid #059669',
              borderRadius: 'var(--radius-sm)',
              fontSize: '12px',
              fontWeight: 700,
              color: '#059669',
              cursor: 'pointer',
              boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
            }}
          >
            <Download size={14} />
            <span>Exportar Fichas N=60 (.CSV)</span>
          </button>
        )}
      </div>

      {seccionActiva === 'tracker_vivo' ? (
        <ValidacionTallerView />
      ) : (
        <>
          {/* Research Header / Academic Metadata */}
          <div
            style={{
              padding: '16px 18px',
              backgroundColor: '#ecfdf5',
              border: '1px solid #a7f3d0',
              borderRadius: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <GraduationCap size={20} color="#059669" />
                <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#065f46', margin: 0 }}>
                  Ficha Técnica de Investigación — Tesis UCV 2026
                </h3>
              </div>
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  backgroundColor: '#d1fae5',
                  color: '#047857',
                  padding: '3px 10px',
                  borderRadius: '12px',
                  border: '1px solid #6ee7b7',
                }}
              >
                Diseño Preexperimental (N = 60 Casos)
              </span>
            </div>

            <div style={{ fontSize: '12px', color: '#047857', lineHeight: 1.4 }}>
              <strong>Título:</strong> {METADATA_TESIS.titulo}
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '8px',
                fontSize: '11px',
                color: '#065f46',
                borderTop: '1px solid #a7f3d0',
                paddingTop: '8px',
              }}
            >
              <div>
                <strong>👥 Tesistas:</strong> {METADATA_TESIS.autores}
              </div>
              <div>
                <strong>🎓 Asesor:</strong> {METADATA_TESIS.asesor}
              </div>
              <div>
                <strong>🏢 Sede de Estudio:</strong> {METADATA_TESIS.sede}
              </div>
              <div>
                <strong>📊 Muestra:</strong> 30 Pre-test / 30 Post-test
              </div>
            </div>
          </div>

          {/* Operationalization of Variables Summary */}
          <Card style={{ padding: '16px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: '0 0 10px 0' }}>
              Cuadro de Operacionalización de Variables e Indicadores
            </h4>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '10px',
              }}
            >
              <div
                style={{
                  padding: '12px',
                  backgroundColor: 'var(--bg-subtle)',
                  borderRadius: '8px',
                  borderLeft: '4px solid #3b82f6',
                }}
              >
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#2563eb' }}>
                  DIMENSIÓN 1: PREDICCIÓN DE FALLAS
                </div>
                <div style={{ fontSize: '12px', fontWeight: 800, color: 'var(--text-main)', margin: '2px 0 4px 0' }}>
                  PPCF: % Predicción Correcta de Fallas
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                  Pre: <strong>83.33%</strong> ➔ Post: <strong>90.00%</strong> (<strong>+6.67%</strong>, p &lt; 0.001)
                </div>
              </div>

              <div
                style={{
                  padding: '12px',
                  backgroundColor: 'var(--bg-subtle)',
                  borderRadius: '8px',
                  borderLeft: '4px solid #059669',
                }}
              >
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#059669' }}>
                  DIMENSIÓN 2: CONTROL DE INFORMACIÓN
                </div>
                <div style={{ fontSize: '12px', fontWeight: 800, color: 'var(--text-main)', margin: '2px 0 4px 0' }}>
                  PRDC: % Registros Diagnósticos Completos (8/8)
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                  Pre: <strong>66.67%</strong> ➔ Post: <strong>100.00%</strong> (<strong>+33.33%</strong>, p &lt; 0.001)
                </div>
              </div>

              <div
                style={{
                  padding: '12px',
                  backgroundColor: 'var(--bg-subtle)',
                  borderRadius: '8px',
                  borderLeft: '4px solid #7c3aed',
                }}
              >
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#7c3aed' }}>
                  DIMENSIÓN 3: EFICIENCIA DIAGNÓSTICA
                </div>
                <div style={{ fontSize: '12px', fontWeight: 800, color: 'var(--text-main)', margin: '2px 0 4px 0' }}>
                  TPRD: Tiempo Promedio de Respuesta
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                  Pre: <strong>33.67 min</strong> ➔ Post: <strong>9.07 min</strong> (<strong>-73.07%</strong> ahorro, p &lt; 0.001)
                </div>
              </div>
            </div>
          </Card>

          {/* 3 Fichas Switcher & Indicator Detail */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '8px',
            }}
          >
            {[
              { id: 'ficha1', label: 'Ficha 1: PPCF (Exactitud)', val: postPPCFPct.toFixed(1) + '%', col: '#2563eb' },
              { id: 'ficha2', label: 'Ficha 2: PRDC (Completitud)', val: postPRDCPct.toFixed(1) + '%', col: '#059669' },
              { id: 'ficha3', label: 'Ficha 3: TPRD (Tiempo Min.)', val: postTPRDProm.toFixed(1) + ' min', col: '#7c3aed' },
            ].map((f) => {
              const esActivo = fichaActiva === f.id;
              return (
                <button
                  key={f.id}
                  type="button"
                  onClick={() => setFichaActiva(f.id as 'ficha1' | 'ficha2' | 'ficha3')}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    padding: '12px 14px',
                    backgroundColor: esActivo ? f.col : '#ffffff',
                    color: esActivo ? '#ffffff' : 'var(--text-main)',
                    border: esActivo ? `1px solid ${f.col}` : '1px solid var(--border-color)',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    boxShadow: esActivo ? '0 2px 8px rgba(0,0,0,0.12)' : 'none',
                  }}
                >
                  <span style={{ fontSize: '11px', fontWeight: 600, opacity: esActivo ? 0.9 : 0.7 }}>
                    {f.label}
                  </span>
                  <span style={{ fontSize: '16px', fontWeight: 800, marginTop: '4px' }}>
                    Post: {f.val}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Detailed Card for Selected Ficha */}
          <Card style={{ padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', marginBottom: '12px' }}>
              <div>
                <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--primary)', textTransform: 'uppercase' }}>
                  {infoFicha.codigo}
                </span>
                <h4 style={{ fontSize: '14px', fontWeight: 800, color: 'var(--text-main)', margin: '2px 0 0 0' }}>
                  {infoFicha.numero}
                </h4>
              </div>

              {/* Phase Switcher (Pre vs Post vs Contraste) */}
              <div
                style={{
                  display: 'inline-flex',
                  backgroundColor: '#f1f5f9',
                  padding: '3px',
                  borderRadius: '6px',
                  gap: '3px',
                }}
              >
                <button
                  type="button"
                  onClick={() => setFaseActiva('post')}
                  style={{
                    padding: '5px 10px',
                    fontSize: '11px',
                    fontWeight: 700,
                    borderRadius: '5px',
                    border: 'none',
                    cursor: 'pointer',
                    backgroundColor: faseActiva === 'post' ? '#059669' : 'transparent',
                    color: faseActiva === 'post' ? '#ffffff' : 'var(--text-secondary)',
                  }}
                >
                  Post-test (CarBot)
                </button>
                <button
                  type="button"
                  onClick={() => setFaseActiva('pre')}
                  style={{
                    padding: '5px 10px',
                    fontSize: '11px',
                    fontWeight: 700,
                    borderRadius: '5px',
                    border: 'none',
                    cursor: 'pointer',
                    backgroundColor: faseActiva === 'pre' ? '#d97706' : 'transparent',
                    color: faseActiva === 'pre' ? '#ffffff' : 'var(--text-secondary)',
                  }}
                >
                  Pre-test (Manual)
                </button>
                <button
                  type="button"
                  onClick={() => setFaseActiva('contraste')}
                  style={{
                    padding: '5px 10px',
                    fontSize: '11px',
                    fontWeight: 700,
                    borderRadius: '5px',
                    border: 'none',
                    cursor: 'pointer',
                    backgroundColor: faseActiva === 'contraste' ? '#2563eb' : 'transparent',
                    color: faseActiva === 'contraste' ? '#ffffff' : 'var(--text-secondary)',
                  }}
                >
                  Contraste
                </button>
              </div>
            </div>

            {/* Formula & Hypothesis Card */}
            <div
              style={{
                padding: '10px 14px',
                backgroundColor: 'var(--bg-subtle)',
                borderRadius: '8px',
                fontSize: '11px',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
                marginBottom: '14px',
              }}
            >
              <div>
                <strong>Fórmula:</strong> {infoFicha.formula}
              </div>
              <div style={{ color: 'var(--primary)', fontWeight: 600 }}>
                💡 <strong>Hipótesis:</strong> {infoFicha.hipotesis}
              </div>
            </div>

            {/* Pre vs Post Comparison or Records Table */}
            {faseActiva === 'contraste' ? (
              <div style={{ width: '100%', height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={dataComparativaFichas} margin={{ top: 12, right: 16, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="indicador" stroke="#64748b" fontSize={11} tickLine={false} />
                    <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        borderColor: 'var(--border-color)',
                        borderRadius: '8px',
                        fontSize: '11px',
                        padding: '6px 10px',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                      }}
                    />
                    <Legend verticalAlign="top" height={28} wrapperStyle={{ fontSize: '11px' }} />
                    <Bar dataKey="Pre-test (Manual)" fill="#f59e0b" radius={[4, 4, 0, 0]} maxBarSize={32} />
                    <Bar dataKey="Post-test (CarBot AI)" fill="#10b981" radius={[4, 4, 0, 0]} maxBarSize={32} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ backgroundColor: 'var(--bg-subtle)', borderBottom: '2px solid var(--border-color)' }}>
                      <th style={{ padding: '8px 10px' }}>Item</th>
                      <th style={{ padding: '8px 10px' }}>Fecha</th>
                      <th style={{ padding: '8px 10px' }}>Placa</th>
                      <th style={{ padding: '8px 10px' }}>Vehículo</th>
                      <th style={{ padding: '8px 10px' }}>Síntoma</th>
                      <th style={{ padding: '8px 10px' }}>Falla Real</th>
                      <th style={{ padding: '8px 10px' }}>Predicción</th>
                      <th style={{ padding: '8px 10px' }}>Campos (8/8)</th>
                      <th style={{ padding: '8px 10px' }}>Tiempo</th>
                      <th style={{ padding: '8px 10px' }}>Resultado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {casosVisibles.map((caso) => (
                      <tr key={caso.item} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: '7px 10px', fontWeight: 700 }}>#{caso.item}</td>
                        <td style={{ padding: '7px 10px', color: 'var(--text-secondary)' }}>{caso.fecha}</td>
                        <td style={{ padding: '7px 10px', fontFamily: 'monospace', fontWeight: 600 }}>{caso.placa}</td>
                        <td style={{ padding: '7px 10px' }}>{caso.marca_modelo}</td>
                        <td style={{ padding: '7px 10px', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {caso.sintoma}
                        </td>
                        <td style={{ padding: '7px 10px', fontWeight: 500 }}>{caso.falla_real}</td>
                        <td style={{ padding: '7px 10px', color: 'var(--primary)' }}>{caso.chatbot_prediccion}</td>
                        <td style={{ padding: '7px 10px', textAlign: 'center' }}>
                          {caso.campos_completos === 1 ? (
                            <span style={{ color: '#059669', fontWeight: 700 }}>8/8</span>
                          ) : (
                            <span style={{ color: '#dc2626', fontWeight: 700 }}>Incompleto</span>
                          )}
                        </td>
                        <td style={{ padding: '7px 10px', fontWeight: 700 }}>{caso.tiempo_diagnostico_minutos} min</td>
                        <td style={{ padding: '7px 10px' }}>
                          {caso.prediccion_correcta === 1 ? (
                            <span
                              style={{
                                backgroundColor: '#dcfce7',
                                color: '#166534',
                                padding: '2px 6px',
                                borderRadius: '4px',
                                fontWeight: 700,
                              }}
                            >
                              Acierto
                            </span>
                          ) : (
                            <span
                              style={{
                                backgroundColor: '#fee2e2',
                                color: '#991b1b',
                                padding: '2px 6px',
                                borderRadius: '4px',
                                fontWeight: 700,
                              }}
                            >
                              Falla
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
};
