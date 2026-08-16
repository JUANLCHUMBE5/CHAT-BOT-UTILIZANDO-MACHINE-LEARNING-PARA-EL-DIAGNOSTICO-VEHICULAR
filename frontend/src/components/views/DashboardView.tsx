import React, { useState } from 'react';
import { Calendar, CheckCircle, Clock, Users, ArrowRight, Zap, FileText, RefreshCw } from 'lucide-react';
import { StatCard } from '../common/StatCard';
import { Card } from '../common/Card';
import { DateRangeModal } from '../common/DateRangeModal';
import type { ResumenMetricas } from '../../types';
import { getModoLabel } from '../../utils/modos';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

interface DashboardViewProps {
  metricas: ResumenMetricas | null;
  cargando?: boolean;
  onFiltrarMetricas?: (fechaInicio?: string, fechaFin?: string) => void;
  onIrAMecanicos?: () => void;
}

const MODOS_COLORS: Record<string, string> = {
  completo_ml_rag_llm: '#f97316',
  diagnostico_degradado_ml_rag: '#06b6d4',
  base_arboles_decision: '#10b981',
  evaluacion_reglas_expertas: '#6366f1',
  rapido_patrones_frecuentes: '#ec4899',
  en_cola_gemini: '#8b5cf6',
  saludo: '#3b82f6',
  baja_confianza: '#f59e0b',
};

const PALETTE_FALLBACKS = ['#f97316', '#06b6d4', '#8b5cf6', '#3b82f6', '#f59e0b', '#10b981', '#6366f1'];

const formatDateLocal = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const formatTiempoPromedio = (ms?: number): string => {
  if (!ms || ms <= 0) return '0 s';
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
};

export const DashboardView: React.FC<DashboardViewProps> = ({
  metricas,
  cargando = false,
  onFiltrarMetricas,
  onIrAMecanicos,
}) => {
  const [activeTabPreset, setActiveTabPreset] = useState<'hoy' | '7dias' | 'esteMes' | 'custom'>('esteMes');
  const [isDateModalOpen, setIsDateModalOpen] = useState(false);
  const [fechaInicio, setFechaInicio] = useState('');
  const [fechaFin, setFechaFin] = useState('');

  const handleQuickRange = (preset: 'hoy' | '7dias' | 'esteMes') => {
    setActiveTabPreset(preset);
    const hoy = new Date();
    const fFin = formatDateLocal(hoy);

    if (preset === 'hoy') {
      setFechaInicio(fFin);
      setFechaFin(fFin);
      if (onFiltrarMetricas) onFiltrarMetricas(fFin, fFin);
    } else if (preset === '7dias') {
      const inicio = new Date();
      inicio.setDate(hoy.getDate() - 7);
      const fInicio = formatDateLocal(inicio);
      setFechaInicio(fInicio);
      setFechaFin(fFin);
      if (onFiltrarMetricas) onFiltrarMetricas(fInicio, fFin);
    } else if (preset === 'esteMes') {
      const inicio = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
      const fInicio = formatDateLocal(inicio);
      setFechaInicio(fInicio);
      setFechaFin(fFin);
      if (onFiltrarMetricas) onFiltrarMetricas(fInicio, fFin);
    }
  };

  const handleApplyCustomRange = (start: string, end: string) => {
    setActiveTabPreset('custom');
    setFechaInicio(start);
    setFechaFin(end);
    if (onFiltrarMetricas) {
      onFiltrarMetricas(start || undefined, end || undefined);
    }
  };

  const handleResetFiltro = () => {
    setActiveTabPreset('esteMes');
    setFechaInicio('');
    setFechaFin('');
    if (onFiltrarMetricas) {
      onFiltrarMetricas(undefined, undefined);
    }
  };

  // Loading skeleton state when metrics are fetching
  if (cargando && !metricas) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
              Resumen del taller
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Cargando indicadores clave...
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              style={{
                height: '110px',
                backgroundColor: '#ffffff',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-color)',
                padding: '16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <RefreshCw size={20} className="animate-spin" style={{ color: 'var(--primary)', opacity: 0.5 }} />
            </div>
          ))}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
          {[1, 2].map((i) => (
            <div
              key={i}
              style={{
                height: '260px',
                backgroundColor: '#ffffff',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-color)',
                padding: '24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Cargando gráficas...</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Fallback when no metrics available
  if (!metricas) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', backgroundColor: '#ffffff', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
        <p style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)' }}>No se pudieron cargar las métricas</p>
        <button
          type="button"
          onClick={() => onFiltrarMetricas && onFiltrarMetricas()}
          style={{ marginTop: '12px', padding: '8px 16px', backgroundColor: '#3b82f6', color: '#fff', border: 'none', borderRadius: 'var(--radius-sm)', cursor: 'pointer' }}
        >
          Reintentar
        </button>
      </div>
    );
  }

  // Format mode names for PieChart legend & tooltips
  const distribucionModosFormateada = (metricas.distribucion_modos || []).map((item) => ({
    ...item,
    nombreModo: getModoLabel(item.modo),
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Mobile-First Header Greeting & Live Status */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 600,
                color: '#15803d',
                backgroundColor: '#dcfce7',
                padding: '2px 8px',
                borderRadius: '12px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#22c55e' }} />
              Taller En Línea
            </span>
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-main)', margin: 0, letterSpacing: '-0.02em' }}>
            Resumen del taller
          </h2>
        </div>
      </div>

      {/* Segmented Control Filter Bar (Compact App-Style Navigation with Glassmorphism) */}
      <div className="glass-segmented-bar">
        <button
          type="button"
          onClick={() => handleQuickRange('hoy')}
          className={`glass-segment-item ${activeTabPreset === 'hoy' ? 'active' : ''}`}
        >
          Hoy
        </button>
        <button
          type="button"
          onClick={() => handleQuickRange('7dias')}
          className={`glass-segment-item ${activeTabPreset === '7dias' ? 'active' : ''}`}
        >
          7 Días
        </button>
        <button
          type="button"
          onClick={() => handleQuickRange('esteMes')}
          className={`glass-segment-item ${activeTabPreset === 'esteMes' ? 'active' : ''}`}
        >
          Este Mes
        </button>
        <button
          type="button"
          onClick={() => setIsDateModalOpen(true)}
          className={`glass-segment-item ${activeTabPreset === 'custom' ? 'active' : ''}`}
        >
          <Calendar size={13} />
          <span>📅 Rango</span>
        </button>
      </div>

      {/* Custom Date Range Selection Modal */}
      <DateRangeModal
        isOpen={isDateModalOpen}
        onClose={() => setIsDateModalOpen(false)}
        initialFechaInicio={fechaInicio}
        initialFechaFin={fechaFin}
        onApply={handleApplyCustomRange}
        onReset={handleResetFiltro}
      />

      {/* Metric Cards (Sleek 2x2 grid with soft gradients & HSL accents) */}
      <div
        className="stat-grid-mobile"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '10px',
        }}
      >
        <StatCard
          title="Diagnósticos realizados"
          value={metricas.diagnosticos_realizados ?? metricas.diagnosticos_mes}
          icon={<FileText size={16} />}
          trend={{ text: 'Periodo', positive: true }}
        />
        <StatCard
          title="Diagnósticos pendientes"
          value={metricas.diagnosticos_pendientes ?? 0}
          icon={<Clock size={16} />}
          trend={{ text: 'Por validar', positive: false }}
        />
        <StatCard
          title="Tasa de confirmación"
          value={`${metricas.porcentaje_confirmados}%`}
          icon={<CheckCircle size={16} />}
          trend={{ text: 'Validados', positive: true }}
        />
        <StatCard
          title="Tiempo promedio"
          value={formatTiempoPromedio(metricas.tiempo_promedio_ms)}
          icon={<Zap size={16} />}
          trend={{ text: 'Periodo', positive: true }}
        />
      </div>

      {/* Charts Row: Compact & Mobile Optimized */}
      <div
        className="charts-grid-mobile"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '12px',
        }}
      >
        {/* Daily Diagnostics Bar Chart */}
        <Card style={{ padding: '14px 12px 10px 12px', overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
              Volumen diario
            </h4>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 500 }}>
              {activeTabPreset === 'hoy'
                ? 'Hoy'
                : activeTabPreset === '7dias'
                ? 'Últimos 7 días'
                : activeTabPreset === 'esteMes'
                ? 'Este mes'
                : 'Rango personalizado'}
            </span>
          </div>
          <div style={{ width: '100%', height: 160, minHeight: 160 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={metricas.actividad_diaria}
                margin={{ top: 8, right: 4, left: -24, bottom: 0 }}
              >
                <XAxis
                  dataKey="fecha"
                  stroke="#94a3b8"
                  fontSize={10}
                  tickLine={false}
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
                  cursor={{ fill: 'rgba(59, 130, 246, 0.06)' }}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderColor: 'var(--border-color)',
                    borderRadius: '8px',
                    fontSize: '11px',
                    padding: '6px 10px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                  }}
                />
                <Bar
                  dataKey="cantidad"
                  fill="#3b82f6"
                  radius={[4, 4, 0, 0]}
                  name="Diagnósticos"
                  maxBarSize={28}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* AI Modes Distribution Donut Chart */}
        <Card style={{ padding: '14px 12px 10px 12px', overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
              Modos de IA
            </h4>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 500 }}>
              Distribución
            </span>
          </div>
          <div style={{ width: '100%', height: 160, minHeight: 160 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                <Pie
                  data={distribucionModosFormateada}
                  cx="50%"
                  cy="50%"
                  innerRadius={36}
                  outerRadius={58}
                  paddingAngle={3}
                  dataKey="cantidad"
                  nameKey="nombreModo"
                >
                  {distribucionModosFormateada.map((entry, index) => (
                    <Cell
                      key={`cell-${entry.modo || index}`}
                      fill={MODOS_COLORS[entry.modo] || PALETTE_FALLBACKS[index % PALETTE_FALLBACKS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderColor: 'var(--border-color)',
                    borderRadius: '8px',
                    fontSize: '11px',
                    padding: '6px 10px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Frequent Faults & Quick Actions Row */}
      <div
        className="bottom-grid-mobile"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '12px',
        }}
      >
        {/* Frequent Faults List */}
        <Card style={{ padding: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
              Fallas frecuentes
            </h4>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Top detectadas</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {(metricas.fallas_frecuentes && metricas.fallas_frecuentes.length > 0) ? (
              metricas.fallas_frecuentes.map((f, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '6px 10px',
                    backgroundColor: 'var(--bg-subtle)',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                >
                  <span style={{ color: 'var(--text-main)', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '75%' }}>
                    {f.falla}
                  </span>
                  <span style={{ fontWeight: 700, color: 'var(--primary)', fontSize: '11px' }}>
                    {f.cantidad} casos
                  </span>
                </div>
              ))
            ) : (
              <div style={{ textAlign: 'center', padding: '16px 0', color: 'var(--text-muted)', fontSize: '12px' }}>
                No se registraron fallas en este periodo.
              </div>
            )}
          </div>
        </Card>

        {/* Quick Management Card */}
        <Card style={{ padding: '14px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
              <Users size={16} color="var(--primary)" />
              <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                Equipo y personal
              </h4>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '0 0 10px 0', lineHeight: 1.4 }}>
              Gestiona el equipo técnico, roles y solicitudes de acceso del taller.
            </p>
          </div>
          {onIrAMecanicos && (
            <button
              type="button"
              onClick={onIrAMecanicos}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                width: '100%',
                padding: '9px 12px',
                backgroundColor: 'var(--primary)',
                color: '#ffffff',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <span>Ir a Personas y Accesos</span>
              <ArrowRight size={14} />
            </button>
          )}
        </Card>
      </div>
    </div>
  );
};
