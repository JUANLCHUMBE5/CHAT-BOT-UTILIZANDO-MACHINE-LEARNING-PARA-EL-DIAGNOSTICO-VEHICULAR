import React from 'react';
import { CheckCircle2, XCircle } from 'lucide-react';
import type { RegistroTesis } from '../../../../data/fichasTesisData';
import type { FichaId, FaseVista } from './TesisFichaOficialView';

interface TesisTablasFichasProps {
  fase: FaseVista;
  fichaId: FichaId;
  preCasos: RegistroTesis[];
  postCasos: RegistroTesis[];
  casosActivos: RegistroTesis[];
  preAciertos: number;
  postAciertos: number;
  prePPCF: number;
  postPPCF: number;
  preCompletos: number;
  postCompletos: number;
  prePRDC: number;
  postPRDC: number;
  preTiempoSuma: number;
  postTiempoSuma: number;
  preTPRD: number;
  postTPRD: number;
}

export const TesisTablasFichas: React.FC<TesisTablasFichasProps> = ({
  fase,
  fichaId,
  preCasos,
  postCasos,
  casosActivos,
  preAciertos,
  postAciertos,
  prePPCF,
  postPPCF,
  preCompletos,
  postCompletos,
  prePRDC,
  postPRDC,
  preTiempoSuma,
  postTiempoSuma,
  preTPRD,
  postTPRD,
}) => {
  if (fase === 'contraste') {
    return (
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}>
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
            <th style={{ padding: '10px 14px' }}># Caso</th>
            <th style={{ padding: '10px 14px' }}>Vehículo y Falla Real</th>
            <th style={{ padding: '10px 14px' }}>Pre-test (Manual)</th>
            <th style={{ padding: '10px 14px' }}>Post-test (CarBot AI)</th>
            <th style={{ padding: '10px 14px', textAlign: 'center' }}>Efecto / Variación</th>
          </tr>
        </thead>
        <tbody>
          {preCasos.length === 0 ? (
            <tr>
              <td colSpan={5} style={{ padding: '24px 14px', textAlign: 'center', color: 'var(--text-muted)' }}>
                No hay casos reales de pre-test registrados aún para contrastar con post-test.
              </td>
            </tr>
          ) : (
            preCasos.map((pre, idx) => {
              const post = postCasos[idx] || pre;
              return (
                <tr
                  key={pre.item}
                  className="table-row-hover"
                  style={{ borderBottom: '1px solid var(--border-color)', backgroundColor: '#fff' }}
                >
                  <td style={{ padding: '10px 14px', fontWeight: 700, color: 'var(--text-muted)' }}>
                    #{idx + 1}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                      {pre.placa} · {pre.marca_modelo}
                    </div>
                    <div style={{ fontSize: '11px', color: '#047857' }}>Falla: {pre.falla_real}</div>
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    {fichaId === 'ficha1' && (
                      <span style={{ color: pre.prediccion_correcta === 1 ? '#059669' : '#dc2626', fontWeight: 600 }}>
                        {pre.prediccion_correcta === 1 ? 'Correcto (1)' : 'Desacierto (0)'}
                      </span>
                    )}
                    {fichaId === 'ficha2' && (
                      <span style={{ color: pre.campos_completos === 1 ? '#059669' : '#d97706', fontWeight: 600 }}>
                        {pre.campos_completos === 1 ? 'Completo (8/8)' : 'Incompleto'}
                      </span>
                    )}
                    {fichaId === 'ficha3' && (
                      <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                        {pre.tiempo_diagnostico_minutos} min
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '10px 14px', backgroundColor: 'rgba(59, 130, 246, 0.02)' }}>
                    {fichaId === 'ficha1' && (
                      <span style={{ color: post.prediccion_correcta === 1 ? '#059669' : '#dc2626', fontWeight: 700 }}>
                        {post.prediccion_correcta === 1 ? 'Correcto (1)' : 'Desacierto (0)'}
                      </span>
                    )}
                    {fichaId === 'ficha2' && (
                      <span style={{ color: post.campos_completos === 1 ? '#059669' : '#d97706', fontWeight: 700 }}>
                        {post.campos_completos === 1 ? 'Completo (8/8)' : 'Incompleto'}
                      </span>
                    )}
                    {fichaId === 'ficha3' && (
                      <span style={{ fontWeight: 700, color: 'var(--primary)' }}>
                        {post.tiempo_diagnostico_minutos} min
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                    {fichaId === 'ficha1' && (
                      pre.prediccion_correcta === 0 && post.prediccion_correcta === 1 ? (
                        <span style={{ color: '#059669', fontWeight: 700 }}>+ Corrigió falla</span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>Mantiene</span>
                      )
                    )}
                    {fichaId === 'ficha2' && (
                      pre.campos_completos < post.campos_completos ? (
                        <span style={{ color: '#059669', fontWeight: 700 }}>+ Estandarizó</span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>Mantiene</span>
                      )
                    )}
                    {fichaId === 'ficha3' && (
                      <span style={{ color: '#059669', fontWeight: 700 }}>
                        -{pre.tiempo_diagnostico_minutos - post.tiempo_diagnostico_minutos} min
                      </span>
                    )}
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    );
  }

  if (fichaId === 'ficha1') {
    return (
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}>
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
            <th style={{ padding: '10px 14px', width: '50px' }}>Ítem</th>
            <th style={{ padding: '10px 14px', width: '90px' }}>Fecha</th>
            <th style={{ padding: '10px 14px', textAlign: 'center' }}>N.° vehículos atendidos</th>
            <th style={{ padding: '10px 14px', textAlign: 'center' }}>Total predicciones realizadas</th>
            <th style={{ padding: '10px 14px', textAlign: 'center' }}>N.° predicciones correctas</th>
            <th style={{ padding: '10px 14px', textAlign: 'center' }}>% Predicción correcta</th>
            <th style={{ padding: '10px 14px' }}>Vehículo / Diagnóstico</th>
          </tr>
        </thead>
        <tbody>
          {casosActivos.length === 0 ? (
            <tr>
              <td colSpan={7} style={{ padding: '24px 14px', textAlign: 'center', color: 'var(--text-muted)' }}>
                No hay casos reales de {fase === 'pre' ? 'Pre-test' : 'Post-test'} registrados aún en el sistema.
              </td>
            </tr>
          ) : (
            casosActivos.map((caso, idx) => (
              <tr
                key={caso.item}
                className="table-row-hover"
                style={{ borderBottom: '1px solid var(--border-color)', backgroundColor: '#fff' }}
              >
                <td style={{ padding: '10px 14px', fontWeight: 700, color: 'var(--text-muted)' }}>
                  {idx + 1}
                </td>
                <td style={{ padding: '10px 14px', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
                  {caso.fecha}
                </td>
                <td style={{ padding: '10px 14px', textAlign: 'center', fontWeight: 600 }}>1</td>
                <td style={{ padding: '10px 14px', textAlign: 'center', fontWeight: 600 }}>1</td>
                <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                  {caso.prediccion_correcta === 1 ? (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', color: '#059669', fontWeight: 700 }}>
                      <CheckCircle2 size={13} /> 1
                    </span>
                  ) : (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', color: '#dc2626', fontWeight: 700 }}>
                      <XCircle size={13} /> 0
                    </span>
                  )}
                </td>
                <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                  <span
                    style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontWeight: 700,
                      fontSize: '11px',
                      backgroundColor: caso.prediccion_correcta === 1 ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.1)',
                      color: caso.prediccion_correcta === 1 ? '#059669' : '#dc2626',
                    }}
                  >
                    {caso.prediccion_correcta === 1 ? '100%' : '0%'}
                  </span>
                </td>
                <td style={{ padding: '10px 14px' }}>
                  <div style={{ color: 'var(--text-main)', fontWeight: 600 }}>
                    {caso.placa} · {caso.marca_modelo}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    Falla: <strong style={{ color: '#047857' }}>{caso.falla_real}</strong> · Predicción: <em>{caso.chatbot_prediccion}</em>
                  </div>
                </td>
              </tr>
            ))
          )}
        </tbody>
        <tfoot>
          <tr
            style={{
              backgroundColor: '#f8fafc',
              fontWeight: 700,
              fontSize: '12px',
              borderTop: '2px solid var(--border-color)',
            }}
          >
            <td colSpan={2} style={{ padding: '12px 14px' }}>
              TOTAL {fase.toUpperCase()}:
            </td>
            <td style={{ padding: '12px 14px', textAlign: 'center' }}>{casosActivos.length}</td>
            <td style={{ padding: '12px 14px', textAlign: 'center' }}>{casosActivos.length}</td>
            <td style={{ padding: '12px 14px', textAlign: 'center', color: 'var(--primary)', fontWeight: 800 }}>
              {fase === 'pre' ? preAciertos : postAciertos}
            </td>
            <td style={{ padding: '12px 14px', textAlign: 'center' }}>
              <span
                style={{
                  padding: '3px 10px',
                  borderRadius: '4px',
                  backgroundColor: 'rgba(234, 88, 12, 0.15)',
                  color: 'var(--primary)',
                  fontWeight: 800,
                  fontSize: '12px',
                }}
              >
                PPCF = {casosActivos.length > 0 ? (fase === 'pre' ? prePPCF.toFixed(1) : postPPCF.toFixed(1)) : '0.0'}%
              </span>
            </td>
            <td style={{ padding: '12px 14px', color: 'var(--text-secondary)', fontSize: '11.5px' }}>
              {casosActivos.length > 0
                ? `PPCF = ( ${fase === 'pre' ? preAciertos : postAciertos} / ${casosActivos.length} ) × 100`
                : 'Pendiente de casos en campo'}
            </td>
          </tr>
        </tfoot>
      </table>
    );
  }

  if (fichaId === 'ficha2') {
    return (
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}>
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
            <th style={{ padding: '10px 14px', width: '50px' }}>Ítem</th>
            <th style={{ padding: '10px 14px', width: '90px' }}>Fecha</th>
            <th style={{ padding: '10px 14px', textAlign: 'center' }}>Total registros evaluados (TRE)</th>
            <th style={{ padding: '10px 14px', textAlign: 'center' }}>Registros con 8 campos completos (RC)</th>
            <th style={{ padding: '10px 14px', textAlign: 'center' }}>% Registros completos PRDC = (RC ÷ TRE) × 100</th>
            <th style={{ padding: '10px 14px' }}>Detalle de Registro</th>
          </tr>
        </thead>
        <tbody>
          {casosActivos.length === 0 ? (
            <tr>
              <td colSpan={6} style={{ padding: '24px 14px', textAlign: 'center', color: 'var(--text-muted)' }}>
                No hay registros reales de {fase === 'pre' ? 'Pre-test' : 'Post-test'} registrados aún en el sistema.
              </td>
            </tr>
          ) : (
            casosActivos.map((caso, idx) => (
              <tr
                key={caso.item}
                className="table-row-hover"
                style={{ borderBottom: '1px solid var(--border-color)', backgroundColor: '#fff' }}
              >
                <td style={{ padding: '10px 14px', fontWeight: 700, color: 'var(--text-muted)' }}>
                  {idx + 1}
                </td>
                <td style={{ padding: '10px 14px', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
                  {caso.fecha}
                </td>
                <td style={{ padding: '10px 14px', textAlign: 'center', fontWeight: 600 }}>1</td>
                <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                  {caso.campos_completos === 1 ? (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', color: '#059669', fontWeight: 700 }}>
                      <CheckCircle2 size={13} /> 1
                    </span>
                  ) : (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', color: '#d97706', fontWeight: 700 }}>
                      <XCircle size={13} /> 0
                    </span>
                  )}
                </td>
                <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                  <span
                    style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontWeight: 700,
                      fontSize: '11px',
                      backgroundColor: caso.campos_completos === 1 ? 'rgba(16, 185, 129, 0.12)' : 'rgba(217, 119, 6, 0.1)',
                      color: caso.campos_completos === 1 ? '#059669' : '#d97706',
                    }}
                  >
                    {caso.campos_completos === 1 ? '100%' : '0%'}
                  </span>
                </td>
                <td style={{ padding: '10px 14px' }}>
                  <div style={{ color: 'var(--text-main)', fontWeight: 600 }}>
                    {caso.placa} · {caso.marca_modelo}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    {caso.campos_completos === 1 ? '8/8 campos requeridos completos' : 'Faltan campos de trazabilidad en ficha manual'}
                  </div>
                </td>
              </tr>
            ))
          )}
        </tbody>
        <tfoot>
          <tr
            style={{
              backgroundColor: '#f8fafc',
              fontWeight: 700,
              fontSize: '12px',
              borderTop: '2px solid var(--border-color)',
            }}
          >
            <td colSpan={2} style={{ padding: '12px 14px' }}>
              TOTAL {fase.toUpperCase()}:
            </td>
            <td style={{ padding: '12px 14px', textAlign: 'center' }}>{casosActivos.length}</td>
            <td style={{ padding: '12px 14px', textAlign: 'center', color: 'var(--primary)', fontWeight: 800 }}>
              {fase === 'pre' ? preCompletos : postCompletos}
            </td>
            <td style={{ padding: '12px 14px', textAlign: 'center' }}>
              <span
                style={{
                  padding: '3px 10px',
                  borderRadius: '4px',
                  backgroundColor: 'rgba(234, 88, 12, 0.15)',
                  color: 'var(--primary)',
                  fontWeight: 800,
                  fontSize: '12px',
                }}
              >
                PRDC = {casosActivos.length > 0 ? (fase === 'pre' ? prePRDC.toFixed(1) : postPRDC.toFixed(1)) : '0.0'}%
              </span>
            </td>
            <td style={{ padding: '12px 14px', color: 'var(--text-secondary)', fontSize: '11.5px' }}>
              {casosActivos.length > 0
                ? `RDC = ( ${fase === 'pre' ? preCompletos : postCompletos} / ${casosActivos.length} ) × 100`
                : 'Pendiente de casos en campo'}
            </td>
          </tr>
        </tfoot>
      </table>
    );
  }

  // Ficha 3
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}>
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
          <th style={{ padding: '10px 14px', width: '50px' }}>Ítem</th>
          <th style={{ padding: '10px 14px', width: '90px' }}>Fecha</th>
          <th style={{ padding: '10px 14px', textAlign: 'center' }}>N.° de diagnósticos evaluados</th>
          <th style={{ padding: '10px 14px', textAlign: 'center' }}>Suma total de tiempos de respuesta (min)</th>
          <th style={{ padding: '10px 14px', textAlign: 'center' }}>Tiempo promedio de respuesta diagnóstica</th>
          <th style={{ padding: '10px 14px' }}>Vehículo / Síntoma</th>
        </tr>
      </thead>
      <tbody>
        {casosActivos.length === 0 ? (
          <tr>
            <td colSpan={6} style={{ padding: '24px 14px', textAlign: 'center', color: 'var(--text-muted)' }}>
              No hay registros reales de {fase === 'pre' ? 'Pre-test' : 'Post-test'} registrados aún en el sistema.
            </td>
          </tr>
        ) : (
          casosActivos.map((caso, idx) => (
            <tr
              key={caso.item}
              className="table-row-hover"
              style={{ borderBottom: '1px solid var(--border-color)', backgroundColor: '#fff' }}
            >
              <td style={{ padding: '10px 14px', fontWeight: 700, color: 'var(--text-muted)' }}>
                {idx + 1}
              </td>
              <td style={{ padding: '10px 14px', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
                {caso.fecha}
              </td>
              <td style={{ padding: '10px 14px', textAlign: 'center', fontWeight: 600 }}>1</td>
              <td style={{ padding: '10px 14px', textAlign: 'center', fontWeight: 700, color: 'var(--text-main)' }}>
                {caso.tiempo_diagnostico_minutos} min
              </td>
              <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                <span
                  style={{
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontWeight: 700,
                    fontSize: '11px',
                    backgroundColor: caso.tiempo_diagnostico_minutos <= 15 ? 'rgba(16, 185, 129, 0.12)' : 'rgba(234, 88, 12, 0.1)',
                    color: caso.tiempo_diagnostico_minutos <= 15 ? '#059669' : 'var(--primary)',
                  }}
                >
                  {caso.tiempo_diagnostico_minutos} min
                </span>
              </td>
              <td style={{ padding: '10px 14px' }}>
                <div style={{ color: 'var(--text-main)', fontWeight: 600 }}>
                  {caso.placa} · {caso.marca_modelo}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '300px' }}>
                  {caso.sintoma}
                </div>
              </td>
            </tr>
          ))
        )}
      </tbody>
      <tfoot>
        <tr
          style={{
            backgroundColor: '#f8fafc',
            fontWeight: 700,
            fontSize: '12px',
            borderTop: '2px solid var(--border-color)',
          }}
        >
          <td colSpan={2} style={{ padding: '12px 14px' }}>
            TOTAL {fase.toUpperCase()}:
          </td>
          <td style={{ padding: '12px 14px', textAlign: 'center' }}>{casosActivos.length}</td>
          <td style={{ padding: '12px 14px', textAlign: 'center', color: 'var(--primary)', fontWeight: 800 }}>
            {fase === 'pre' ? preTiempoSuma : postTiempoSuma} min
          </td>
          <td style={{ padding: '12px 14px', textAlign: 'center' }}>
            <span
              style={{
                padding: '3px 10px',
                borderRadius: '4px',
                backgroundColor: 'rgba(234, 88, 12, 0.15)',
                color: 'var(--primary)',
                fontWeight: 800,
                fontSize: '12px',
              }}
            >
              TPRD = {casosActivos.length > 0 ? (fase === 'pre' ? preTPRD.toFixed(1) : postTPRD.toFixed(1)) : '0.0'} min
            </span>
          </td>
          <td style={{ padding: '12px 14px', color: 'var(--text-secondary)', fontSize: '11.5px' }}>
            {casosActivos.length > 0
              ? `TPRD = ( ${fase === 'pre' ? preTiempoSuma : postTiempoSuma} min / ${casosActivos.length} ) = ${fase === 'pre' ? preTPRD.toFixed(1) : postTPRD.toFixed(1)} min`
              : 'Pendiente de casos en campo'}
          </td>
        </tr>
      </tfoot>
    </table>
  );
};
