import React, { useState } from 'react';
import {
  Calendar,
  CheckCircle2,
  Clock,
  FileText,
  RefreshCw,
  Zap,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card } from '../common/Card';
import { DateRangeModal } from '../common/DateRangeModal';
import { StatCard } from '../common/StatCard';
import type { ResumenMetricas } from '../../types';
import { getModoLabel } from '../../utils/modos';

interface DashboardViewProps {
  metricas: ResumenMetricas | null;
  cargando?: boolean;
  onFiltrarMetricas?: (fechaInicio?: string, fechaFin?: string) => void;
  onIrAMecanicos?: () => void;
}

const MODOS_COLORS: Record<string, string> = {
  completo_ml_rag_llm: '#10b981',
  diagnostico_degradado_ml_rag: '#06b6d4',
  base_arboles_decision: '#6366f1',
  evaluacion_reglas_expertas: '#8b5cf6',
  rapido_patrones_frecuentes: '#ec4899',
  en_cola_gemini: '#f59e0b',
  saludo: '#3b82f6',
  baja_confianza: '#ef4444',
};

const PALETTE_FALLBACKS = ['#10b981', '#06b6d4', '#8b5cf6', '#3b82f6', '#f59e0b', '#6366f1', '#ec4899'];

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
}) => {
  const [activePreset, setActivePreset] = useState<'hoy' | '7dias' | 'esteMes' | 'custom'>('esteMes');
  const [isDateModalOpen, setIsDateModalOpen] = useState(false);
  const [fechaInicio, setFechaInicio] = useState('');
  const [fechaFin, setFechaFin] = useState('');

  const handleQuickRange = (preset: 'hoy' | '7dias' | 'esteMes') => {
    setActivePreset(preset);
    const hoy = new Date();
    const fin = formatDateLocal(hoy);
    let inicio = fin;

    if (preset === '7dias') {
      const fecha = new Date();
      fecha.setDate(hoy.getDate() - 6);
      inicio = formatDateLocal(fecha);
    } else if (preset === 'esteMes') {
      inicio = formatDateLocal(new Date(hoy.getFullYear(), hoy.getMonth(), 1));
    }

    setFechaInicio(inicio);
    setFechaFin(fin);
    onFiltrarMetricas?.(inicio, fin);
  };

  const handleApplyCustomRange = (start: string, end: string) => {
    setActivePreset('custom');
    setFechaInicio(start);
    setFechaFin(end);
    onFiltrarMetricas?.(start || undefined, end || undefined);
  };

  const handleResetFiltro = () => {
    setActivePreset('esteMes');
    setFechaInicio('');
    setFechaFin('');
    onFiltrarMetricas?.();
  };

  if (cargando && !metricas) {
    return (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
        {[1, 2, 3, 4].map((item) => (
          <div
            key={item}
            style={{
              height: '95px',
              backgroundColor: '#ffffff',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-color)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <RefreshCw size={18} className="animate-spin" style={{ color: 'var(--primary)', opacity: 0.5 }} />
          </div>
        ))}
      </div>
    );
  }

  if (!metricas) {
    return (
      <div style={{ padding: '32px 16px', textAlign: 'center', backgroundColor: '#fff', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
        <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)' }}>No se pudieron cargar las métricas operativas</p>
        <button
          type="button"
          onClick={() => onFiltrarMetricas?.()}
          style={{ marginTop: '12px', padding: '8px 16px', backgroundColor: '#3b82f6', color: '#fff', border: 'none', borderRadius: 'var(--radius-sm)', cursor: 'pointer' }}
        >
          Reintentar conexión
        </button>
      </div>
    );
  }

  const modos = (metricas.distribucion_modos || []).map((item) => ({
    ...item,
    nombreModo: getModoLabel(item.modo),
  }));

  const hasActividad = (metricas.actividad_diaria || []).some((item) => item.cantidad > 0);
  const hasModos = modos.some((item) => item.cantidad > 0);
  const hasFallas = Boolean(metricas.fallas_frecuentes?.length);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* Selector de Rango de Fecha */}
      <div className="glass-segmented-bar">
        <button type="button" onClick={() => handleQuickRange('hoy')} className={`glass-segment-item ${activePreset === 'hoy' ? 'active' : ''}`}>
          Hoy
        </button>
        <button type="button" onClick={() => handleQuickRange('7dias')} className={`glass-segment-item ${activePreset === '7dias' ? 'active' : ''}`}>
          7 días
        </button>
        <button type="button" onClick={() => handleQuickRange('esteMes')} className={`glass-segment-item ${activePreset === 'esteMes' ? 'active' : ''}`}>
          Este mes
        </button>
        <button type="button" onClick={() => setIsDateModalOpen(true)} className={`glass-segment-item ${activePreset === 'custom' ? 'active' : ''}`}>
          <Calendar size={13} />
          <span>Rango</span>
        </button>
      </div>

      <DateRangeModal
        isOpen={isDateModalOpen}
        onClose={() => setIsDateModalOpen(false)}
        initialFechaInicio={fechaInicio}
        initialFechaFin={fechaFin}
        onApply={handleApplyCustomRange}
        onReset={handleResetFiltro}
      />

      {/* 4 Stat Cards Operativas Reales (2x2 en móvil) */}
      <div className="stat-grid-mobile" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '10px' }}>
        <StatCard
          title="Diagnósticos Realizados"
          value={metricas.diagnosticos_realizados ?? metricas.diagnosticos_mes}
          icon={<FileText size={16} />}
        />
        <StatCard
          title="Pendientes Confirmación"
          value={metricas.diagnosticos_pendientes ?? 0}
          icon={<Clock size={16} />}
        />
        <StatCard
          title="Confirmados por Mecánicos"
          value={`${metricas.porcentaje_confirmados}%`}
          icon={<CheckCircle2 size={16} />}
        />
        <StatCard
          title="Tiempo Promedio del Bot"
          value={formatTiempoPromedio(metricas.tiempo_promedio_ms)}
          icon={<Zap size={16} />}
        />
      </div>

      {(hasActividad || hasModos) && (
        <div className="charts-grid-mobile" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '10px' }}>
          {hasActividad && (
            <Card style={{ padding: '12px 12px 8px', overflow: 'hidden' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <h4 style={{ fontSize: '12.5px', fontWeight: 700, margin: 0, color: 'var(--text-main)' }}>Volumen diario</h4>
                <span style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>
                  {activePreset === 'hoy' ? 'Hoy' : activePreset === '7dias' ? '7 días' : activePreset === 'esteMes' ? 'Este mes' : 'Rango'}
                </span>
              </div>
              <div style={{ width: '100%', height: 150 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={metricas.actividad_diaria} margin={{ top: 6, right: 4, left: -24, bottom: 0 }}>
                    <XAxis dataKey="fecha" stroke="#94a3b8" fontSize={9.5} tickLine={false} interval="preserveStartEnd" />
                    <YAxis stroke="#94a3b8" fontSize={9.5} tickLine={false} axisLine={false} allowDecimals={false} />
                    <Tooltip contentStyle={{ borderColor: 'var(--border-color)', borderRadius: '6px', fontSize: '11px' }} />
                    <Bar dataKey="cantidad" fill="var(--primary)" radius={[4, 4, 0, 0]} name="Diagnósticos" maxBarSize={24} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}

          {hasModos && (
            <Card style={{ padding: '12px 12px 8px', overflow: 'hidden' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <h4 style={{ fontSize: '12.5px', fontWeight: 700, margin: 0, color: 'var(--text-main)' }}>Modos de respuesta</h4>
              </div>
              <div style={{ width: '100%', height: 150 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={modos} cx="50%" cy="50%" innerRadius={34} outerRadius={54} paddingAngle={3} dataKey="cantidad" nameKey="nombreModo">
                      {modos.map((entry, index) => (
                        <Cell key={`cell-${entry.modo || index}`} fill={MODOS_COLORS[entry.modo] || PALETTE_FALLBACKS[index % PALETTE_FALLBACKS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ borderColor: 'var(--border-color)', borderRadius: '6px', fontSize: '11px' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}
        </div>
      )}

      {hasFallas && (
        <Card style={{ padding: '12px 14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <h4 style={{ fontSize: '12.5px', fontWeight: 700, margin: 0, color: 'var(--text-main)' }}>Fallas frecuentes</h4>
            <span style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>Periodo seleccionado</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            {metricas.fallas_frecuentes.map((falla, index) => (
              <div
                key={`${falla.falla}-${index}`}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '5px 8px',
                  backgroundColor: 'var(--bg-subtle)',
                  borderRadius: '5px',
                  fontSize: '11px',
                }}
              >
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '75%' }}>
                  {falla.falla}
                </span>
                <span style={{ fontWeight: 700, color: 'var(--primary)', fontSize: '10.5px' }}>
                  {falla.cantidad} caso(s)
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {!hasActividad && !hasModos && !hasFallas && (
        <Card style={{ padding: '18px 14px', textAlign: 'center' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Aún no hay diagnósticos en este periodo.
          </span>
        </Card>
      )}
    </div>
  );
};
