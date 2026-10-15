import React from 'react';
import { CheckCircle2, XCircle } from 'lucide-react';
import type { RegistroTesis } from '../../../../data/fichasTesisData';
import type { FichaId, FaseVista } from './TesisFichaOficialView';

interface TesisTablasFichasProps {
  fase: FaseVista;
  fichaId: FichaId;
  casosActivos: RegistroTesis[];
  preAciertos: number;
  postAciertos: number;
  prePPCF: number | null;
  postPPCF: number | null;
  prePrediccionesEvaluadas: number;
  postPrediccionesEvaluadas: number;
  preCompletos: number;
  postCompletos: number;
  prePRDC: number | null;
  postPRDC: number | null;
  preRegistrosEvaluados: number;
  postRegistrosEvaluados: number;
  preTiempoSuma: number;
  postTiempoSuma: number;
  preTPRD: number | null;
  postTPRD: number | null;
  preTiemposEvaluados: number;
  postTiemposEvaluados: number;
}

export const TesisTablasFichas: React.FC<TesisTablasFichasProps> = ({
  fase,
  fichaId,
  casosActivos,
  preAciertos,
  postAciertos,
  prePPCF,
  postPPCF,
  prePrediccionesEvaluadas,
  postPrediccionesEvaluadas,
  preCompletos,
  postCompletos,
  prePRDC,
  postPRDC,
  preRegistrosEvaluados,
  postRegistrosEvaluados,
  preTiempoSuma,
  postTiempoSuma,
  preTPRD,
  postTPRD,
  preTiemposEvaluados,
  postTiemposEvaluados,
}) => {
  const prediccionesEvaluadas = fase === 'pre' ? prePrediccionesEvaluadas : postPrediccionesEvaluadas;
  const registrosEvaluados = fase === 'pre' ? preRegistrosEvaluados : postRegistrosEvaluados;
  const tiemposEvaluados = fase === 'pre' ? preTiemposEvaluados : postTiemposEvaluados;
  const cantidadCampos = (caso: RegistroTesis) =>
    caso.cantidad_campos_completos ?? (caso.campos_completos === 1 ? 8 : null);
  const resultadoPrediccion = (caso: RegistroTesis) =>
    caso.chatbot_prediccion?.trim() && caso.falla_real?.trim() &&
    (caso.prediccion_correcta === 0 || caso.prediccion_correcta === 1)
      ? caso.prediccion_correcta
      : null;
  if (fichaId === 'ficha1') {
    return (
      <table className="notranslate" translate="no" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}>
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
                <td style={{ padding: '10px 14px', textAlign: 'center', fontWeight: 600 }}>{resultadoPrediccion(caso) !== null ? 1 : 0}</td>
                <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                  {resultadoPrediccion(caso) === 1 ? (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', color: '#059669', fontWeight: 700 }}>
                      <CheckCircle2 size={13} /> 1
                    </span>
                  ) : resultadoPrediccion(caso) === 0 ? (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', color: '#dc2626', fontWeight: 700 }}>
                      <XCircle size={13} /> 0
                    </span>
                  ) : (
                    <span style={{ color: 'var(--text-muted)' }}>Pendiente</span>
                  )}
                </td>
                <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                  <span
                    style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontWeight: 700,
                      fontSize: '11px',
                      backgroundColor: resultadoPrediccion(caso) === 1 ? 'rgba(16, 185, 129, 0.12)' : resultadoPrediccion(caso) === 0 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(148, 163, 184, 0.12)',
                      color: resultadoPrediccion(caso) === 1 ? '#059669' : resultadoPrediccion(caso) === 0 ? '#dc2626' : 'var(--text-muted)',
                    }}
                  >
                    {resultadoPrediccion(caso) === 1 ? '100%' : resultadoPrediccion(caso) === 0 ? '0%' : 'Pendiente'}
                  </span>
                </td>
                <td style={{ padding: '10px 14px' }}>
                  <div style={{ color: 'var(--text-main)', fontWeight: 600 }}>
                    {caso.placa} · {caso.marca_modelo}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    Falla: <strong style={{ color: '#047857' }}>{caso.falla_real || 'Pendiente'}</strong> · Predicción: <em>{caso.chatbot_prediccion || 'Pendiente'}</em>
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
            <td style={{ padding: '12px 14px', textAlign: 'center' }}>{prediccionesEvaluadas}</td>
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
                PPCF = {(fase === 'pre' ? prePPCF : postPPCF) !== null ? (fase === 'pre' ? prePPCF : postPPCF)?.toFixed(1) : 'Pendiente'}%
              </span>
            </td>
            <td style={{ padding: '12px 14px', color: 'var(--text-secondary)', fontSize: '11.5px' }}>
              {prediccionesEvaluadas > 0
                ? `PPCF = ( ${fase === 'pre' ? preAciertos : postAciertos} / ${prediccionesEvaluadas} ) × 100`
                : 'Pendiente de casos en campo'}
            </td>
          </tr>
        </tfoot>
      </table>
    );
  }

  if (fichaId === 'ficha2') {
    return (
      <table className="notranslate" translate="no" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}>
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
                  ) : caso.campos_completos === 0 ? (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', color: '#d97706', fontWeight: 700 }}>
                      <XCircle size={13} /> 0
                    </span>
                  ) : (
                    <span style={{ color: 'var(--text-muted)' }}>Pendiente</span>
                  )}
                </td>
                <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                  <span
                    style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontWeight: 700,
                      fontSize: '11px',
                      backgroundColor: caso.campos_completos === 1 ? 'rgba(16, 185, 129, 0.12)' : caso.campos_completos === 0 ? 'rgba(217, 119, 6, 0.1)' : 'rgba(148, 163, 184, 0.12)',
                      color: caso.campos_completos === 1 ? '#059669' : caso.campos_completos === 0 ? '#d97706' : 'var(--text-muted)',
                    }}
                  >
                    {caso.campos_completos === 1 ? '100%' : caso.campos_completos === 0 ? '0%' : 'Pendiente'}
                  </span>
                </td>
                <td style={{ padding: '10px 14px' }}>
                  <div style={{ color: 'var(--text-main)', fontWeight: 600 }}>
                    {caso.placa} · {caso.marca_modelo}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    {caso.campos_completos === 1 ? '8/8 campos requeridos completos' : caso.campos_completos === 0 ? `${cantidadCampos(caso) ?? 'Incompleto; cantidad no disponible'}/8 campos completos` : 'Pendiente de evaluación de completitud'}
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
            <td style={{ padding: '12px 14px', textAlign: 'center' }}>{registrosEvaluados}</td>
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
                PRDC = {(fase === 'pre' ? prePRDC : postPRDC) !== null ? (fase === 'pre' ? prePRDC : postPRDC)?.toFixed(1) : 'Pendiente'}%
              </span>
            </td>
            <td style={{ padding: '12px 14px', color: 'var(--text-secondary)', fontSize: '11.5px' }}>
              {registrosEvaluados > 0
                ? `PRDC = ( ${fase === 'pre' ? preCompletos : postCompletos} / ${registrosEvaluados} ) × 100`
                : 'Pendiente de casos en campo'}
            </td>
          </tr>
        </tfoot>
      </table>
    );
  }

  // Ficha 3
  return (
    <table className="notranslate" translate="no" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}>
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
              <td style={{ padding: '10px 14px', textAlign: 'center', fontWeight: 600 }}>{caso.tiempo_diagnostico_minutos !== null && caso.tiempo_diagnostico_minutos > 0 ? 1 : 0}</td>
              <td style={{ padding: '10px 14px', textAlign: 'center', fontWeight: 700, color: 'var(--text-main)' }}>
                {caso.tiempo_diagnostico_minutos !== null && caso.tiempo_diagnostico_minutos > 0 ? `${caso.tiempo_diagnostico_minutos} min` : 'Pendiente'}
              </td>
              <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                <span
                  style={{
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontWeight: 700,
                    fontSize: '11px',
                  backgroundColor: caso.tiempo_diagnostico_minutos !== null && caso.tiempo_diagnostico_minutos > 0 ? (caso.tiempo_diagnostico_minutos <= 15 ? 'rgba(16, 185, 129, 0.12)' : 'rgba(234, 88, 12, 0.1)') : 'rgba(148, 163, 184, 0.12)',
                  color: caso.tiempo_diagnostico_minutos !== null && caso.tiempo_diagnostico_minutos > 0 ? (caso.tiempo_diagnostico_minutos <= 15 ? '#059669' : 'var(--primary)') : 'var(--text-muted)',
                  }}
                >
                  {caso.tiempo_diagnostico_minutos !== null && caso.tiempo_diagnostico_minutos > 0 ? `${caso.tiempo_diagnostico_minutos} min` : 'Pendiente'}
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
            <td style={{ padding: '12px 14px', textAlign: 'center' }}>{tiemposEvaluados}</td>
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
              TPRD = {(fase === 'pre' ? preTPRD : postTPRD) !== null ? (fase === 'pre' ? preTPRD : postTPRD)?.toFixed(1) : 'Pendiente'} min
            </span>
          </td>
          <td style={{ padding: '12px 14px', color: 'var(--text-secondary)', fontSize: '11.5px' }}>
            {tiemposEvaluados > 0
              ? `TPRD = ( ${fase === 'pre' ? preTiempoSuma : postTiempoSuma} min / ${tiemposEvaluados} tiempos medidos ) = ${(fase === 'pre' ? preTPRD : postTPRD)?.toFixed(1)} min`
              : 'Pendiente de casos en campo'}
          </td>
        </tr>
      </tfoot>
    </table>
  );
};
