import React, { useState } from 'react';
import { Card } from '../../../common/Card';
import { Badge } from '../../../common/Badge';
import { DATOS_SINTETICOS_DEMO_60, METADATA_TESIS, type RegistroTesis } from '../../../../data/fichasTesisData';
import { TesisTablasFichas } from './TesisTablasFichas';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

export type FichaId = 'ficha1' | 'ficha2' | 'ficha3';
export type FaseVista = 'pre' | 'post' | 'contraste';

interface TesisFichaOficialViewProps {
  fichaId: FichaId;
  casosReales?: RegistroTesis[];
}

export const TesisFichaOficialView: React.FC<TesisFichaOficialViewProps> = ({
  fichaId,
  casosReales = [],
}) => {
  const [fase, setFase] = useState<FaseVista>('pre');
  const [modoDemo, setModoDemo] = useState(false);

  // Fuente de datos según el modo activo
  const casosFuente: RegistroTesis[] = modoDemo ? DATOS_SINTETICOS_DEMO_60 : casosReales;

  const preCasos = casosFuente.filter((c) => c.fase === 'Pre-test');
  const postCasos = casosFuente.filter((c) => c.fase === 'Post-test');
  const casosActivos: RegistroTesis[] = fase === 'pre' ? preCasos : postCasos;

  // Cálculos Ficha 1 (PPCF)
  const preAciertos = preCasos.filter((c) => c.prediccion_correcta === 1).length;
  const postAciertos = postCasos.filter((c) => c.prediccion_correcta === 1).length;
  const prePPCF = preCasos.length > 0 ? (preAciertos / preCasos.length) * 100 : 0;
  const postPPCF = postCasos.length > 0 ? (postAciertos / postCasos.length) * 100 : 0;

  // Cálculos Ficha 2 (PRDC)
  const preCompletos = preCasos.filter((c) => c.campos_completos === 1).length;
  const postCompletos = postCasos.filter((c) => c.campos_completos === 1).length;
  const prePRDC = preCasos.length > 0 ? (preCompletos / preCasos.length) * 100 : 0;
  const postPRDC = postCasos.length > 0 ? (postCompletos / postCasos.length) * 100 : 0;

  // Cálculos Ficha 3 (TPRD)
  const preTiempoSuma = preCasos.reduce((acc, c) => acc + c.tiempo_diagnostico_minutos, 0);
  const postTiempoSuma = postCasos.reduce((acc, c) => acc + c.tiempo_diagnostico_minutos, 0);
  const preTPRD = preCasos.length > 0 ? preTiempoSuma / preCasos.length : 0;
  const postTPRD = postCasos.length > 0 ? postTiempoSuma / postCasos.length : 0;

  const infoFicha = {
    ficha1: {
      tituloFicha: 'Ficha de registro: Predicción de fallas vehiculares',
      codigo: 'Anexo 2 - Ficha 1',
      dimension: 'Predicción de fallas vehiculares',
      indicador: 'Porcentaje de predicción correcta de fallas vehiculares (PPCF)',
      medida: 'Porcentaje (%)',
      formula: 'PPCF = (N.° de predicciones correctas / Total de predicciones realizadas) × 100',
    },
    ficha2: {
      tituloFicha: 'Ficha de registro: Control de información diagnóstica vehicular',
      codigo: 'Anexo 2 - Ficha 2',
      dimension: 'Control de información diagnóstica vehicular',
      indicador: 'Porcentaje de registros diagnósticos completos (PRDC)',
      medida: 'Porcentaje (%)',
      formula: 'RDC = (RC / TRE) × 100  [RC: Registros con los 8 campos completos, TRE: Total registros evaluados]',
    },
    ficha3: {
      tituloFicha: 'Ficha de registro: Eficiencia del diagnóstico vehicular',
      codigo: 'Anexo 2 - Ficha 3',
      dimension: 'Eficiencia del diagnóstico vehicular',
      indicador: 'Tiempo promedio de respuesta diagnóstica (TPRD)',
      medida: 'Minutos',
      formula: 'TPRD = Suma total de tiempos de respuesta diagnóstica / Total de diagnósticos evaluados',
    },
  }[fichaId];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* Banner de Estado Metodológico */}
      <div
        style={{
          padding: '10px 14px',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          backgroundColor: modoDemo ? '#fffbeb' : '#f8fafc',
          border: modoDemo ? '1px solid #fde68a' : '1px solid #e2e8f0',
        }}
      >
        {modoDemo ? (
          <AlertCircle size={18} style={{ color: '#d97706', flexShrink: 0 }} />
        ) : (
          <CheckCircle2 size={18} style={{ color: '#059669', flexShrink: 0 }} />
        )}
        <div style={{ fontSize: '12px', lineHeight: '1.4' }}>
          {modoDemo ? (
            <span style={{ color: '#92400e', fontWeight: 600 }}>
              MODO DEMOSTRACIÓN: Visualizando 60 registros sintéticos de prueba (excluidos de los resultados oficiales de tesis).
            </span>
          ) : (
            <span style={{ color: '#334155' }}>
              <strong>Trabajo de campo pendiente:</strong> Los resultados pretest y postest se calcularán exclusivamente
              con registros reales recopilados y verificados durante la aplicación de los instrumentos. <strong>Avance actual: {casosReales.length} de 60 registros.</strong>
            </span>
          )}
        </div>
      </div>

      {/* 1. Tarjeta de Formato Oficial Institucional (Anexo 2) */}
      <Card style={{ padding: 0, overflow: 'hidden', border: '1px solid var(--border-color)' }}>
        {/* Banner Superior */}
        <div
          style={{
            padding: '14px 18px',
            backgroundColor: 'var(--bg-subtle)',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  color: 'var(--primary)',
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                }}
              >
                UNIVERSIDAD CÉSAR VALLEJO · {infoFicha.codigo}
              </span>
              <Badge
                type={modoDemo ? 'borrador' : 'confirmado'}
                label={modoDemo ? 'Demo Sintética' : `Muestra Real (${casosFuente.length}/60)`}
              />
            </div>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 800, color: 'var(--text-main)' }}>
              {infoFicha.tituloFicha}
            </h3>
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
            {/* Selector de Modo: Real vs Demo */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                backgroundColor: '#e2e8f0',
                padding: '2px',
                borderRadius: '8px',
                gap: '2px',
              }}
            >
              <button
                type="button"
                onClick={() => setModoDemo(false)}
                style={{
                  padding: '5px 9px',
                  fontSize: '11px',
                  fontWeight: 700,
                  borderRadius: '6px',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: !modoDemo ? '#ffffff' : 'transparent',
                  color: !modoDemo ? '#059669' : 'var(--text-muted)',
                  boxShadow: !modoDemo ? '0 1px 2px rgba(0,0,0,0.08)' : 'none',
                }}
              >
                Reales ({casosReales.length})
              </button>
              <button
                type="button"
                onClick={() => setModoDemo(true)}
                style={{
                  padding: '5px 9px',
                  fontSize: '11px',
                  fontWeight: 700,
                  borderRadius: '6px',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: modoDemo ? '#ffffff' : 'transparent',
                  color: modoDemo ? '#d97706' : 'var(--text-muted)',
                  boxShadow: modoDemo ? '0 1px 2px rgba(0,0,0,0.08)' : 'none',
                }}
              >
                Demo (60)
              </button>
            </div>

            {/* Selector de Fase de Prueba */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                backgroundColor: '#f1f5f9',
                padding: '3px',
                borderRadius: '8px',
                gap: '2px',
              }}
            >
              <button
                type="button"
                onClick={() => setFase('pre')}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '5px',
                  padding: '5px 10px',
                  fontSize: '11px',
                  fontWeight: 700,
                  borderRadius: '6px',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: fase === 'pre' ? '#ffffff' : 'transparent',
                  color: fase === 'pre' ? 'var(--text-main)' : 'var(--text-muted)',
                  boxShadow: fase === 'pre' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                }}
              >
                Pre-test ({preCasos.length})
              </button>

              <button
                type="button"
                onClick={() => setFase('post')}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '5px',
                  padding: '5px 10px',
                  fontSize: '11px',
                  fontWeight: 700,
                  borderRadius: '6px',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: fase === 'post' ? '#ffffff' : 'transparent',
                  color: fase === 'post' ? 'var(--primary)' : 'var(--text-muted)',
                  boxShadow: fase === 'post' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                }}
              >
                Post-test ({postCasos.length})
              </button>

              <button
                type="button"
                onClick={() => setFase('contraste')}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '5px',
                  padding: '5px 10px',
                  fontSize: '11px',
                  fontWeight: 700,
                  borderRadius: '6px',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: fase === 'contraste' ? '#ffffff' : 'transparent',
                  color: fase === 'contraste' ? '#059669' : 'var(--text-muted)',
                  boxShadow: fase === 'contraste' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                }}
              >
                Contraste
              </button>
            </div>
          </div>
        </div>

        {/* Metadatos Institucionales de la Ficha */}
        <div
          style={{
            padding: '12px 18px',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '8px 16px',
            fontSize: '11.5px',
            backgroundColor: '#ffffff',
            borderBottom: '1px solid var(--border-color)',
          }}
        >
          <div>
            <strong style={{ color: 'var(--text-secondary)' }}>Investigador(es): </strong>
            <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{METADATA_TESIS.autores}</span>
          </div>
          <div>
            <strong style={{ color: 'var(--text-secondary)' }}>Fase actual: </strong>
            <span style={{ color: 'var(--text-main)', fontWeight: 700 }}>
              {fase === 'pre'
                ? 'Pre-test (Diagnóstico Tradicional)'
                : fase === 'post'
                ? 'Post-test (Asistido por CarBot)'
                : 'Contraste de Fases'}
            </span>
          </div>
          <div>
            <strong style={{ color: 'var(--text-secondary)' }}>Variable: </strong>
            <span style={{ color: 'var(--text-main)' }}>Diagnóstico vehicular</span>
          </div>
          <div>
            <strong style={{ color: 'var(--text-secondary)' }}>Dimensión: </strong>
            <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{infoFicha.dimension}</span>
          </div>
          <div>
            <strong style={{ color: 'var(--text-secondary)' }}>Indicador: </strong>
            <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{infoFicha.indicador}</span>
          </div>
          <div>
            <strong style={{ color: 'var(--text-secondary)' }}>Unidad de Medida: </strong>
            <span style={{ color: 'var(--text-main)' }}>{infoFicha.medida}</span>
          </div>
          <div style={{ gridColumn: '1 / -1' }}>
            <strong style={{ color: 'var(--text-secondary)' }}>Fórmula Oficial: </strong>
            <code
              style={{
                backgroundColor: '#f8fafc',
                padding: '3px 8px',
                borderRadius: '4px',
                border: '1px solid #e2e8f0',
                color: '#1e293b',
                fontWeight: 600,
              }}
            >
              {infoFicha.formula}
            </code>
          </div>
        </div>

        {/* 2. Tabla Modular de Datos de la Ficha */}
        <div style={{ overflowX: 'auto' }}>
          <TesisTablasFichas
            fase={fase}
            fichaId={fichaId}
            preCasos={preCasos}
            postCasos={postCasos}
            casosActivos={casosActivos}
            preAciertos={preAciertos}
            postAciertos={postAciertos}
            prePPCF={prePPCF}
            postPPCF={postPPCF}
            preCompletos={preCompletos}
            postCompletos={postCompletos}
            prePRDC={prePRDC}
            postPRDC={postPRDC}
            preTiempoSuma={preTiempoSuma}
            postTiempoSuma={postTiempoSuma}
            preTPRD={preTPRD}
            postTPRD={postTPRD}
          />
        </div>
      </Card>
    </div>
  );
};
