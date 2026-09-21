import React from 'react';
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import { Card } from '../../common/Card';
import type { ResumenMetricas } from '../../../types';
import {
  calcularVariacion,
  type PeriodosComparativa,
} from '../../../utils/dashboardComparador';

interface VehiculosPorDiaChartProps {
  metricasActuales: ResumenMetricas;
  metricasAnteriores: ResumenMetricas | null;
  periodos: PeriodosComparativa;
}

export const VehiculosPorDiaChart: React.FC<VehiculosPorDiaChartProps> = ({
  metricasActuales,
  metricasAnteriores,
  periodos,
}) => {
  const actividad = metricasActuales.actividad_diaria || [];
  const totalActual =
    metricasActuales.diagnosticos_realizados ?? metricasActuales.diagnosticos_mes ?? 0;
  const totalAnterior =
    metricasAnteriores
      ? (metricasAnteriores.diagnosticos_realizados ?? metricasAnteriores.diagnosticos_mes ?? 0)
      : null;

  const variacion = calcularVariacion(totalActual, totalAnterior);
  const tieneDatos = actividad.some((d) => d.cantidad > 0);

  return (
    <Card className="dashboard-chart-card" style={{ padding: '16px 18px', overflow: 'hidden' }}>
      {/* Header del gráfico con comparativa */}
      <div className="chart-header-row">
        <div>
          <h3 style={{ fontSize: '14px', fontWeight: 800, margin: 0, color: 'var(--text-main)' }}>
            Vehículos atendidos por día
          </h3>
          <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
            Distribución diaria de ingresos a diagnóstico
          </p>
        </div>

        {/* Resumen comparativo */}
        <div className="chart-comparison-badge-container">
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '12.5px', fontWeight: 800, color: 'var(--text-main)' }}>
              {totalActual} <span style={{ fontSize: '10.5px', fontWeight: 500, color: 'var(--text-muted)' }}>vehículos</span>
            </span>
            {totalAnterior !== null && (
              <span style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted)' }}>
                Ant: {totalAnterior}
              </span>
            )}
          </div>

          {periodos.anterior && !variacion.neutra && (
            <span
              style={{
                fontSize: '10.5px',
                fontWeight: 700,
                padding: '2px 7px',
                borderRadius: '9999px',
                backgroundColor: variacion.positiva ? 'rgba(34, 197, 94, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                color: variacion.positiva ? '#15803d' : '#b91c1c',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '2px',
              }}
            >
              {variacion.positiva ? '↑' : '↓'} {variacion.texto}
            </span>
          )}
        </div>
      </div>

      {/* Gráfico Responsive */}
      <div style={{ width: '100%', height: 180, marginTop: '12px' }}>
        {tieneDatos ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={actividad}
              margin={{ top: 8, right: 6, left: -22, bottom: 4 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis
                dataKey="fecha"
                stroke="#94a3b8"
                fontSize={10}
                tickLine={false}
                axisLine={{ stroke: '#e2e8f0' }}
                interval="preserveStartEnd"
              />
              <YAxis
                stroke="#94a3b8"
                fontSize={10}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderColor: 'var(--border-color)',
                  borderRadius: '8px',
                  boxShadow: '0 4px 12px rgba(15, 23, 42, 0.08)',
                  fontSize: '11.5px',
                  padding: '6px 10px',
                }}
                formatter={(value: unknown) => [`${Number(value) || 0} vehículo(s)`, 'Atendidos']}

                labelFormatter={(label) => `Fecha: ${label}`}
              />

              <Bar
                dataKey="cantidad"
                fill="var(--primary, #f97316)"
                radius={[4, 4, 0, 0]}
                name="Vehículos"
                maxBarSize={28}
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div
            style={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: 'var(--bg-subtle, #f8fafc)',
              borderRadius: '8px',
              border: '1px dashed var(--border-color)',
              gap: '4px',
            }}
          >
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Sin registros en este período
            </span>
            <span style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>
              No se registraron diagnósticos entre {periodos.actual.inicio} y {periodos.actual.fin}
            </span>
          </div>
        )}
      </div>
    </Card>
  );
};
