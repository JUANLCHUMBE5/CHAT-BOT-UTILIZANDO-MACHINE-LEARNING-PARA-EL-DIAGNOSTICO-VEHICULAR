import { Calendar, TrendingUp, CheckCircle, Clock } from 'lucide-react';
import { StatCard } from '../common/StatCard';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import type { ResumenMetricas, Diagnostico } from '../../types';
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
  diagnosticosRecientes: Diagnostico[];
  onVerDiagnostico: (diag: Diagnostico) => void;
}

const MODOS_COLORS: Record<string, string> = {
  completo_ml_rag_llm: '#ea580c',
  diagnostico_degradado_ml_rag: '#64748b',
  saludo: '#0284c7',
  en_cola_gemini: '#d97706',
  baja_confianza: '#ca8a04',
};

export const DashboardView: React.FC<DashboardViewProps> = ({
  metricas,
  diagnosticosRecientes,
  onVerDiagnostico,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* View Title */}
      <div>
        <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-main)' }}>
          Resumen Ejecutivo de Diagnósticos
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Métricas consolidadas de hoy, esta semana y este mes en Taller Carabayllo.
        </p>
      </div>

      {/* Metric Cards Grid (Hoy, Semana, Mes, Confirmados %) */}
      <div
        className="stat-grid-mobile"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '12px',
        }}
      >
        <StatCard
          title="Diagnósticos Hoy"
          value={metricas.diagnosticos_hoy}
          subtitle="Vía WhatsApp"
          icon={<Calendar size={18} />}
          trend={{ text: '+15% vs ayer', positive: true }}
        />
        <StatCard
          title="Esta Semana"
          value={metricas.diagnosticos_semana}
          subtitle="Últimos 7 días"
          icon={<TrendingUp size={18} />}
          trend={{ text: '+8% vs sem. previa', positive: true }}
        />
        <StatCard
          title="Este Mes"
          value={metricas.diagnosticos_mes}
          subtitle="Mes actual"
          icon={<Clock size={18} />}
        />
        <StatCard
          title="Precisión"
          value={`${metricas.porcentaje_confirmados}%`}
          subtitle="Confirmados por mecánico"
          icon={<CheckCircle size={18} />}
          trend={{ text: 'Validez Tesis UCV', positive: true }}
        />
      </div>

      {/* Charts Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '16px',
        }}
      >
        {/* Bar Chart: Volúmen diario */}
        <Card title="Volumen de Diagnósticos Diarios (Semana Actual)">
          <div className="chart-container-mobile" style={{ width: '100%', height: 180, marginTop: '8px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metricas.actividad_diaria}>
                <XAxis dataKey="fecha" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderColor: '#e2e8f0',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="cantidad" fill="#ea580c" radius={[4, 4, 0, 0]} name="Diagnósticos" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Donut Chart: Modos de Diagnóstico (ML+RAG+LLM vs Degradado vs Saludo) */}
        <Card title="Distribución por Modo de Diagnóstico">
          <div className="chart-container-mobile" style={{ width: '100%', height: 180, marginTop: '8px', display: 'flex', alignItems: 'center' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={metricas.distribucion_modos}
                  dataKey="cantidad"
                  nameKey="modo"
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={65}
                  paddingAngle={4}
                >
                  {metricas.distribucion_modos.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={MODOS_COLORS[entry.modo] || '#ea580c'}
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val, name) => [
                    `${val} solicitudes`,
                    name === 'completo_ml_rag_llm' ? 'Síntesis Gemini ML+RAG' : name,
                  ]}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderColor: '#e2e8f0',
                    borderRadius: '8px',
                    fontSize: '13px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Two Column Grid: Fallas Frecuentes & Recent Activity */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '20px',
        }}
      >
        {/* Top Fallas Vehiculares */}
        <Card title="Fallas Mecánicas Más Frecuentes (Carabayllo)">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '8px' }}>
            {metricas.fallas_frecuentes.map((item, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 12px',
                  backgroundColor: 'var(--bg-subtle)',
                  borderRadius: '8px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span
                    style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--primary-light)',
                      color: 'var(--primary)',
                      fontWeight: 700,
                      fontSize: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {idx + 1}
                  </span>
                  <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-main)' }}>
                    {item.falla}
                  </span>
                </div>
                <span
                  style={{
                    fontSize: '12px',
                    fontWeight: 600,
                    padding: '2px 8px',
                    borderRadius: '9999px',
                    backgroundColor: '#ffffff',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  {item.cantidad} casos
                </span>
              </div>
            ))}
          </div>
        </Card>

        {/* Últimos Diagnósticos Registrados */}
        <Card title="Últimos Diagnósticos en Taller">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '8px' }}>
            {diagnosticosRecientes.slice(0, 4).map((diag) => (
              <div
                key={diag.id}
                onClick={() => onVerDiagnostico(diag)}
                style={{
                  padding: '12px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-color)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  backgroundColor: '#ffffff',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--primary)';
                  e.currentTarget.style.backgroundColor = 'var(--primary-light)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-color)';
                  e.currentTarget.style.backgroundColor = '#ffffff';
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--primary)' }}>
                    {diag.placa_vehiculo} — {diag.marca_modelo}
                  </span>
                  <Badge type={diag.estado} size="sm" />
                </div>
                <p style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', marginTop: '4px' }}>
                  {diag.falla_predicha}
                </p>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '6px', fontSize: '11px', color: 'var(--text-muted)' }}>
                  <span>Confianza ML: {diag.confianza}%</span>
                  <span>{diag.fecha_hora}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};
