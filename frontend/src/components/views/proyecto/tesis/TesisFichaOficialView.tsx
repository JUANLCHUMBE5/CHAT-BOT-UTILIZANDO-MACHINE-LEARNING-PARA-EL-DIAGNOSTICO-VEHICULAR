import React, { useState } from 'react';
import { Card } from '../../../common/Card';
import { ErrorBoundary } from '../../../common/ErrorBoundary';
import type { RegistroTesis } from '../../../../data/fichasTesisData';
import { TesisTablasFichas } from './TesisTablasFichas';

export type FichaId = 'ficha1' | 'ficha2' | 'ficha3';
export type FaseVista = 'pre' | 'post';

interface TesisFichaOficialViewProps {
  fichaId: FichaId;
  casosReales?: RegistroTesis[];
}

export const TesisFichaOficialView: React.FC<TesisFichaOficialViewProps> = ({
  fichaId,
  casosReales = [],
}) => {
  const [fase, setFase] = useState<FaseVista>('pre');

  const preCasos = casosReales.filter((c) => (c.fase || '').toLowerCase().includes('pre'));
  const postCasos = casosReales.filter((c) => (c.fase || '').toLowerCase().includes('post'));
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
  const preTiempoSuma = preCasos.reduce((acc, c) => acc + (Number(c.tiempo_diagnostico_minutos) || 0), 0);
  const postTiempoSuma = postCasos.reduce((acc, c) => acc + (Number(c.tiempo_diagnostico_minutos) || 0), 0);
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
      formula: 'PRDC = (RC / TRE) × 100  [RC: Registros con 8 campos completos, TRE: Total registros evaluados]',
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

  const resumenIndicadorFase = () => {
    if (fichaId === 'ficha1') {
      const valor = fase === 'pre' ? prePPCF : postPPCF;
      const aciertos = fase === 'pre' ? preAciertos : postAciertos;
      return (
        <span style={{ fontWeight: 700, color: 'var(--primary)' }}>
          PPCF: {casosActivos.length > 0 ? `${valor.toFixed(1)}%` : '—'} ({aciertos}/{casosActivos.length} aciertos)
        </span>
      );
    }
    if (fichaId === 'ficha2') {
      const valor = fase === 'pre' ? prePRDC : postPRDC;
      const completos = fase === 'pre' ? preCompletos : postCompletos;
      return (
        <span style={{ fontWeight: 700, color: 'var(--primary)' }}>
          PRDC: {casosActivos.length > 0 ? `${valor.toFixed(1)}%` : '—'} ({completos}/{casosActivos.length} con 8 campos)
        </span>
      );
    }
    const valor = fase === 'pre' ? preTPRD : postTPRD;
    const suma = fase === 'pre' ? preTiempoSuma : postTiempoSuma;
    return (
      <span style={{ fontWeight: 700, color: 'var(--primary)' }}>
        TPRD: {casosActivos.length > 0 ? `${valor.toFixed(1)} min` : '—'} (total {suma} min)
      </span>
    );
  };

  return (
    <ErrorBoundary fallbackTitle="Error al visualizar formato de Fichas Oficiales">
      <div className="notranslate" translate="no" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <Card style={{ padding: 0, overflow: 'hidden', border: '1px solid var(--border-color)' }}>
          {/* Encabezado Oficial del Instrumento */}
          <div
            style={{
              padding: '12px 18px',
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
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  · CARTER MOTOR'S E.I.R.L.
                </span>
              </div>
              <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 800, color: 'var(--text-main)' }}>
                {infoFicha.tituloFicha}
              </h3>
            </div>

            {/* Selector de Fase de Prueba */}
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
                onClick={() => setFase('pre')}
                style={{
                  padding: '6px 12px',
                  fontSize: '11.5px',
                  fontWeight: 700,
                  borderRadius: '6px',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: fase === 'pre' ? '#ffffff' : 'transparent',
                  color: fase === 'pre' ? '#166534' : 'var(--text-muted)',
                  boxShadow: fase === 'pre' ? '0 1px 2px rgba(0,0,0,0.08)' : 'none',
                  transition: 'all 0.15s ease',
                }}
              >
                Pre-test ({preCasos.length}/30)
              </button>

              <button
                type="button"
                onClick={() => setFase('post')}
                style={{
                  padding: '6px 12px',
                  fontSize: '11.5px',
                  fontWeight: 700,
                  borderRadius: '6px',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: fase === 'post' ? '#ffffff' : 'transparent',
                  color: fase === 'post' ? 'var(--primary)' : 'var(--text-muted)',
                  boxShadow: fase === 'post' ? '0 1px 2px rgba(0,0,0,0.08)' : 'none',
                  transition: 'all 0.15s ease',
                }}
              >
                Post-test ({postCasos.length}/30)
              </button>
            </div>
          </div>

          {/* Fila Compacta de Metadatos de la Variable Dependiente */}
          <div
            style={{
              padding: '10px 18px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px',
              fontSize: '12px',
              backgroundColor: '#ffffff',
              borderBottom: '1px solid var(--border-color)',
            }}
          >
            <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
              <div>
                <strong style={{ color: 'var(--text-secondary)' }}>Dimensión: </strong>
                <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{infoFicha.dimension}</span>
              </div>
              <div>
                <strong style={{ color: 'var(--text-secondary)' }}>Indicador: </strong>
                <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>{infoFicha.indicador}</span>
              </div>
              <div>
                <strong style={{ color: 'var(--text-secondary)' }}>Fórmula: </strong>
                <code
                  style={{
                    backgroundColor: '#f8fafc',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    border: '1px solid #e2e8f0',
                    fontSize: '11px',
                  }}
                >
                  {infoFicha.formula}
                </code>
              </div>
            </div>

            <div style={{ fontSize: '12px' }}>
              <span style={{ color: 'var(--text-secondary)', marginRight: '6px' }}>Resultado {fase === 'pre' ? 'Pre-test' : 'Post-test'}:</span>
              {resumenIndicadorFase()}
            </div>
          </div>

          {/* Tabla de Datos de la Ficha */}
          <div style={{ overflowX: 'auto' }}>
            <TesisTablasFichas
              fase={fase}
              fichaId={fichaId}
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
    </ErrorBoundary>
  );
};
