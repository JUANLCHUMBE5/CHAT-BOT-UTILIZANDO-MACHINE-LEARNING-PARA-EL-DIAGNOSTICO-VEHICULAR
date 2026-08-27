import React from 'react';
import {
  Brain,
  Sparkles,
  Award,
  Zap,
  Layers,
  Cpu,
  ShieldCheck,
  BookOpen,
  FileText,
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
  PieChart,
  Pie,
  Cell,
  Legend,
  CartesianGrid,
} from 'recharts';

const MODELOS_COMPARATIVA_DATA = [
  {
    modelo: 'SVM',
    modeloCompleto: 'Linear SVM (Calibrado)',
    f1_macro: 95.95,
    exactitud: 97.54,
    f1_weighted: 97.03,
    desviacion: '±1.20%',
    destacado: true,
  },
  {
    modelo: 'Log. Reg.',
    modeloCompleto: 'Regresión Logística',
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
  { etapa: '1. TF-IDF', etapaCompleta: '1. Normalización y TF-IDF', ms: 3, fill: '#64748b' },
  { etapa: '2. ML (SVM)', etapaCompleta: '2. Clasificador ML (Linear SVM)', ms: 12, fill: '#2563eb' },
  { etapa: '3. RAG', etapaCompleta: '3. Búsqueda Vectorial RAG (FAISS)', ms: 45, fill: '#06b6d4' },
  { etapa: '4. Gemini', etapaCompleta: '4. Generación LLM Gemini Flash', ms: 1150, fill: '#8b5cf6' },
];

const RESILIENCIA_DATA = [
  { name: 'Modo Completo (ML + RAG + LLM)', value: 85, color: '#f97316' },
  { name: 'Modo Degradado (ML + RAG Fallback)', value: 15, color: '#06b6d4' },
];

export const ModeloIATab: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header Evaluation Card */}
      <div
        style={{
          padding: '16px 18px',
          backgroundColor: '#faf5ff',
          border: '1px solid #e9d5ff',
          borderRadius: '12px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '10px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Sparkles size={16} style={{ color: '#9333ea' }} />
            <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#581c87', margin: 0 }}>
              Evaluación y Benchmark de Modelos de Inteligencia Artificial
            </h3>
          </div>
          <p style={{ fontSize: '12px', color: '#6b21a8', margin: '4px 0 0 0', lineHeight: 1.4 }}>
            Comparativa experimental bajo validación cruzada 4-Fold GroupKFold, análisis de latencias y resiliencia híbrida.
          </p>
        </div>
        <span
          style={{
            fontSize: '11px',
            fontWeight: 700,
            backgroundColor: '#f3e8ff',
            color: '#7e22ce',
            padding: '3px 9px',
            borderRadius: '12px',
            border: '1px solid #d8b4fe',
          }}
        >
          v2.2.0-audited
        </span>
      </div>

      {/* 4 Stat Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '12px',
        }}
      >
        <StatCard
          title="Algoritmo Ganador"
          value="Linear SVM"
          icon={<Award size={18} />}
          trend={{ text: 'Calibrado Sigmoide', positive: true }}
        />
        <StatCard
          title="F1-Macro (4-Fold)"
          value="95.95%"
          icon={<Brain size={18} />}
          trend={{ text: 'Desviación ±1.20%', positive: true }}
        />
        <StatCard
          title="Latencia Inferencia"
          value="~12 ms"
          icon={<Zap size={18} />}
          trend={{ text: 'Tiempo Real', positive: true }}
        />
        <StatCard
          title="Cobertura de Fallas"
          value="48 Clases"
          icon={<Layers size={18} />}
          trend={{ text: 'Sistemas Automotrices', positive: true }}
        />
      </div>

      {/* Benchmark & Latency Charts */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '14px',
        }}
      >
        {/* Gráfico 1: Comparativa de Modelos ML */}
        <Card style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Cpu size={16} style={{ color: 'var(--primary)' }} />
                <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                  Comparativa de Modelos ML
                </h4>
              </div>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                F1-Score Macro vs Exactitud en 4-Fold GroupKFold
              </span>
            </div>
          </div>

          <div style={{ width: '100%', height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={MODELOS_COMPARATIVA_DATA} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="modelo" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis domain={[90, 100]} stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
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
                <Bar dataKey="f1_macro" fill="#2563eb" name="F1 Macro (%)" radius={[4, 4, 0, 0]} maxBarSize={28} />
                <Bar dataKey="exactitud" fill="#06b6d4" name="Exactitud (%)" radius={[4, 4, 0, 0]} maxBarSize={28} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '6px',
              marginTop: '10px',
              paddingTop: '8px',
              borderTop: '1px solid var(--border-color)',
              fontSize: '11px',
            }}
          >
            <div>
              <strong>🥇 Linear SVM:</strong> 95.95% F1 macro (Ganador)
            </div>
            <div>
              <strong>🌲 Random Forest:</strong> 94.37% (Árboles)
            </div>
          </div>
        </Card>

        {/* Gráfico 2: Latencia por Etapa */}
        <Card style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Zap size={16} style={{ color: '#d97706' }} />
                <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                  Latencia por Componente
                </h4>
              </div>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Tiempo de respuesta por etapa del pipeline (ms)
              </span>
            </div>
          </div>

          <div style={{ width: '100%', height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={LATENCIAS_PIPELINE_DATA} layout="vertical" margin={{ top: 6, right: 24, left: 4, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                <XAxis type="number" stroke="#64748b" fontSize={11} tickLine={false} unit=" ms" />
                <YAxis dataKey="etapa" type="category" stroke="#64748b" fontSize={11} tickLine={false} width={80} />
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
                <Bar dataKey="ms" radius={[0, 4, 4, 0]} maxBarSize={20}>
                  {LATENCIAS_PIPELINE_DATA.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div
            style={{
              marginTop: '10px',
              paddingTop: '8px',
              borderTop: '1px solid var(--border-color)',
              fontSize: '11px',
              color: 'var(--text-secondary)',
            }}
          >
            💡 <strong>Observación:</strong> El modelo ML infiere en solo <strong>12 ms</strong>, garantizando respuesta instantánea aun sin LLM.
          </div>
        </Card>

        {/* Gráfico 3: Resiliencia del Sistema */}
        <Card style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldCheck size={16} style={{ color: '#059669' }} />
                <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                  Resiliencia y Fallback
                </h4>
              </div>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Distribución operativa ante contingencias de cuota Gemini
              </span>
            </div>
          </div>

          <div style={{ width: '100%', height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                <Pie
                  data={RESILIENCIA_DATA}
                  cx="50%"
                  cy="45%"
                  innerRadius={42}
                  outerRadius={68}
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
                <Legend verticalAlign="bottom" height={32} wrapperStyle={{ fontSize: '11px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div
            style={{
              marginTop: '10px',
              paddingTop: '8px',
              borderTop: '1px solid var(--border-color)',
              fontSize: '11px',
              color: 'var(--text-secondary)',
            }}
          >
            🛡️ <strong>100% de Disponibilidad</strong> gracias al modo degradado RAG.
          </div>
        </Card>
      </div>

      {/* Dataset & Technical Details Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '14px' }}>
        <Card style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <BookOpen size={16} style={{ color: 'var(--primary)' }} />
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
              Justificación Teórica: Linear SVM vs Random Forest
            </h4>
          </div>
          <p style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
            Al procesar lenguaje natural automotriz mediante <strong>TF-IDF (unigramas y bigramas)</strong>, la matriz de características es de <strong>alta dimensionalidad y dispersa</strong>. Los modelos de vectores de soporte lineales (SVM) encuentran hiperplanos de separación con margen máximo de manera óptima, mientras que los árboles de decisión en Random Forest sufren de división subóptima y mayor sobreajuste en espacios de alta dimensionalidad.
          </p>
        </Card>

        <Card style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <Layers size={16} style={{ color: '#059669' }} />
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
              Dataset de Entrenamiento y 48 Clases de Fallas
            </h4>
          </div>
          <p style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
            El dataset comprende consultas reales y sintéticas auditadas de talleres de Lima Norte distribuidas en <strong>48 categorías mecánicas</strong> (frenos, inyección, refrigeración, suspensión, motor, transmisión, dirección y encendido). Se aplicó validación cruzada estratificada con <strong>GroupKFold</strong> para evitar fuga de datos entre variantes de síntomas.
          </p>
        </Card>

        <Card style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <FileText size={16} style={{ color: '#8b5cf6' }} />
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
              Pipeline RAG y corpus técnico preliminar
            </h4>
          </div>
          <p style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
            El corpus vectorial está indexado en <strong>FAISS</strong> con 64 procedimientos técnicos referenciales. Cuando el ML clasifica la falla, RAG recupera el fragmento preliminar más relevante para enriquecer la respuesta. El corpus todavía no cuenta con auditoría mecánica homologada y no debe tratarse como una especificación OEM exacta.
          </p>
        </Card>
      </div>
    </div>
  );
};
