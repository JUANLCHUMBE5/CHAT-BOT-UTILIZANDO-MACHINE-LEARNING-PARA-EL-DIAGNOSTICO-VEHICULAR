import React from 'react';
import { Card } from '../../../common/Card';
import type { FichaTipo, FaseTipo } from '../../../../hooks/useTesisStats';

interface TesisCasoRegistro {
  item: number;
  fase: string;
  fecha: string;
  placa: string;
  marca_modelo: string;
  sintoma: string;
  falla_real: string;
  chatbot_prediccion: string;
  campos_completos: number;
  tiempo_diagnostico_minutos: number;
  prediccion_correcta: number;
}

interface TesisCasosTableProps {
  casosVisibles: TesisCasoRegistro[];
  preCasos: TesisCasoRegistro[];
  postCasos: TesisCasoRegistro[];
  fichaActiva: FichaTipo;
  faseActiva: FaseTipo;
}

export const TesisCasosTable: React.FC<TesisCasosTableProps> = ({
  casosVisibles,
  preCasos,
  postCasos,
  fichaActiva,
  faseActiva,
}) => {
  return (
    <Card style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{ overflowX: 'auto' }}>
        {faseActiva === 'contraste' ? (
          /* Tabla de contraste pareado caso a caso (1..30) */
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--bg-subtle)', borderBottom: '1px solid var(--border-color)', fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)' }}>
                <th style={{ padding: '10px 14px' }}>#</th>
                <th style={{ padding: '10px 14px' }}>Vehículo / Falla Real</th>
                <th style={{ padding: '10px 14px' }}>Pre-test (Manual)</th>
                <th style={{ padding: '10px 14px' }}>Post-test (CarBot AI)</th>
                <th style={{ padding: '10px 14px', textAlign: 'center' }}>Impacto Ficha 1</th>
                <th style={{ padding: '10px 14px', textAlign: 'center' }}>Impacto Ficha 2</th>
                <th style={{ padding: '10px 14px', textAlign: 'right' }}>Δ Tiempo Ficha 3</th>
              </tr>
            </thead>
            <tbody>
              {preCasos.map((pre, idx) => {
                const post = postCasos[idx] || pre;
                const deltaTiempo = pre.tiempo_diagnostico_minutos - post.tiempo_diagnostico_minutos;

                return (
                  <tr key={pre.item} className="table-row-hover" style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '10px 14px', fontWeight: 700, color: 'var(--text-muted)' }}>
                      #{idx + 1}
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <strong style={{ color: 'var(--text-main)' }}>{pre.placa}</strong> · {pre.marca_modelo}
                      <div style={{ fontSize: '11px', color: '#047857', marginTop: '2px' }}>{pre.falla_real}</div>
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <div>Acierto: {pre.prediccion_correcta === 1 ? '✅ Sí' : '❌ No'}</div>
                      <div style={{ color: 'var(--text-muted)' }}>{pre.tiempo_diagnostico_minutos} min · {pre.campos_completos}/1 campos</div>
                    </td>
                    <td style={{ padding: '10px 14px', backgroundColor: 'rgba(59, 130, 246, 0.03)' }}>
                      <div>Acierto: {post.prediccion_correcta === 1 ? '✅ Sí' : '❌ No'} ({post.chatbot_prediccion})</div>
                      <div style={{ color: 'var(--text-muted)' }}>{post.tiempo_diagnostico_minutos} min · {post.campos_completos}/1 campos</div>
                    </td>
                    <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                      {pre.prediccion_correcta === 0 && post.prediccion_correcta === 1 ? (
                        <span style={{ color: '#16a34a', fontWeight: 700 }}>+ Mejoró</span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>= Mantiene</span>
                      )}
                    </td>
                    <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                      {pre.campos_completos < post.campos_completos ? (
                        <span style={{ color: '#16a34a', fontWeight: 700 }}>+ Completo</span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>=</span>
                      )}
                    </td>
                    <td style={{ padding: '10px 14px', textAlign: 'right', fontWeight: 700, color: deltaTiempo > 0 ? '#16a34a' : 'var(--text-muted)' }}>
                      {deltaTiempo > 0 ? `-${deltaTiempo} min` : `${deltaTiempo} min`}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          /* Tabla normal de 30 casos */
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--bg-subtle)', borderBottom: '1px solid var(--border-color)', fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)' }}>
                <th style={{ padding: '10px 14px' }}>Item</th>
                <th style={{ padding: '10px 14px' }}>Fecha</th>
                <th style={{ padding: '10px 14px' }}>Placa</th>
                <th style={{ padding: '10px 14px' }}>Marca y Modelo</th>
                <th style={{ padding: '10px 14px' }}>Síntoma del Cliente</th>
                <th style={{ padding: '10px 14px' }}>Falla Real</th>
                <th style={{ padding: '10px 14px' }}>Predicción</th>
                <th style={{ padding: '10px 14px', textAlign: 'center' }}>
                  {fichaActiva === 'ficha1' ? 'Acierto (PPCF)' : fichaActiva === 'ficha2' ? 'Campos (PRDC)' : 'Tiempo (TPRD)'}
                </th>
              </tr>
            </thead>
            <tbody>
              {casosVisibles.map((caso) => (
                <tr key={caso.item} className="table-row-hover" style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '10px 14px', fontWeight: 700, color: 'var(--text-muted)' }}>
                    #{caso.item}
                  </td>
                  <td style={{ padding: '10px 14px', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
                    {caso.fecha}
                  </td>
                  <td style={{ padding: '10px 14px', fontWeight: 700, color: 'var(--text-main)' }}>
                    {caso.placa}
                  </td>
                  <td style={{ padding: '10px 14px', color: 'var(--text-secondary)' }}>
                    {caso.marca_modelo}
                  </td>
                  <td style={{ padding: '10px 14px', maxWidth: '200px' }}>
                    <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={caso.sintoma}>
                      "{caso.sintoma}"
                    </div>
                  </td>
                  <td style={{ padding: '10px 14px', color: '#047857', fontWeight: 600 }}>
                    {caso.falla_real}
                  </td>
                  <td style={{ padding: '10px 14px', color: 'var(--text-main)' }}>
                    {caso.chatbot_prediccion}
                  </td>
                  <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                    {fichaActiva === 'ficha1' ? (
                      caso.prediccion_correcta === 1 ? (
                        <span style={{ color: '#16a34a', fontWeight: 700 }}>1 (Correcto)</span>
                      ) : (
                        <span style={{ color: '#dc2626', fontWeight: 700 }}>0 (Error)</span>
                      )
                    ) : fichaActiva === 'ficha2' ? (
                      caso.campos_completos === 1 ? (
                        <span style={{ color: '#16a34a', fontWeight: 700 }}>1 (8/8)</span>
                      ) : (
                        <span style={{ color: '#dc2626', fontWeight: 700 }}>0 (Incompleto)</span>
                      )
                    ) : (
                      <span style={{ fontWeight: 700, color: 'var(--text-main)' }}>
                        {caso.tiempo_diagnostico_minutos} min
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Card>
  );
};
