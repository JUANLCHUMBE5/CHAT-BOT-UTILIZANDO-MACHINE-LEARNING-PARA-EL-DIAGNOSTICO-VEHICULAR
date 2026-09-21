import React from 'react';
import { Car, Clock, CheckCircle2, Timer } from 'lucide-react';
import { StatCard } from '../../common/StatCard';
import type { ResumenMetricas } from '../../../types';
import {
  calcularVariacion,
  calcularVariacionPendientes,
  type PeriodosComparativa,
} from '../../../utils/dashboardComparador';

interface DashboardKpisProps {
  metricasActuales: ResumenMetricas;
  metricasAnteriores: ResumenMetricas | null;
  periodos: PeriodosComparativa;
}

export const DashboardKpis: React.FC<DashboardKpisProps> = ({
  metricasActuales,
  metricasAnteriores,
  periodos,
}) => {
  // 1. Vehículos atendidos (diagnósticos realizados en el período)
  const totalActual =
    metricasActuales.diagnosticos_realizados ?? metricasActuales.diagnosticos_mes ?? 0;
  const totalAnterior =
    metricasAnteriores
      ? (metricasAnteriores.diagnosticos_realizados ?? metricasAnteriores.diagnosticos_mes ?? 0)
      : null;
  const variacionVehiculos = calcularVariacion(totalActual, totalAnterior);

  // 2. Diagnósticos pendientes
  const pendientesActual = metricasActuales.diagnosticos_pendientes ?? 0;
  const pendientesAnterior = metricasAnteriores?.diagnosticos_pendientes ?? null;
  const variacionPendientes = calcularVariacionPendientes(pendientesActual, pendientesAnterior);

  // 3. Diagnósticos completados (confirmados)
  const pctConfirmados = metricasActuales.porcentaje_confirmados ?? 0;
  const completadosActual = totalActual > 0 ? Math.round((pctConfirmados / 100) * totalActual) : 0;
  const completadosAnterior =
    totalAnterior !== null && totalAnterior > 0
      ? Math.round(((metricasAnteriores?.porcentaje_confirmados ?? 0) / 100) * totalAnterior)
      : null;
  const variacionCompletados = calcularVariacion(completadosActual, completadosAnterior);

  return (
    <section aria-label="Indicadores clave de rendimiento operativo" className="dashboard-kpis-grid">
      {/* 1. Vehículos Atendidos */}
      <StatCard
        title="Vehículos Atendidos"
        value={totalActual}
        subtitle={
          periodos.anterior
            ? `${totalAnterior ?? 0} en ${periodos.etiquetaAnterior}`
            : 'Período seleccionado'
        }
        icon={<Car size={18} aria-hidden="true" />}
        trend={
          periodos.anterior && !variacionVehiculos.neutra
            ? {
                text: variacionVehiculos.texto,
                positive: variacionVehiculos.positiva,
              }
            : undefined
        }
      />

      {/* 2. Diagnósticos Pendientes */}
      <StatCard
        title="Diagnósticos Pendientes"
        value={pendientesActual}
        subtitle={
          pendientesActual > 0
            ? 'Requieren revisión o prueba física'
            : 'Sin pendientes acumulados'
        }
        icon={<Clock size={18} aria-hidden="true" />}
        trend={
          periodos.anterior && !variacionPendientes.neutra
            ? {
                text: variacionPendientes.texto,
                positive: variacionPendientes.positiva,
              }
            : undefined
        }
      />

      {/* 3. Diagnósticos Completados */}
      <StatCard
        title="Diagnósticos Completados"
        value={completadosActual}
        subtitle={
          totalActual > 0
            ? `${pctConfirmados}% del total atendido`
            : 'Sin atenciones en el período'
        }
        icon={<CheckCircle2 size={18} aria-hidden="true" />}
        trend={
          periodos.anterior && !variacionCompletados.neutra
            ? {
                text: variacionCompletados.texto,
                positive: variacionCompletados.positiva,
              }
            : undefined
        }
      />

      {/* 4. Tiempo Promedio de Diagnóstico */}
      <div
        className="stat-card-compact stat-card-glass stat-card-tiempo-proceso"
        style={{
          backgroundColor: 'rgba(255, 255, 255, 0.78)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          borderRadius: '14px',
          border: '1px solid var(--border-color, #e2e8f0)',
          padding: '12px 14px',
          boxShadow: '0 4px 12px rgba(15, 23, 42, 0.05)',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 700,
              color: '#475569',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            Tiempo Promedio Diagnóstico
          </span>
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '8px',
              background:
                'linear-gradient(135deg, rgba(249, 115, 22, 0.18) 0%, rgba(234, 88, 12, 0.08) 100%)',
              color: '#ea580c',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <Timer size={18} aria-hidden="true" />
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', flexWrap: 'wrap' }}>
          <span
            style={{
              fontSize: '15px',
              fontWeight: 800,
              color: '#64748b',
              letterSpacing: '-0.02em',
              lineHeight: 1.2,
            }}
          >
            Sin datos suficientes
          </span>
          <span
            style={{
              fontSize: '9.5px',
              fontWeight: 700,
              padding: '2px 6px',
              borderRadius: '9999px',
              backgroundColor: 'rgba(148, 163, 184, 0.15)',
              color: '#475569',
            }}
            title="Medición operativa en taller. No se expone latencia técnica del bot como tiempo físico."
          >
            Proceso taller
          </span>
        </div>

        <span style={{ fontSize: '11px', color: '#94a3b8' }}>
          Medición presencial en bahía
        </span>
      </div>
    </section>
  );
};
