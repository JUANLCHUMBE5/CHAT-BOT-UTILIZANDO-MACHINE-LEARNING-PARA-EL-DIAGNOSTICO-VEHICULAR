import React, { useState } from 'react';
import {
  Calendar,
  CheckCircle,
  Clock,
  Users,
  ArrowRight,
  Zap,
  FileText,
  RefreshCw,
  Cpu,
  Brain,
  Sparkles,
  BookOpen,
  ShieldCheck,
  BarChart3,
  Layers,
  Award,
  GraduationCap,
} from 'lucide-react';
import { StatCard } from '../common/StatCard';
import { Card } from '../common/Card';
import { DateRangeModal } from '../common/DateRangeModal';
import { FichasTesisView } from './FichasTesisView';
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
  Legend,
  CartesianGrid,
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

// Benchmark data optimized with compact labels for mobile responsiveness
const MODELOS_COMPARATIVA_DATA = [
  {
    modelo: 'SVM',
    modeloCompleto: 'Linear SVM (Calibrado)',
    f1_macro: 97.37,
    exactitud: 97.54,
    f1_weighted: 97.03,
    desviacion: '±1.20%',
    destacado: true,
  },
  {
    modelo: 'Log. Reg.',
    modeloCompleto: 'Logistic Regression',
    f1_macro: 96.39,
    exactitud: 96.10,
    f1_weighted: 96.25,
    desviacion: '±1.48%',
    destacado: false,
  },
  {
    modelo: 'Naive B.',
    modeloCompleto: 'Complement Naive Bayes',
    f1_macro: 94.99,
    exactitud: 94.80,
    f1_weighted: 95.10,
    desviacion: '±2.16%',
    destacado: false,
  },
  {
    modelo: 'R. Forest',
    modeloCompleto: 'Random Forest (200 Árboles)',
    f1_macro: 94.37,
    exactitud: 94.20,
    f1_weighted: 94.50,
    desviacion: '±1.42%',
    destacado: false,
  },
];

const LATENCIAS_PIPELINE_DATA = [
  { etapa: '1. TF-IDF', etapaCompleta: '1. Normalización TF-IDF', ms: 3, fill: '#64748b' },
  { etapa: '2. ML (SVM)', etapaCompleta: '2. Clasificador ML (SVM)', ms: 12, fill: '#2563eb' },
  { etapa: '3. RAG', etapaCompleta: '3. Búsqueda RAG (Manuales)', ms: 45, fill: '#06b6d4' },
  { etapa: '4. Gemini', etapaCompleta: '4. Generación Gemini LLM', ms: 1150, fill: '#8b5cf6' },
];

const RESILIENCIA_DATA = [
  { name: 'Modo Completo (ML+RAG+LLM)', value: 85, color: '#f97316' },
  { name: 'Modo Degradado (Fallback)', value: 15, color: '#06b6d4' },
];

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
  // Main Tab: 'operaciones' vs 'ml_tesis' vs 'fichas_tesis'
  const [tabPrincipal, setTabPrincipal] = useState<'operaciones' | 'ml_tesis' | 'fichas_tesis'>('operaciones');

  // Filter Presets for Operaciones Tab
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
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
              Panel de Control
            </h2>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Cargando indicadores clave...
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              style={{
                height: '95px',
                backgroundColor: '#ffffff',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-color)',
                padding: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <RefreshCw size={18} className="animate-spin" style={{ color: 'var(--primary)', opacity: 0.5 }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Fallback when no metrics available
  if (!metricas) {
    return (
      <div style={{ padding: '32px 16px', textAlign: 'center', backgroundColor: '#ffffff', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
        <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)' }}>No se pudieron cargar las métricas</p>
        <button
          type="button"
          onClick={() => onFiltrarMetricas && onFiltrarMetricas()}
          style={{ marginTop: '12px', padding: '8px 16px', backgroundColor: '#3b82f6', color: '#fff', border: 'none', borderRadius: 'var(--radius-sm)', cursor: 'pointer', fontSize: '13px' }}
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* Top 3-Tab Switcher: Operaciones vs ML vs Fichas Tesis */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          backgroundColor: '#f1f5f9',
          padding: '4px',
          borderRadius: '10px',
          gap: '4px',
        }}
      >
        <button
          type="button"
          onClick={() => setTabPrincipal('operaciones')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            padding: '7px 8px',
            borderRadius: '7px',
            fontSize: '12px',
            fontWeight: 700,
            border: 'none',
            backgroundColor: tabPrincipal === 'operaciones' ? '#ffffff' : 'transparent',
            color: tabPrincipal === 'operaciones' ? 'var(--primary)' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: tabPrincipal === 'operaciones' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
          }}
        >
          <BarChart3 size={14} />
          <span>Operaciones</span>
        </button>

        <button
          type="button"
          onClick={() => setTabPrincipal('ml_tesis')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            padding: '7px 8px',
            borderRadius: '7px',
            fontSize: '12px',
            fontWeight: 700,
            border: 'none',
            backgroundColor: tabPrincipal === 'ml_tesis' ? '#7c3aed' : 'transparent',
            color: tabPrincipal === 'ml_tesis' ? '#ffffff' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: tabPrincipal === 'ml_tesis' ? '0 1px 3px rgba(124,58,237,0.2)' : 'none',
          }}
        >
          <Brain size={14} />
          <span>Modelos ML</span>
        </button>

        <button
          type="button"
          onClick={() => setTabPrincipal('fichas_tesis')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            padding: '7px 8px',
            borderRadius: '7px',
            fontSize: '12px',
            fontWeight: 700,
            border: 'none',
            backgroundColor: tabPrincipal === 'fichas_tesis' ? '#059669' : 'transparent',
            color: tabPrincipal === 'fichas_tesis' ? '#ffffff' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: tabPrincipal === 'fichas_tesis' ? '0 1px 3px rgba(5,150,105,0.2)' : 'none',
          }}
        >
          <GraduationCap size={14} />
          <span>🎓 Fichas Tesis UCV</span>
        </button>
      </div>

      {/* ========================================================================= */}
      {/* VISTA 1: OPERACIONES DEL TALLER (DASHBOARD DEL DÍA A DÍA)                 */}
      {/* ========================================================================= */}
      {tabPrincipal === 'operaciones' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Segmented Control Filter Bar */}
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
              <span>Rango</span>
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

          {/* Metric Cards (2x2 Grid on mobile) */}
          <div
            className="stat-grid-mobile"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '10px',
            }}
          >
            <StatCard
              title="Diagnósticos"
              value={metricas.diagnosticos_realizados ?? metricas.diagnosticos_mes}
              icon={<FileText size={16} />}
              trend={{ text: 'Periodo', positive: true }}
            />
            <StatCard
              title="Pendientes"
              value={metricas.diagnosticos_pendientes ?? 0}
              icon={<Clock size={16} />}
              trend={{ text: 'Por validar', positive: false }}
            />
            <StatCard
              title="Confirmación"
              value={`${metricas.porcentaje_confirmados}%`}
              icon={<CheckCircle size={16} />}
              trend={{ text: 'Validados', positive: true }}
            />
            <StatCard
              title="T. Promedio"
              value={formatTiempoPromedio(metricas.tiempo_promedio_ms)}
              icon={<Zap size={16} />}
              trend={{ text: 'Periodo', positive: true }}
            />
          </div>

          {/* Charts Row */}
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
                    : 'Rango'}
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
      )}

      {/* ========================================================================= */}
      {/* VISTA 2: RENDIMIENTO ML, RAG & LLM (EVALUACIÓN DE ALGORITMOS)             */}
      {/* ========================================================================= */}
      {tabPrincipal === 'ml_tesis' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Header Description Card */}
          <div
            style={{
              padding: '14px 16px',
              backgroundColor: '#faf5ff',
              border: '1px solid #e9d5ff',
              borderRadius: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Sparkles size={16} style={{ color: '#9333ea' }} />
                <h3 style={{ fontSize: '14px', fontWeight: 800, color: '#581c87', margin: 0 }}>
                  Evaluación de Modelos IA
                </h3>
              </div>
              <span style={{ fontSize: '10px', fontWeight: 700, backgroundColor: '#f3e8ff', color: '#7e22ce', padding: '2px 7px', borderRadius: '12px', border: '1px solid #d8b4fe' }}>
                v2.2.0-audited
              </span>
            </div>
            <p style={{ fontSize: '12px', color: '#6b21a8', margin: 0, lineHeight: 1.4 }}>
              Comparativa experimental de algoritmos supervisados, tiempos de inferencia y resiliencia híbrida.
            </p>
          </div>

          {/* 4 Stat Cards in 2x2 Grid for Mobile */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '10px',
            }}
          >
            <StatCard
              title="Algoritmo Ganador"
              value="Linear SVM"
              icon={<Award size={16} />}
              trend={{ text: 'Calibrado', positive: true }}
            />
            <StatCard
              title="F1-Macro (4-Fold)"
              value="97.37%"
              icon={<Brain size={16} />}
              trend={{ text: '±1.20%', positive: true }}
            />
            <StatCard
              title="Latencia Inferencia"
              value="~12 ms"
              icon={<Zap size={16} />}
              trend={{ text: 'Ultra Rápido', positive: true }}
            />
            <StatCard
              title="Cobertura Clases"
              value="48 Clases"
              icon={<Layers size={16} />}
              trend={{ text: 'Fallas Auto', positive: true }}
            />
          </div>

          {/* Charts Row: Mobile Optimized with clean labels */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '12px',
            }}
          >
            {/* Gráfico 1: Comparativa de Modelos ML */}
            <Card style={{ padding: '14px 12px 10px 12px', overflow: 'hidden' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Cpu size={15} style={{ color: 'var(--primary)' }} />
                    <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                      Modelos de Machine Learning
                    </h4>
                  </div>
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                    F1-Score Macro vs Exactitud en 4-Fold GroupKFold
                  </span>
                </div>
              </div>

              <div style={{ width: '100%', height: 210 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={MODELOS_COMPARATIVA_DATA}
                    margin={{ top: 8, right: 4, left: -22, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis
                      dataKey="modelo"
                      stroke="#64748b"
                      fontSize={10}
                      tickLine={false}
                      interval={0}
                    />
                    <YAxis
                      domain={[90, 100]}
                      stroke="#64748b"
                      fontSize={10}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        borderColor: 'var(--border-color)',
                        borderRadius: '8px',
                        fontSize: '11px',
                        padding: '6px 10px',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                      }}
                      formatter={(val: unknown) => [`${val}%`, '']}
                      labelFormatter={(_label: unknown, payload: readonly { payload?: { modeloCompleto?: string } }[] | undefined) => {
                        if (payload && payload[0] && payload[0].payload) {
                          return payload[0].payload.modeloCompleto;
                        }
                        return String(_label ?? '');
                      }}
                    />
                    <Legend verticalAlign="top" height={28} wrapperStyle={{ fontSize: '11px' }} />
                    <Bar dataKey="f1_macro" fill="#2563eb" name="F1 Macro (%)" radius={[3, 3, 0, 0]} maxBarSize={24} />
                    <Bar dataKey="exactitud" fill="#06b6d4" name="Exactitud (%)" radius={[3, 3, 0, 0]} maxBarSize={24} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border-color)', fontSize: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#2563eb', flexShrink: 0 }} />
                  <span><strong>SVM:</strong> 97.37% (Ganador)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10b981', flexShrink: 0 }} />
                  <span><strong>R. Forest:</strong> 94.37%</span>
                </div>
              </div>
            </Card>

            {/* Gráfico 2: Desglose de Latencia del Pipeline Híbrido */}
            <Card style={{ padding: '14px 12px 10px 12px', overflow: 'hidden' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Zap size={15} style={{ color: '#d97706' }} />
                    <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                      Latencia por Componente
                    </h4>
                  </div>
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                    Tiempo de respuesta por etapa (milisegundos)
                  </span>
                </div>
              </div>

              <div style={{ width: '100%', height: 210 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={LATENCIAS_PIPELINE_DATA}
                    layout="vertical"
                    margin={{ top: 6, right: 20, left: -4, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                    <XAxis type="number" stroke="#64748b" fontSize={10} tickLine={false} unit=" ms" />
                    <YAxis dataKey="etapa" type="category" stroke="#64748b" fontSize={10} tickLine={false} width={75} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        borderColor: 'var(--border-color)',
                        borderRadius: '8px',
                        fontSize: '11px',
                        padding: '6px 10px',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                      }}
                      formatter={(val: unknown) => [`${val} ms`, 'Tiempo']}
                      labelFormatter={(_label: unknown, payload: readonly { payload?: { etapaCompleta?: string } }[] | undefined) => {
                        if (payload && payload[0] && payload[0].payload) {
                          return payload[0].payload.etapaCompleta;
                        }
                        return String(_label ?? '');
                      }}
                    />
                    <Bar dataKey="ms" radius={[0, 4, 4, 0]} maxBarSize={18}>
                      {LATENCIAS_PIPELINE_DATA.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border-color)', fontSize: '10px', color: 'var(--text-secondary)' }}>
                💡 <strong>Observación:</strong> El ML responde en <strong>12 ms</strong>, asegurando respuesta continua.
              </div>
            </Card>

            {/* Gráfico 3: Resiliencia del Sistema (Distribución de Fallback) */}
            <Card style={{ padding: '14px 12px 10px 12px', overflow: 'hidden' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <ShieldCheck size={15} style={{ color: '#059669' }} />
                    <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                      Resiliencia y Fallback
                    </h4>
                  </div>
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                    Disponibilidad ante contingencias de cuota Gemini
                  </span>
                </div>
              </div>

              <div style={{ width: '100%', height: 210 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                    <Pie
                      data={RESILIENCIA_DATA}
                      cx="50%"
                      cy="45%"
                      innerRadius={38}
                      outerRadius={62}
                      paddingAngle={3}
                      dataKey="value"
                      nameKey="name"
                    >
                      {RESILIENCIA_DATA.map((entry, index) => (
                        <Cell key={`res-cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        borderColor: 'var(--border-color)',
                        borderRadius: '8px',
                        fontSize: '11px',
                        padding: '6px 10px',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                      }}
                      formatter={(val: unknown) => [`${val}%`, 'Tasa']}
                    />
                    <Legend verticalAlign="bottom" height={32} wrapperStyle={{ fontSize: '10px' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border-color)', fontSize: '10px', color: 'var(--text-secondary)' }}>
                🛡️ <strong>100% de Disponibilidad</strong> gracias al modo degradado.
              </div>
            </Card>
          </div>

          {/* Conclusiones & Justificación de la Tesis */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '10px',
            }}
          >
            <Card style={{ padding: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                <BookOpen size={15} style={{ color: 'var(--primary)' }} />
                <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                  Hallazgo Clave: SVM vs Random Forest
                </h4>
              </div>
              <p style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.45, margin: 0 }}>
                En representaciones con <strong>TF-IDF (n-gramas 1-2)</strong>, el espacio vectorial es disperso. <strong>Linear SVM (97.37%)</strong> superó a <strong>Random Forest (94.37%)</strong> al hallar hiperplanos óptimos de separación sin sobreajuste por profundidad de árboles.
              </p>
            </Card>

            <Card style={{ padding: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                <ShieldCheck size={15} style={{ color: '#059669' }} />
                <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                  Arquitectura Híbrida y Resiliencia
                </h4>
              </div>
              <p style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.45, margin: 0 }}>
                La integración de <strong>RAG + Modo Degradado</strong> garantiza disponibilidad: si la API de Gemini se satura, el bot responde de inmediato con <strong>SVM + manual técnico OEM</strong> sin interrupción.
              </p>
            </Card>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* VISTA 3: FICHAS DE REGISTRO OFICIALES DE LA TESIS (PRE-TEST vs POST-TEST) */}
      {/* ========================================================================= */}
      {tabPrincipal === 'fichas_tesis' && <FichasTesisView />}
    </div>
  );
};
