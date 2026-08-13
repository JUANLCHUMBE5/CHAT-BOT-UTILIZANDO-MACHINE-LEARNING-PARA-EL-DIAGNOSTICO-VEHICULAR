import React, { useState } from 'react';
import { Calendar, TrendingUp, CheckCircle, Clock, Users, ArrowRight } from 'lucide-react';
import { StatCard } from '../common/StatCard';
import { Card } from '../common/Card';
import { DateRangeModal } from '../common/DateRangeModal';
import type { ResumenMetricas } from '../../types';
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
  metricas: ResumenMetricas;
  onFiltrarMetricas?: (fechaInicio?: string, fechaFin?: string) => void;
  onIrAMecanicos?: () => void;
}

const MODOS_COLORS: Record<string, string> = {
  completo_ml_rag_llm: '#f97316',
  diagnostico_degradado_ml_rag: '#06b6d4',
  en_cola_gemini: '#8b5cf6',
  saludo: '#3b82f6',
  baja_confianza: '#f59e0b',
};

const PALETTE_FALLBACKS = ['#f97316', '#06b6d4', '#8b5cf6', '#3b82f6', '#f59e0b'];

const formatDateLocal = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export const DashboardView: React.FC<DashboardViewProps> = ({
  metricas,
  onFiltrarMetricas,
  onIrAMecanicos,
}) => {
  const [activeTabPreset, setActiveTabPreset] = useState<'hoy' | '7dias' | 'esteMes' | 'custom'>('hoy');
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
    setActiveTabPreset('hoy');
    setFechaInicio('');
    setFechaFin('');
    if (onFiltrarMetricas) {
      onFiltrarMetricas(undefined, undefined);
    }
  };

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
            Resumen Operativo
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
          title="Hoy"
          value={metricas.diagnosticos_hoy}
          icon={<Calendar size={16} />}
          trend={{ text: '+15%', positive: true }}
        />
        <StatCard
          title="Esta Semana"
          value={metricas.diagnosticos_semana}
          icon={<TrendingUp size={16} />}
          trend={{ text: '+8%', positive: true }}
        />
        <StatCard
          title="Este Mes"
          value={metricas.diagnosticos_mes}
          icon={<Clock size={16} />}
        />
        <StatCard
          title="Precisión"
          value={`${metricas.porcentaje_confirmados}%`}
          icon={<CheckCircle size={16} />}
          trend={{ text: 'UCV', positive: true }}
        />
      </div>

      {/* Single App-Native Primary Action Banner */}
      {onIrAMecanicos && (
        <button
          type="button"
          onClick={onIrAMecanicos}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '14px 18px',
            borderRadius: '14px',
            background: 'linear-gradient(135deg, #f97316 0%, #ea580c 45%, #c2410c 100%)',
            color: '#ffffff',
            border: '1px solid rgba(255, 255, 255, 0.25)',
            fontSize: '13px',
            fontWeight: 700,
            cursor: 'pointer',
            boxShadow: '0 10px 25px -4px rgba(234, 88, 12, 0.42), 0 4px 10px rgba(0, 0, 0, 0.06)',
            width: '100%',
          }}
          className="management-btn-native card-hover-effect"
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(4px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              <Users size={20} color="#ffffff" />
            </div>
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: '13px', fontWeight: 700, lineHeight: 1.2 }}>
                Gestionar Equipo y Mecánicos
              </div>
              <div style={{ fontSize: '11px', fontWeight: 400, opacity: 0.9 }}>
                Alta de nuevo personal, roles y estado de acceso
              </div>
            </div>
          </div>
          <div className="arrow-icon-animated" style={{ display: 'flex', alignItems: 'center' }}>
            <ArrowRight size={20} color="#ffffff" />
          </div>
        </button>
      )}

      {/* Charts Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '14px',
        }}
      >
        {/* Bar Chart: Volúmen diario */}
        <Card title="Volumen Diarios">
          <div className="chart-container-mobile" style={{ width: '100%', height: 180, marginTop: '4px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metricas.actividad_diaria} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="barOrangeGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f97316" stopOpacity={1} />
                    <stop offset="100%" stopColor="#ea580c" stopOpacity={0.85} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="fecha" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(15, 23, 42, 0.88)',
                    backdropFilter: 'blur(8px)',
                    WebkitBackdropFilter: 'blur(8px)',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    borderRadius: '12px',
                    color: '#ffffff',
                    fontSize: '12px',
                    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.25)',
                    padding: '8px 12px',
                  }}
                  itemStyle={{ color: '#ffedd5', fontWeight: 600 }}
                  labelStyle={{ color: '#94a3b8', fontWeight: 500 }}
                />
                <Bar dataKey="cantidad" fill="url(#barOrangeGradient)" radius={[6, 6, 0, 0]} name="Diagnósticos" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Donut Chart: Modos de Diagnóstico */}
        <Card title="Distribución por Modo">
          <div className="chart-container-mobile" style={{ width: '100%', height: 180, marginTop: '4px', display: 'flex', alignItems: 'center' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={metricas.distribucion_modos}
                  dataKey="cantidad"
                  nameKey="modo"
                  cx="50%"
                  cy="50%"
                  innerRadius={38}
                  outerRadius={62}
                  paddingAngle={4}
                >
                  {metricas.distribucion_modos.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={MODOS_COLORS[entry.modo] || PALETTE_FALLBACKS[index % PALETTE_FALLBACKS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(15, 23, 42, 0.88)',
                    backdropFilter: 'blur(8px)',
                    WebkitBackdropFilter: 'blur(8px)',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    borderRadius: '12px',
                    color: '#ffffff',
                    fontSize: '12px',
                    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.25)',
                    padding: '8px 12px',
                  }}
                  itemStyle={{ color: '#ffffff', fontWeight: 600 }}
                  labelStyle={{ color: '#94a3b8', fontWeight: 500 }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Frequent Faults Table */}
      <Card title="Fallas Frecuentes">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '2px' }}>
          {metricas.fallas_frecuentes.map((item, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '7px 10px',
                backgroundColor: 'var(--bg-subtle)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '12px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span
                  style={{
                    fontWeight: 700,
                    color: 'var(--primary)',
                    width: '16px',
                    textAlign: 'center',
                  }}
                >
                  {index + 1}
                </span>
                <span style={{ fontWeight: 500, color: 'var(--text-main)' }}>{item.falla}</span>
              </div>
              <span
                style={{
                  fontSize: '10px',
                  fontWeight: 600,
                  backgroundColor: '#ffffff',
                  padding: '2px 6px',
                  borderRadius: '10px',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-secondary)',
                }}
              >
                {item.cantidad}
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};
