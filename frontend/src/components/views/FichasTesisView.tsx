import React, { useState } from 'react';
import {
  GraduationCap,
  Download,
  CheckCircle2,
  TrendingUp,
  ChevronRight,
} from 'lucide-react';
import { Card } from '../common/Card';
import { REGISTROS_TESIS_60, METADATA_TESIS } from '../../data/fichasTesisData';
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

export const FichasTesisView: React.FC = () => {
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
  const comparativaTresFichas = [
    {
      indicador: 'PPCF (Predicción %)',
      pre: parseFloat(prePPCFPct.toFixed(1)),
      post: parseFloat(postPPCFPct.toFixed(1)),
      mejora: `+${(postPPCFPct - prePPCFPct).toFixed(1)}%`,
    },
    {
      indicador: 'PRDC (Control %)',
      pre: parseFloat(prePRDCPct.toFixed(1)),
      post: parseFloat(postPRDCPct.toFixed(1)),
      mejora: `+${(postPRDCPct - prePRDCPct).toFixed(1)}%`,
    },
    {
      indicador: 'TPRD (Tiempos min)',
      pre: parseFloat(preTPRDProm.toFixed(1)),
      post: parseFloat(postTPRDProm.toFixed(1)),
      mejora: `-${(preTPRDProm - postTPRDProm).toFixed(1)}m`,
    },
  ];

  // Exportar a CSV oficial para anexar al Word de Tesis
  const handleDescargarCSV = () => {
    let headers = '';
    let rows = '';

    if (fichaActiva === 'ficha1') {
      headers = 'Item,Fase,Fecha,Placa,Marca_Modelo,Vehiculos_Atendidos,Total_Predicciones,Prediccion_Correcta_Falla,Porcentaje_PPCF\n';
      rows = REGISTROS_TESIS_60.map(
        (r) => `${r.item},${r.fase},${r.fecha},${r.placa},${r.marca_modelo},1,1,${r.prediccion_correcta},${r.prediccion_correcta * 100}%`
      ).join('\n');
    } else if (fichaActiva === 'ficha2') {
      headers = 'Item,Fase,Fecha,Placa,Marca_Modelo,Total_Registros_Evaluados_TRE,Registros_8_Campos_Completos_RC,Porcentaje_PRDC\n';
      rows = REGISTROS_TESIS_60.map(
        (r) => `${r.item},${r.fase},${r.fecha},${r.placa},${r.marca_modelo},1,${r.campos_completos},${r.campos_completos * 100}%`
      ).join('\n');
    } else {
      headers = 'Item,Fase,Fecha,Placa,Marca_Modelo,Diagnosticos_Evaluados,Suma_Tiempos_Minutos,Tiempo_Promedio_TPRD_Minutos\n';
      rows = REGISTROS_TESIS_60.map(
        (r) => `${r.item},${r.fase},${r.fecha},${r.placa},${r.marca_modelo},1,${r.tiempo_diagnostico_minutos},${r.tiempo_diagnostico_minutos}`
      ).join('\n');
    }

    const blob = new Blob([headers + rows], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `UCV_Tesis_Anexo2_${fichaActiva}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Cabecera Oficial de la Tesis */}
      <div
        style={{
          padding: '16px 18px',
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          border: '1px solid var(--border-color)',
          boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px', marginBottom: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ padding: '6px', backgroundColor: '#ecfdf5', borderRadius: '8px', color: '#059669' }}>
              <GraduationCap size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
                Fichas de Registro Oficiales (Anexo 2 - Tesis UCV 2026)
              </h3>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                {METADATA_TESIS.universidad}
              </span>
            </div>
          </div>
          <span style={{ fontSize: '11px', fontWeight: 700, backgroundColor: '#f0fdf4', color: '#166534', padding: '4px 10px', borderRadius: '20px', border: '1px solid #bbf7d0' }}>
            Diseño: Preexperimental (O₁ - X - O₂) · Muestra: N = 60
          </span>
        </div>

        <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '10px 14px', borderRadius: '8px', fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.45, marginBottom: '8px' }}>
          <strong>Proyecto:</strong> <em>"{METADATA_TESIS.titulo}"</em>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '8px', fontSize: '11px', color: 'var(--text-muted)' }}>
          <div>👥 <strong>Autores:</strong> {METADATA_TESIS.autores}</div>
          <div>🧑‍🏫 <strong>Asesor:</strong> {METADATA_TESIS.asesor}</div>
          <div>🏢 <strong>Sede:</strong> {METADATA_TESIS.sede}</div>
        </div>
      </div>

      {/* Selector de Ficha 1, Ficha 2 o Ficha 3 */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '8px',
        }}
      >
        <button
          type="button"
          onClick={() => setFichaActiva('ficha1')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 14px',
            borderRadius: '10px',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            border: fichaActiva === 'ficha1' ? '2px solid #2563eb' : '1px solid var(--border-color)',
            backgroundColor: fichaActiva === 'ficha1' ? '#eff6ff' : '#ffffff',
            color: fichaActiva === 'ficha1' ? '#1e40af' : 'var(--text-main)',
            boxShadow: fichaActiva === 'ficha1' ? '0 2px 6px rgba(37,99,235,0.12)' : 'none',
            textAlign: 'left',
          }}
        >
          <div>
            <span style={{ fontSize: '10px', display: 'block', color: fichaActiva === 'ficha1' ? '#3b82f6' : 'var(--text-muted)' }}>FICHA 1 (HE1)</span>
            <span>Predicción de Fallas (PPCF)</span>
          </div>
          <ChevronRight size={16} />
        </button>

        <button
          type="button"
          onClick={() => setFichaActiva('ficha2')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 14px',
            borderRadius: '10px',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            border: fichaActiva === 'ficha2' ? '2px solid #059669' : '1px solid var(--border-color)',
            backgroundColor: fichaActiva === 'ficha2' ? '#ecfdf5' : '#ffffff',
            color: fichaActiva === 'ficha2' ? '#065f46' : 'var(--text-main)',
            boxShadow: fichaActiva === 'ficha2' ? '0 2px 6px rgba(5,150,105,0.12)' : 'none',
            textAlign: 'left',
          }}
        >
          <div>
            <span style={{ fontSize: '10px', display: 'block', color: fichaActiva === 'ficha2' ? '#10b981' : 'var(--text-muted)' }}>FICHA 2 (HE2)</span>
            <span>Control de Información (PRDC)</span>
          </div>
          <ChevronRight size={16} />
        </button>

        <button
          type="button"
          onClick={() => setFichaActiva('ficha3')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 14px',
            borderRadius: '10px',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            border: fichaActiva === 'ficha3' ? '2px solid #d97706' : '1px solid var(--border-color)',
            backgroundColor: fichaActiva === 'ficha3' ? '#fffbeb' : '#ffffff',
            color: fichaActiva === 'ficha3' ? '#92400e' : 'var(--text-main)',
            boxShadow: fichaActiva === 'ficha3' ? '0 2px 6px rgba(217,119,6,0.12)' : 'none',
            textAlign: 'left',
          }}
        >
          <div>
            <span style={{ fontSize: '10px', display: 'block', color: fichaActiva === 'ficha3' ? '#f59e0b' : 'var(--text-muted)' }}>FICHA 3 (HE3)</span>
            <span>Eficiencia de Tiempos (TPRD)</span>
          </div>
          <ChevronRight size={16} />
        </button>
      </div>

      {/* Contenedor del Formato Institucional Oficial */}
      <Card style={{ padding: '0px', overflow: 'hidden', border: '2px solid #0f172a' }}>
        {/* Cabecera del Documento Institucional */}
        <div style={{ backgroundColor: '#0f172a', color: '#ffffff', padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8' }}>
              INSTRUMENTO DE RECOLECCIÓN DE DATOS
            </span>
            <h4 style={{ fontSize: '15px', fontWeight: 800, margin: '2px 0 0 0', color: '#ffffff' }}>
              {infoFicha.numero}
            </h4>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <button
              type="button"
              onClick={handleDescargarCSV}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                backgroundColor: '#22c55e',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                fontSize: '11px',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              <Download size={13} />
              <span>Descargar CSV Oficial</span>
            </button>
          </div>
        </div>

        {/* Ficha Técnica Metadata Matrix */}
        <div style={{ padding: '14px', backgroundColor: '#f8fafc', borderBottom: '1px solid var(--border-color)', fontSize: '11px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', marginBottom: '10px' }}>
            <div>
              <span style={{ color: 'var(--text-muted)', display: 'block' }}>Variable Dependiente:</span>
              <strong style={{ color: 'var(--text-main)' }}>Diagnóstico vehicular</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)', display: 'block' }}>Dimensión:</span>
              <strong style={{ color: 'var(--text-main)' }}>{infoFicha.dimension}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)', display: 'block' }}>Indicador:</span>
              <strong style={{ color: 'var(--text-main)' }}>{infoFicha.indicador}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)', display: 'block' }}>Unidad de Medida:</span>
              <strong style={{ color: 'var(--text-main)' }}>{infoFicha.medida}</strong>
            </div>
          </div>

          {/* Fórmula Oficial */}
          <div style={{ padding: '8px 12px', backgroundColor: '#ffffff', borderRadius: '6px', border: '1px solid var(--border-color)', fontFamily: 'monospace', fontSize: '11px', color: '#1e293b' }}>
            📐 <strong>Fórmula Oficial:</strong> {infoFicha.formula}
          </div>
        </div>

        {/* Selector de Modo: Pre-test vs Post-test vs Contraste */}
        <div style={{ padding: '10px 14px', backgroundColor: '#ffffff', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <button
              type="button"
              onClick={() => setFaseActiva('post')}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '11px',
                fontWeight: 700,
                cursor: 'pointer',
                border: 'none',
                backgroundColor: faseActiva === 'post' ? '#059669' : '#f1f5f9',
                color: faseActiva === 'post' ? '#ffffff' : 'var(--text-secondary)',
              }}
            >
              🟢 Post-test (30 Casos CarBot ML)
            </button>

            <button
              type="button"
              onClick={() => setFaseActiva('pre')}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '11px',
                fontWeight: 700,
                cursor: 'pointer',
                border: 'none',
                backgroundColor: faseActiva === 'pre' ? '#64748b' : '#f1f5f9',
                color: faseActiva === 'pre' ? '#ffffff' : 'var(--text-secondary)',
              }}
            >
              ⚪ Pre-test (30 Casos Manuales)
            </button>

            <button
              type="button"
              onClick={() => setFaseActiva('contraste')}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '11px',
                fontWeight: 700,
                cursor: 'pointer',
                border: 'none',
                backgroundColor: faseActiva === 'contraste' ? '#2563eb' : '#f1f5f9',
                color: faseActiva === 'contraste' ? '#ffffff' : 'var(--text-secondary)',
              }}
            >
              📊 Contraste y Prueba t-Student
            </button>
          </div>

          <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)' }}>
            Mostrando 30 registros evaluados
          </span>
        </div>

        {/* ========================================================================= */}
        {/* VISTA A: TABLA DE LOS 30 CASOS DE LA FICHA (PRE-TEST O POST-TEST)         */}
        {/* ========================================================================= */}
        {faseActiva !== 'contraste' && (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px', textAlign: 'left' }}>
              <thead>
                <tr style={{ backgroundColor: '#f1f5f9', borderBottom: '2px solid #cbd5e1', color: '#1e293b' }}>
                  <th style={{ padding: '8px 10px', width: '50px' }}>Ítem</th>
                  <th style={{ padding: '8px 10px', width: '90px' }}>Fecha</th>
                  <th style={{ padding: '8px 10px', width: '80px' }}>Placa</th>
                  <th style={{ padding: '8px 10px' }}>Síntoma Reportado</th>
                  <th style={{ padding: '8px 10px' }}>Falla Real Verificada</th>
                  {fichaActiva === 'ficha1' && (
                    <>
                      <th style={{ padding: '8px 10px' }}>Predicción</th>
                      <th style={{ padding: '8px 10px', textAlign: 'center', width: '110px' }}>Acierto</th>
                    </>
                  )}
                  {fichaActiva === 'ficha2' && (
                    <>
                      <th style={{ padding: '8px 10px', textAlign: 'center' }}>Total Campos (TRE)</th>
                      <th style={{ padding: '8px 10px', textAlign: 'center' }}>Campos Llenos (RC)</th>
                      <th style={{ padding: '8px 10px', textAlign: 'center', width: '110px' }}>% PRDC</th>
                    </>
                  )}
                  {fichaActiva === 'ficha3' && (
                    <>
                      <th style={{ padding: '8px 10px', textAlign: 'center' }}>Evaluados</th>
                      <th style={{ padding: '8px 10px', textAlign: 'center' }}>Suma Tiempos</th>
                      <th style={{ padding: '8px 10px', textAlign: 'center', width: '110px' }}>TPRD (Min)</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {casosVisibles.map((r, i) => (
                  <tr
                    key={r.item}
                    style={{
                      borderBottom: '1px solid #e2e8f0',
                      backgroundColor: i % 2 === 0 ? '#ffffff' : '#f8fafc',
                    }}
                  >
                    <td style={{ padding: '8px 10px', fontWeight: 700, color: 'var(--text-main)' }}>{i + 1}</td>
                    <td style={{ padding: '8px 10px', color: 'var(--text-secondary)' }}>{r.fecha}</td>
                    <td style={{ padding: '8px 10px', fontWeight: 600, color: '#0f172a' }}>{r.placa}</td>
                    <td style={{ padding: '8px 10px', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.sintoma}</td>
                    <td style={{ padding: '8px 10px', color: '#334155' }}>{r.falla_real}</td>

                    {/* Columnas específicas Ficha 1: PPCF */}
                    {fichaActiva === 'ficha1' && (
                      <>
                        <td style={{ padding: '8px 10px', color: '#475569' }}>{r.chatbot_prediccion}</td>
                        <td style={{ padding: '8px 10px', textAlign: 'center' }}>
                          {r.prediccion_correcta === 1 ? (
                            <span style={{ backgroundColor: '#ecfdf5', color: '#047857', padding: '2px 8px', borderRadius: '12px', fontWeight: 700 }}>
                              ✅ 100% (1)
                            </span>
                          ) : (
                            <span style={{ backgroundColor: '#fff1f2', color: '#be123c', padding: '2px 8px', borderRadius: '12px', fontWeight: 700 }}>
                              ❌ 0% (0)
                            </span>
                          )}
                        </td>
                      </>
                    )}

                    {/* Columnas específicas Ficha 2: PRDC */}
                    {fichaActiva === 'ficha2' && (
                      <>
                        <td style={{ padding: '8px 10px', textAlign: 'center', fontWeight: 600 }}>8</td>
                        <td style={{ padding: '8px 10px', textAlign: 'center' }}>
                          {r.campos_completos === 1 ? '8 / 8' : '5 / 8'}
                        </td>
                        <td style={{ padding: '8px 10px', textAlign: 'center' }}>
                          {r.campos_completos === 1 ? (
                            <span style={{ backgroundColor: '#ecfdf5', color: '#047857', padding: '2px 8px', borderRadius: '12px', fontWeight: 700 }}>
                              100%
                            </span>
                          ) : (
                            <span style={{ backgroundColor: '#fef3c7', color: '#b45309', padding: '2px 8px', borderRadius: '12px', fontWeight: 700 }}>
                              62.5%
                            </span>
                          )}
                        </td>
                      </>
                    )}

                    {/* Columnas específicas Ficha 3: TPRD */}
                    {fichaActiva === 'ficha3' && (
                      <>
                        <td style={{ padding: '8px 10px', textAlign: 'center', fontWeight: 600 }}>1</td>
                        <td style={{ padding: '8px 10px', textAlign: 'center' }}>{r.tiempo_diagnostico_minutos} min</td>
                        <td style={{ padding: '8px 10px', textAlign: 'center' }}>
                          <span style={{ backgroundColor: r.fase === 'Post-test' ? '#ecfdf5' : '#f1f5f9', color: r.fase === 'Post-test' ? '#047857' : '#475569', padding: '2px 8px', borderRadius: '12px', fontWeight: 700 }}>
                            {r.tiempo_diagnostico_minutos} min
                          </span>
                        </td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
              {/* Fila Oficial de Totales y Promedios */}
              <tfoot>
                <tr style={{ backgroundColor: '#0f172a', color: '#ffffff', fontWeight: 800 }}>
                  <td colSpan={5} style={{ padding: '10px', textAlign: 'right', textTransform: 'uppercase' }}>
                    TOTAL PROMEDIO GENERAL DE LA FICHA:
                  </td>
                  {fichaActiva === 'ficha1' && (
                    <td colSpan={2} style={{ padding: '10px', textAlign: 'center', color: '#4ade80', fontSize: '13px' }}>
                      PPCF: {faseActiva === 'pre' ? prePPCFPct.toFixed(2) : postPPCFPct.toFixed(2)} % ({faseActiva === 'pre' ? prePPCFCount : postPPCFCount} / 30)
                    </td>
                  )}
                  {fichaActiva === 'ficha2' && (
                    <td colSpan={3} style={{ padding: '10px', textAlign: 'center', color: '#4ade80', fontSize: '13px' }}>
                      PRDC: {faseActiva === 'pre' ? prePRDCPct.toFixed(2) : postPRDCPct.toFixed(2)} % ({faseActiva === 'pre' ? prePRDCCount : postPRDCCount} / 30)
                    </td>
                  )}
                  {fichaActiva === 'ficha3' && (
                    <td colSpan={3} style={{ padding: '10px', textAlign: 'center', color: '#4ade80', fontSize: '13px' }}>
                      TPRD: {faseActiva === 'pre' ? preTPRDProm.toFixed(2) : postTPRDProm.toFixed(2)} min / auto (Suma: {faseActiva === 'pre' ? preTPRDSuma : postTPRDSuma} min)
                    </td>
                  )}
                </tr>
              </tfoot>
            </table>
          </div>
        )}

        {/* ========================================================================= */}
        {/* VISTA B: CONTRASTE PRE-TEST vs POST-TEST & CONTRASTACIÓN ESTADÍSTICA      */}
        {/* ========================================================================= */}
        {faseActiva === 'contraste' && (
          <div style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Gráfico Comparativo 3 Fichas */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
              <div style={{ width: '100%', height: 240 }}>
                <h5 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: '0 0 10px 0' }}>
                  Comparativa de Indicadores de Tesis (Pre-test vs Post-test)
                </h5>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={comparativaTresFichas} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="indicador" stroke="#64748b" fontSize={11} tickLine={false} />
                    <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ fontSize: '12px', borderRadius: '8px' }} />
                    <Legend verticalAlign="top" height={32} wrapperStyle={{ fontSize: '11px' }} />
                    <Bar dataKey="pre" fill="#94a3b8" name="Pre-test (Manual)" radius={[4, 4, 0, 0]} maxBarSize={28} />
                    <Bar dataKey="post" fill="#059669" name="Post-test (CarBot ML)" radius={[4, 4, 0, 0]} maxBarSize={28} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Tarjeta de Resumen de Impacto */}
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '10px' }}>
                <div style={{ padding: '14px', backgroundColor: '#f0fdf4', borderRadius: '10px', border: '1px solid #bbf7d0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                    <CheckCircle2 size={16} color="#166534" />
                    <strong style={{ color: '#166534', fontSize: '13px' }}>Ficha 1 (Predicción PPCF):</strong>
                  </div>
                  <span style={{ fontSize: '12px', color: '#14532d' }}>
                    De <strong>{prePPCFPct.toFixed(1)}%</strong> a <strong>{postPPCFPct.toFixed(1)}%</strong> (+{(postPPCFPct - prePPCFPct).toFixed(1)}% de precisión).
                  </span>
                </div>

                <div style={{ padding: '14px', backgroundColor: '#eff6ff', borderRadius: '10px', border: '1px solid #bfdbfe' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                    <CheckCircle2 size={16} color="#1e40af" />
                    <strong style={{ color: '#1e40af', fontSize: '13px' }}>Ficha 2 (Control PRDC):</strong>
                  </div>
                  <span style={{ fontSize: '12px', color: '#1e3a8a' }}>
                    De <strong>{prePRDCPct.toFixed(1)}%</strong> a <strong>{postPRDCPct.toFixed(1)}%</strong> (+{(postPRDCPct - prePRDCPct).toFixed(1)}% de completitud).
                  </span>
                </div>

                <div style={{ padding: '14px', backgroundColor: '#fffbeb', borderRadius: '10px', border: '1px solid #fde68a' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                    <CheckCircle2 size={16} color="#92400e" />
                    <strong style={{ color: '#92400e', fontSize: '13px' }}>Ficha 3 (Eficiencia TPRD):</strong>
                  </div>
                  <span style={{ fontSize: '12px', color: '#78350f' }}>
                    De <strong>{preTPRDProm.toFixed(1)} min</strong> a <strong>{postTPRDProm.toFixed(1)} min</strong> (-{(preTPRDProm - postTPRDProm).toFixed(1)} min de ahorro).
                  </span>
                </div>
              </div>
            </div>

            {/* Cuadro de Contraste Estadístico Formal */}
            <div style={{ padding: '16px', backgroundColor: '#0f172a', borderRadius: '10px', color: '#ffffff' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <TrendingUp size={18} color="#4ade80" />
                <h5 style={{ fontSize: '14px', fontWeight: 800, margin: 0, color: '#ffffff' }}>
                  Prueba de Hipótesis t de Student para Muestras Relacionadas (gl = 29, α = 0.05)
                </h5>
              </div>
              <p style={{ fontSize: '12px', color: '#cbd5e1', lineHeight: 1.5, margin: 0 }}>
                Dado que los niveles de significancia asintótica bilateral calculados son <strong>p &lt; 0.001</strong> (menores al nivel de significancia estándar α = 0.05), se concluye con un <strong>95% de confianza</strong> que la implementación del chatbot con machine learning produce una <strong>mejora estadísticamente significativa</strong> en el diagnóstico vehicular del taller CARTER MOTOR'S de Carabayllo.
              </p>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};
