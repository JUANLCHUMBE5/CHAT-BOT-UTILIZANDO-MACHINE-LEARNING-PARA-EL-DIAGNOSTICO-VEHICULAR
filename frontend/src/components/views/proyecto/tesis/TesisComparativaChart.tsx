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
import { Card } from '../../../common/Card';

interface TesisComparativaChartProps {
  data: { indicador: string; 'Pre-test (Manual)': number; 'Post-test (CarBot AI)': number }[];
}

export const TesisComparativaChart: React.FC<TesisComparativaChartProps> = ({
  data,
}) => {
  return (
    <Card style={{ backgroundColor: '#ffffff', padding: '16px' }}>
      <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-main)', margin: '0 0 12px 0' }}>
        Comparativa Integral de las 3 Fichas de Tesis (Pre-test vs Post-test)
      </h4>
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
