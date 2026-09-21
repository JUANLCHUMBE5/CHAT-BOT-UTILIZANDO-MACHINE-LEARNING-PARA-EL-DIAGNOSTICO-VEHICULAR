import React, { useState } from 'react';
import { Calendar, RefreshCw } from 'lucide-react';
import { DateRangeModal } from '../../common/DateRangeModal';
import type { DashboardPreset, PeriodosComparativa } from '../../../utils/dashboardComparador';

interface DashboardFiltrosProps {
  preset: DashboardPreset;
  periodos: PeriodosComparativa;
  cargando: boolean;
  customInicio: string;
  customFin: string;
  onCambiarPreset: (preset: 'hoy' | '7dias' | 'esteMes') => void;
  onAplicarRango: (inicio: string, fin: string) => void;
  onRecargar: () => void;
}

export const DashboardFiltros: React.FC<DashboardFiltrosProps> = ({
  preset,
  periodos,
  cargando,
  customInicio,
  customFin,
  onCambiarPreset,
  onAplicarRango,
  onRecargar,
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div className="dashboard-header-container">
      {/* Título Operativo y Estado de Período */}
      <div className="dashboard-title-box">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
            Dashboard Operativo
          </h2>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '9999px',
              backgroundColor: 'rgba(249, 115, 22, 0.12)',
              color: 'var(--primary)',
            }}
          >
            Taller en vivo
          </span>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '3px 0 0 0' }}>
          Período: <strong>{periodos.etiquetaActual}</strong> ({periodos.actual.inicio} a {periodos.actual.fin})
          {periodos.anterior && (
            <span className="periodo-comparado-hint"> • Comparado con: {periodos.etiquetaAnterior}</span>
          )}
        </p>
      </div>

      {/* Controles de Filtro Temporal y Recarga */}
      <div className="dashboard-actions-row">
        <div className="glass-segmented-bar" role="group" aria-label="Filtro temporal del dashboard">
          <button
            type="button"
            onClick={() => onCambiarPreset('hoy')}
            className={`glass-segment-item ${preset === 'hoy' ? 'active' : ''}`}
            aria-pressed={preset === 'hoy'}
          >
            Hoy
          </button>
          <button
            type="button"
            onClick={() => onCambiarPreset('7dias')}
            className={`glass-segment-item ${preset === '7dias' ? 'active' : ''}`}
            aria-pressed={preset === '7dias'}
          >
            7 días
          </button>
          <button
            type="button"
            onClick={() => onCambiarPreset('esteMes')}
            className={`glass-segment-item ${preset === 'esteMes' ? 'active' : ''}`}
            aria-pressed={preset === 'esteMes'}
          >
            Este mes
          </button>
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className={`glass-segment-item ${preset === 'custom' ? 'active' : ''}`}
            aria-pressed={preset === 'custom'}
          >
            <Calendar size={13} aria-hidden="true" />
            <span>Rango</span>
          </button>
        </div>

        <button
          type="button"
          onClick={onRecargar}
          disabled={cargando}
          className="dashboard-refresh-btn"
          title="Actualizar datos del dashboard"
          aria-label="Actualizar métricas"
        >
          <RefreshCw size={15} className={cargando ? 'animate-spin' : ''} />
          <span className="refresh-btn-text">Actualizar</span>
        </button>
      </div>

      <DateRangeModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        initialFechaInicio={customInicio}
        initialFechaFin={customFin}
        onApply={(start, end) => {
          setIsModalOpen(false);
          onAplicarRango(start, end);
        }}
        onReset={() => {
          setIsModalOpen(false);
          onCambiarPreset('esteMes');
        }}
      />
    </div>
  );
};
