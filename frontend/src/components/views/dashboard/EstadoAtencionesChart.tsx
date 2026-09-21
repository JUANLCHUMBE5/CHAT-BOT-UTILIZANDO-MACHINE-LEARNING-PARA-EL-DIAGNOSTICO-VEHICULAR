import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Card } from '../../common/Card';
import type { ResumenMetricas } from '../../../types';

interface EstadoAtencionesChartProps {
  metricas: ResumenMetricas;
}

const ESTADOS_COLORES: Record<string, string> = {
  completados: '#10b981', // Verde
  pendientes: '#f59e0b',  // Ámbar
  en_proceso: '#3b82f6',  // Azul
  otros: '#94a3b8',       // Gris pizarra
};

export const EstadoAtencionesChart: React.FC<EstadoAtencionesChartProps> = ({ metricas }) => {
  const total = metricas.diagnosticos_realizados ?? metricas.diagnosticos_mes ?? 0;
  const pctConfirmados = metricas.porcentaje_confirmados ?? 0;

  // Cálculo de conteos reales
  const completados = total > 0 ? Math.round((pctConfirmados / 100) * total) : 0;
  const pendientes = metricas.diagnosticos_pendientes ?? 0;

  // Casos en proceso / revisión activa
  const enProceso = Math.max(
    0,
    total - completados - pendientes
  );

  const dataEstados = [
    {
      id: 'completados',
      nombre: 'Completados',
      cantidad: completados,
      porcentaje: total > 0 ? Math.round((completados / total) * 100) : 0,
      color: ESTADOS_COLORES.completados,
    },
    {
      id: 'pendientes',
      nombre: 'Pendientes',
      cantidad: pendientes,
      porcentaje: total > 0 ? Math.round((pendientes / total) * 100) : 0,
      color: ESTADOS_COLORES.pendientes,
    },
    {
      id: 'en_proceso',
      nombre: 'En proceso',
      cantidad: enProceso,
      porcentaje: total > 0 ? Math.max(0, 100 - Math.round((completados / total) * 100) - Math.round((pendientes / total) * 100)) : 0,
      color: ESTADOS_COLORES.en_proceso,
    },
  ];

  const tieneDatos = total > 0;

  return (
    <Card className="dashboard-chart-card" style={{ padding: '16px 18px', overflow: 'hidden' }}>
      <div style={{ marginBottom: '10px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 800, margin: 0, color: 'var(--text-main)' }}>
          Estado de atenciones
        </h3>
        <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
          Seguimiento de resolución en taller
        </p>
      </div>

      <div className="estado-atenciones-container">
        {/* Gráfico Donut con Centro Informativo */}
        <div style={{ position: 'relative', width: '130px', height: '130px', margin: '0 auto', flexShrink: 0 }}>
          {tieneDatos ? (
            <>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={dataEstados}
                    cx="50%"
                    cy="50%"
                    innerRadius={38}
                    outerRadius={56}
                    paddingAngle={3}
                    dataKey="cantidad"
                    nameKey="nombre"
                  >
                    {dataEstados.map((entry) => (
                      <Cell key={`cell-${entry.id}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      borderColor: 'var(--border-color)',
                      borderRadius: '8px',
                      boxShadow: '0 4px 12px rgba(15, 23, 42, 0.08)',
                      fontSize: '11px',
                    }}
                    formatter={(value: unknown, name: unknown) => [
                      `${Number(value) || 0} (${total > 0 ? Math.round(((Number(value) || 0) / total) * 100) : 0}%)`,
                      String(name ?? ''),
                    ]}

                  />

                </PieChart>
              </ResponsiveContainer>
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  pointerEvents: 'none',
                }}
              >
                <span style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-main)', lineHeight: 1 }}>
                  {total}
                </span>
                <span style={{ fontSize: '9px', fontWeight: 600, color: 'var(--text-muted)', marginTop: '2px' }}>
                  Vehículos
                </span>
              </div>
            </>
          ) : (
            <div
              style={{
                width: '100%',
                height: '100%',
                borderRadius: '50%',
                border: '4px dashed #e2e8f0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>0</span>
            </div>
          )}
        </div>

        {/* Leyenda y Desglose Detallado */}
        <div className="estado-atenciones-legend">
          {dataEstados.map((estado) => (
            <div
              key={estado.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '5px 8px',
                borderRadius: '6px',
                backgroundColor: 'var(--bg-subtle, #f8fafc)',
                fontSize: '11.5px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                <span
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: estado.color,
                    flexShrink: 0,
                  }}
                  aria-hidden="true"
                />
                <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                  {estado.nombre}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontWeight: 700, color: 'var(--text-main)' }}>
                  {estado.cantidad}
                </span>
                <span
                  style={{
                    fontSize: '10.5px',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    minWidth: '28px',
                    textAlign: 'right',
                  }}
                >
                  {estado.porcentaje}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};
