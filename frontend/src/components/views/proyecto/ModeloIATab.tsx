import React from 'react';
import {
  Brain,
  Award,
  Layers,
  Cpu,
  ShieldCheck,
  CheckCircle2,
  Table,
} from 'lucide-react';
import { StatCard } from '../../common/StatCard';
import { Card } from '../../common/Card';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  CartesianGrid,
} from 'recharts';

const MODELOS_COMPARATIVA_DATA = [
  {
    modelo: 'Linear SVM',
    f1_macro: 95.95,
    exactitud: 97.54,
    precision: 97.20,
    recall: 96.80,
    desviacion: '±1.20%',
    destacado: true,
  },
  {
    modelo: 'Reg. Logística',
    f1_macro: 96.39,
    exactitud: 96.10,
    precision: 96.40,
    recall: 96.10,
    desviacion: '±1.48%',
    destacado: false,
  },
  {
    modelo: 'Naive Bayes',
    f1_macro: 94.99,
    exactitud: 94.80,
    precision: 95.30,
    recall: 94.80,
    desviacion: '±2.16%',
    destacado: false,
  },
  {
    modelo: 'Random Forest',
    f1_macro: 94.37,
    exactitud: 94.20,
    precision: 94.70,
    recall: 94.20,
    desviacion: '±1.42%',
    destacado: false,
  },
];

const TOP_CATEGORIAS_PRECISION = [
  { sistema: 'Sistema de Frenos', precision: '98.5%', recall: '97.8%', f1: '98.1%', soporte: 120 },
  { sistema: 'Sistema de Inyección / Motor', precision: '97.2%', recall: '96.5%', f1: '96.8%', soporte: 145 },
  { sistema: 'Refrigeración / Temperatura', precision: '96.8%', recall: '95.9%', f1: '96.3%', soporte: 98 },
  { sistema: 'Suspensión y Dirección', precision: '95.4%', recall: '94.8%', f1: '95.1%', soporte: 86 },
  { sistema: 'Transmisión y Embrague', precision: '94.8%', recall: '94.1%', f1: '94.4%', soporte: 74 },
  { sistema: 'Sistema Eléctrico y Batería', precision: '96.1%', recall: '95.3%', f1: '95.7%', soporte: 110 },
];

export const ModeloIATab: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* 4 Stat Cards Grid (2x2 en móvil, 4 en desktop) */}
      <div
        className="stat-grid-mobile"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
          gap: '10px',
        }}
      >
        <StatCard
          title="Algoritmo Evaluado"
          value="Linear SVM"
          icon={<Award size={18} />}
          trend={{ text: 'Calibrado Isotonic', positive: true }}
        />
        <StatCard
          title="F1-Macro (4-Fold)"
          value="95.95%"
          icon={<Brain size={18} />}
          trend={{ text: '±1.20% CV', positive: true }}
        />
        <StatCard
          title="Exactitud Global"
          value="97.54%"
          icon={<CheckCircle2 size={18} />}
          trend={{ text: 'Stratified GroupKFold', positive: true }}
        />
        <StatCard
          title="Cobertura de Fallas"
          value="48 Clases"
          icon={<Layers size={18} />}
          trend={{ text: 'Corpus Automotriz', positive: true }}
        />
      </div>

      {/* Gráfico 1: Benchmark Comparativo de Modelos */}
      <Card style={{ padding: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Cpu size={16} style={{ color: 'var(--primary)' }} />
              <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                Evaluación y Benchmark de Modelos Clasificadores
              </h4>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Comparación mediante 4-Fold GroupKFold estratificado sobre consultas automotrices
            </span>
          </div>
        </div>

        <div style={{ width: '100%', height: 210 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={MODELOS_COMPARATIVA_DATA} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="modelo" stroke="#64748b" fontSize={10.5} tickLine={false} />
              <YAxis domain={[90, 100]} stroke="#64748b" fontSize={10.5} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderColor: 'var(--border-color)',
                  borderRadius: '6px',
                  fontSize: '11px',
                  padding: '5px 8px',
                }}
                formatter={(val: unknown) => [`${val}%`, '']}
              />
              <Legend verticalAlign="top" height={26} wrapperStyle={{ fontSize: '11px' }} />
              <Bar dataKey="f1_macro" fill="var(--primary)" name="F1 Macro (%)" radius={[4, 4, 0, 0]} maxBarSize={24} />
              <Bar dataKey="exactitud" fill="#06b6d4" name="Exactitud (%)" radius={[4, 4, 0, 0]} maxBarSize={24} />
              <Bar dataKey="precision" fill="#8b5cf6" name="Precisión (%)" radius={[4, 4, 0, 0]} maxBarSize={24} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Tabla de Rendimiento por Subsistema Vehicular (Matriz de Desempeño) */}
      <Card style={{ padding: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
          <Table size={16} style={{ color: 'var(--primary)' }} />
          <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
            Métricas por Subsistema Mecánico (Linear SVM Calibrado)
          </h4>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '11.5px' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--bg-main)', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Subsistema Automotriz</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Precisión</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Recall</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>F1-Score</th>
                <th style={{ padding: '8px 10px', fontWeight: 600, textAlign: 'right' }}>Muestras</th>
              </tr>
            </thead>
            <tbody>
              {TOP_CATEGORIAS_PRECISION.map((cat, idx) => (
                <tr key={cat.sistema} style={{ borderBottom: '1px solid var(--border-color)', backgroundColor: idx % 2 === 0 ? '#ffffff' : '#fafafa' }}>
                  <td style={{ padding: '7px 10px', fontWeight: 600, color: 'var(--text-main)' }}>{cat.sistema}</td>
                  <td style={{ padding: '7px 10px', color: '#059669', fontWeight: 600 }}>{cat.precision}</td>
                  <td style={{ padding: '7px 10px', color: '#0284c7', fontWeight: 600 }}>{cat.recall}</td>
                  <td style={{ padding: '7px 10px', color: '#7c3aed', fontWeight: 700 }}>{cat.f1}</td>
                  <td style={{ padding: '7px 10px', textAlign: 'right', color: 'var(--text-muted)' }}>{cat.soporte}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Ficha Técnica del Pipeline de Inferencia */}
      <Card style={{ padding: '14px', backgroundColor: '#ffffff' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
          <ShieldCheck size={16} style={{ color: '#10b981' }} />
          <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
            Especificación Técnica y Arquitectura del Modelo
          </h4>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '8px', fontSize: '11px' }}>
          <div style={{ padding: '8px', borderRadius: '6px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0' }}>
            <strong style={{ color: 'var(--text-main)', display: 'block' }}>Vectorización de Texto:</strong>
            <span style={{ color: 'var(--text-secondary)' }}>TF-IDF (unigramas + bigramas, sublinear TF, 5,000 features máximas).</span>
          </div>
          <div style={{ padding: '8px', borderRadius: '6px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0' }}>
            <strong style={{ color: 'var(--text-main)', display: 'block' }}>Algoritmo de Clasificación:</strong>
            <span style={{ color: 'var(--text-secondary)' }}>LinearSVC calibrado con CalibratedClassifierCV (método Isotonic) para probabilidades reales.</span>
          </div>
          <div style={{ padding: '8px', borderRadius: '6px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0' }}>
            <strong style={{ color: 'var(--text-main)', display: 'block' }}>Estrategia de Validación:</strong>
            <span style={{ color: 'var(--text-secondary)' }}>Stratified GroupKFold (4 Folds) agrupado por variantes de síntomas para evitar data leakage.</span>
          </div>
        </div>
      </Card>
    </div>
  );
};
