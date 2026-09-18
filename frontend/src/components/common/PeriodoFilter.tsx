import { useState } from 'react';
import { Calendar } from 'lucide-react';
import { periodoDias, type Periodo } from '../../utils/periodo';

export function PeriodoFilter({ value, onChange }: { value: Periodo; onChange: (p: Periodo) => void }) {
  const [rango, setRango] = useState(value);
  const invalido = Boolean(rango.fecha_desde && rango.fecha_hasta && rango.fecha_desde > rango.fecha_hasta);
  const seleccionar = (p: Periodo) => {
    setRango(p);
    onChange(p);
  };

  const esActivo = (dias?: number) => {
    if (!dias) return !value.fecha_desde && !value.fecha_hasta;
    const p = periodoDias(dias);
    return value.fecha_desde === p.fecha_desde && value.fecha_hasta === p.fecha_hasta;
  };

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        backgroundColor: '#ffffff',
        border: '1px solid var(--border-color, #e2e8f0)',
        borderRadius: '8px',
        padding: '3px 8px',
        boxShadow: '0 1px 2px rgba(0, 0, 0, 0.04)',
        flexWrap: 'wrap',
      }}
      aria-label="Período de consulta"
    >
      {/* Segmented Preset Pills */}
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          backgroundColor: '#f1f5f9',
          borderRadius: '6px',
          padding: '2px',
          gap: '2px',
        }}
      >
        <button
          type="button"
          onClick={() => seleccionar(periodoDias(7))}
          style={{
            border: 'none',
            borderRadius: '5px',
            padding: '3px 8px',
            fontSize: '11px',
            fontWeight: esActivo(7) ? 700 : 500,
            backgroundColor: esActivo(7) ? 'var(--primary, #ea580c)' : 'transparent',
            color: esActivo(7) ? '#ffffff' : '#64748b',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          7 días
        </button>
        <button
          type="button"
          onClick={() => seleccionar(periodoDias(14))}
          style={{
            border: 'none',
            borderRadius: '5px',
            padding: '3px 8px',
            fontSize: '11px',
            fontWeight: esActivo(14) ? 700 : 500,
            backgroundColor: esActivo(14) ? 'var(--primary, #ea580c)' : 'transparent',
            color: esActivo(14) ? '#ffffff' : '#64748b',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          14 días
        </button>
        <button
          type="button"
          onClick={() => seleccionar({})}
          style={{
            border: 'none',
            borderRadius: '5px',
            padding: '3px 8px',
            fontSize: '11px',
            fontWeight: esActivo() ? 700 : 500,
            backgroundColor: esActivo() ? 'var(--primary, #ea580c)' : 'transparent',
            color: esActivo() ? '#ffffff' : '#64748b',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          Todo
        </button>
      </div>

      {/* Separador vertical */}
      <div style={{ width: '1px', height: '16px', backgroundColor: '#e2e8f0', margin: '0 2px' }} />

      {/* Rango de fechas compacto */}
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
        <Calendar size={13} style={{ color: '#94a3b8' }} />
        <input
          type="date"
          value={rango.fecha_desde || ''}
          onChange={(e) => setRango({ ...rango, fecha_desde: e.target.value || undefined })}
          style={{
            padding: '2px 6px',
            fontSize: '11px',
            border: '1px solid #cbd5e1',
            borderRadius: '5px',
            color: '#334155',
            outline: 'none',
            height: '24px',
            backgroundColor: '#f8fafc',
          }}
        />
        <span style={{ fontSize: '11px', color: '#94a3b8' }}>al</span>
        <input
          type="date"
          value={rango.fecha_hasta || ''}
          onChange={(e) => setRango({ ...rango, fecha_hasta: e.target.value || undefined })}
          style={{
            padding: '2px 6px',
            fontSize: '11px',
            border: '1px solid #cbd5e1',
            borderRadius: '5px',
            color: '#334155',
            outline: 'none',
            height: '24px',
            backgroundColor: '#f8fafc',
          }}
        />
        <button
          type="button"
          disabled={invalido}
          onClick={() => onChange(rango)}
          style={{
            padding: '2px 10px',
            height: '24px',
            fontSize: '11px',
            fontWeight: 600,
            backgroundColor: invalido ? '#f1f5f9' : '#0f172a',
            color: invalido ? '#94a3b8' : '#ffffff',
            border: 'none',
            borderRadius: '5px',
            cursor: invalido ? 'not-allowed' : 'pointer',
            transition: 'background 0.15s ease',
          }}
        >
          Aplicar
        </button>
      </div>

      {invalido && (
        <span style={{ fontSize: '10px', color: '#dc2626', fontWeight: 600, marginLeft: '4px' }} role="alert">
          Fecha inicial mayor
        </span>
      )}
    </div>
  );
}
