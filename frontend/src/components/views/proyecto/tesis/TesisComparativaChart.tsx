import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';
import { AlertTriangle, BarChart3 } from 'lucide-react';
import { Card } from '../../../common/Card';
import { Button } from '../../../common/Button';

export interface ComparativaDataRow {
  indicador: string;
  'Pre-test (Manual)': number;
  'Post-test (CarBot AI)': number;
}

interface TesisComparativaChartProps {
  data: ComparativaDataRow[];
  esModoDemo?: boolean;
  onAlternarDemo?: () => void;
  tieneDatosAmbasFases?: boolean;
  casosPretest?: number;
  casosPosttest?: number;
}

export const TesisComparativaChart: React.FC<TesisComparativaChartProps> = ({
  data,
  esModoDemo = false,
  onAlternarDemo,
  tieneDatosAmbasFases = false,
  casosPretest = 0,
  casosPosttest = 0,
}) => {
  // Si no está en modo demo y faltan registros en alguna de las dos fases del trabajo de campo
  if (!esModoDemo && !tieneDatosAmbasFases) {
    return (
      <Card style={{ backgroundColor: '#ffffff', padding: '24px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '12px' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              backgroundColor: '#f1f5f9',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#64748b',
            }}
          >
            <BarChart3 size={24} />
          </div>
          <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
            Comparación pendiente de completar ambas fases del trabajo de campo
          </h4>
          <p style={{ fontSize: '13px', color: '#64748b', maxWidth: '520px', margin: 0, lineHeight: 1.5 }}>
            La gráfica comparativa oficial de la tesis requiere registros verificados tanto en la fase Pre-test
            como en Post-test. Actualmente registrados en taller: <strong>{casosPretest} Pre-test</strong> y{' '}
            <strong>{casosPosttest} Post-test</strong> (muestra oficial requerida: 30 casos en cada fase).
          </p>
          {onAlternarDemo && (
            <Button variant="secondary" size="sm" onClick={onAlternarDemo} style={{ marginTop: '6px' }}>
              Ver simulación con datos de demostración
            </Button>
          )}
        </div>
      </Card>
    );
  }

  return (
    <Card style={{ backgroundColor: '#ffffff', padding: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
        <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
          Comparativa Integral de las 3 Fichas de Tesis (Pre-test vs Post-test)
        </h4>
        {onAlternarDemo && (
          <Button
            variant={esModoDemo ? 'primary' : 'secondary'}
            size="sm"
            onClick={onAlternarDemo}
            style={{ fontSize: '11px', padding: '4px 10px' }}
          >
            {esModoDemo ? 'Volver a Datos Reales' : 'Ver Modo Demostración'}
          </Button>
        )}
      </div>

      {esModoDemo && (
        <div
          style={{
            backgroundColor: '#fffbeb',
            border: '1px solid #fde68a',
            borderRadius: '6px',
            padding: '8px 12px',
            marginBottom: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: '#92400e',
            fontWeight: 600,
          }}
        >
          <AlertTriangle size={16} style={{ flexShrink: 0 }} />
          <span>
            MODO DEMOSTRACIÓN: Esta gráfica muestra 60 registros sintéticos simulados. Los resultados oficiales de la tesis
            se obtendrán exclusivamente tras culminar el trabajo de campo real en el taller.
          </span>
        </div>
      )}

      <div style={{ height: '240px', width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis dataKey="indicador" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderRadius: '8px',
                border: '1px solid #cbd5e1',
                fontSize: '12px',
              }}
            />
            <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
            <Bar dataKey="Pre-test (Manual)" fill="#94a3b8" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Post-test (CarBot AI)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};
