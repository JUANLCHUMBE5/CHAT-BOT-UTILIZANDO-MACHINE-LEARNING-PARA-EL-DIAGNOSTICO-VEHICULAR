import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { useDashboardOperativo } from '../../hooks/useDashboardOperativo';
import type { ResumenMetricas } from '../../types';
import {
  DashboardFiltros,
  DashboardKpis,
  VehiculosPorDiaChart,
  EstadoAtencionesChart,
  FallasFrecuentesList,
} from './dashboard';

interface DashboardViewProps {
  onIrAFallas?: () => void;
  onIrAMecanicos?: () => void;
  // Parámetros opcionales para preservar retrocompatibilidad
  metricas?: ResumenMetricas | null;
  cargando?: boolean;
  onFiltrarMetricas?: (fechaInicio?: string, fechaFin?: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  onIrAFallas,
  onIrAMecanicos,
}) => {
  const {
    preset,
    periodos,
    metricasActuales,
    metricasAnteriores,
    cargando,
    error,
    customInicio,
    customFin,
    cambiarPreset,
    aplicarRangoCustom,
    recargar,
  } = useDashboardOperativo();

  // 1. Estado de Carga Inicial (Skeleton Screen)
  if (cargando && !metricasActuales) {
    return (
      <div className="dashboard-view-wrapper" aria-busy="true" aria-label="Cargando dashboard operativo">
        {/* Skeleton Header */}
        <div style={{ height: '40px', backgroundColor: '#ffffff', borderRadius: '10px', opacity: 0.6 }} />

        {/* Skeleton KPIs */}
        <div className="dashboard-kpis-grid">
          {[1, 2, 3, 4].map((item) => (
            <div
              key={item}
              style={{
                height: '90px',
                backgroundColor: '#ffffff',
                borderRadius: '14px',
                border: '1px solid var(--border-color, #e2e8f0)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <RefreshCw size={18} className="animate-spin" style={{ color: 'var(--primary, #ea580c)', opacity: 0.4 }} />
            </div>
          ))}
        </div>

        {/* Skeleton Charts */}
        <div className="dashboard-charts-grid">
          <div style={{ height: '220px', backgroundColor: '#ffffff', borderRadius: '12px', border: '1px solid var(--border-color, #e2e8f0)' }} />
          <div style={{ height: '220px', backgroundColor: '#ffffff', borderRadius: '12px', border: '1px solid var(--border-color, #e2e8f0)' }} />
        </div>
      </div>
    );
  }

  // 2. Estado de Error
  if (error && !metricasActuales) {
    return (
      <div
        style={{
          padding: '40px 20px',
          textAlign: 'center',
          backgroundColor: '#ffffff',
          borderRadius: '14px',
          border: '1px solid var(--border-color, #e2e8f0)',
          maxWidth: '500px',
          margin: '40px auto',
          boxShadow: '0 4px 16px rgba(15, 23, 42, 0.05)',
        }}
        role="alert"
      >
        <div
          style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            backgroundColor: 'rgba(239, 68, 68, 0.12)',
            color: '#dc2626',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
          }}
        >
          <AlertCircle size={24} />
        </div>
        <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)', margin: '0 0 6px' }}>
          No se pudieron cargar los datos del dashboard
        </h3>
        <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', margin: '0 0 16px' }}>
          {error}
        </p>
        <button
          type="button"
          onClick={recargar}
          style={{
            padding: '8px 18px',
            backgroundColor: 'var(--primary, #ea580c)',
            color: '#ffffff',
            border: 'none',
            borderRadius: '8px',
            fontSize: '13px',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <RefreshCw size={14} />
          <span>Reintentar</span>
        </button>
      </div>
    );
  }

  // 3. Fallback de Datos Nulos
  if (!metricasActuales) {
    return (
      <div style={{ padding: '32px 16px', textAlign: 'center', backgroundColor: '#ffffff', borderRadius: '12px' }}>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
          No hay datos para el período seleccionado.
        </p>
        <button
          type="button"
          onClick={recargar}
          style={{ marginTop: '10px', padding: '6px 14px', cursor: 'pointer' }}
        >
          Reintentar
        </button>
      </div>
    );
  }

  // 4. Render Principal del Dashboard Operativo
  return (
    <div className="dashboard-view-wrapper">
      {/* Encabezado y Filtros Temporales */}
      <DashboardFiltros
        preset={preset}
        periodos={periodos}
        cargando={cargando}
        customInicio={customInicio}
        customFin={customFin}
        onCambiarPreset={cambiarPreset}
        onAplicarRango={aplicarRangoCustom}
        onRecargar={recargar}
      />

      {/* Fila 1: Tarjetas KPI Operativas */}
      <DashboardKpis
        metricasActuales={metricasActuales}
        metricasAnteriores={metricasAnteriores}
        periodos={periodos}
      />

      {/* Fila 2: Gráficos de Actividad y Estados */}
      <div className="dashboard-charts-grid">
        <VehiculosPorDiaChart
          metricasActuales={metricasActuales}
          metricasAnteriores={metricasAnteriores}
          periodos={periodos}
        />
        <EstadoAtencionesChart metricas={metricasActuales} />
      </div>

      {/* Fila 3: Fallas Más Frecuentes del Período */}
      <FallasFrecuentesList
        metricas={metricasActuales}
        onIrAFallas={onIrAFallas || onIrAMecanicos}
      />
    </div>
  );
};
