import React from 'react';
import { RefreshCw, Calendar } from 'lucide-react';
import { periodoDias, type Periodo } from '../../../utils/periodo';

interface DiagnosticosPeriodoBarProps {
  periodo: Periodo;
  periodoExterno?: Periodo;
  mostrarRangoFechas: boolean;
  setMostrarRangoFechas: (val: boolean) => void;
  seleccionarPresetPeriodo: (dias?: number) => void;
  rangoFechas: Periodo;
  setRangoFechas: React.Dispatch<React.SetStateAction<Periodo>>;
  aplicarRangoPersonalizado: () => void;
  fechaInvalida: boolean;
  cargando: boolean;
  onActualizar: () => void;
}

export const DiagnosticosPeriodoBar: React.FC<DiagnosticosPeriodoBarProps> = ({
  periodo,
  periodoExterno,
  mostrarRangoFechas,
  setMostrarRangoFechas,
  seleccionarPresetPeriodo,
  rangoFechas,
  setRangoFechas,
  aplicarRangoPersonalizado,
  fechaInvalida,
  cargando,
  onActualizar,
}) => {
  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
        {!periodoExterno && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              backgroundColor: '#f8fafc',
              padding: '3px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              gap: '2px',
            }}
          >
            <button
              type="button"
              onClick={() => seleccionarPresetPeriodo()}
              style={{
                padding: '4px 9px',
                fontSize: '11px',
                fontWeight: 600,
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: !periodo.fecha_desde && !periodo.fecha_hasta ? 'var(--primary)' : 'transparent',
                color: !periodo.fecha_desde && !periodo.fecha_hasta ? '#ffffff' : 'var(--text-secondary)',
                transition: 'all 0.15s ease',
              }}
            >
              Todo
            </button>
            <button
              type="button"
              onClick={() => seleccionarPresetPeriodo(7)}
              style={{
                padding: '4px 9px',
                fontSize: '11px',
                fontWeight: 600,
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor:
                  periodo.fecha_desde === periodoDias(7).fecha_desde ? 'var(--primary)' : 'transparent',
                color:
                  periodo.fecha_desde === periodoDias(7).fecha_desde ? '#ffffff' : 'var(--text-secondary)',
                transition: 'all 0.15s ease',
              }}
            >
              7 días
            </button>
            <button
              type="button"
              onClick={() => seleccionarPresetPeriodo(14)}
              style={{
                padding: '4px 9px',
                fontSize: '11px',
                fontWeight: 600,
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor:
                  periodo.fecha_desde === periodoDias(14).fecha_desde ? 'var(--primary)' : 'transparent',
                color:
                  periodo.fecha_desde === periodoDias(14).fecha_desde ? '#ffffff' : 'var(--text-secondary)',
                transition: 'all 0.15s ease',
              }}
            >
              14 días
            </button>
            <button
              type="button"
              onClick={() => setMostrarRangoFechas(!mostrarRangoFechas)}
              style={{
                padding: '4px 8px',
                fontSize: '11px',
                fontWeight: 600,
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: mostrarRangoFechas ? '#e2e8f0' : 'transparent',
                color: 'var(--text-secondary)',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
              title="Seleccionar fechas personalizadas"
            >
              <Calendar size={12} />
              <span>Fechas</span>
            </button>
          </div>
        )}

        <button
          type="button"
          onClick={onActualizar}
          disabled={cargando}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            padding: '5px 10px',
            backgroundColor: '#ffffff',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            fontSize: '11px',
            fontWeight: 600,
            cursor: cargando ? 'not-allowed' : 'pointer',
            color: 'var(--text-secondary)',
          }}
        >
          <RefreshCw size={12} className={cargando ? 'animate-spin' : ''} />
          <span>Actualizar</span>
        </button>
      </div>

      {mostrarRangoFechas && !periodoExterno && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 12px',
            backgroundColor: '#f8fafc',
            borderRadius: '6px',
            border: '1px solid var(--border-color)',
            fontSize: '12px',
            flexWrap: 'wrap',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Desde:</span>
            <input
              type="date"
              value={rangoFechas.fecha_desde || ''}
              onChange={(e) =>
                setRangoFechas((prev) => ({
                  ...prev,
                  fecha_desde: e.target.value || undefined,
                }))
              }
              style={{
                padding: '3px 6px',
                fontSize: '11px',
                borderRadius: '4px',
                border: '1px solid var(--border-color)',
              }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Hasta:</span>
            <input
              type="date"
              value={rangoFechas.fecha_hasta || ''}
              onChange={(e) =>
                setRangoFechas((prev) => ({
                  ...prev,
                  fecha_hasta: e.target.value || undefined,
                }))
              }
              style={{
                padding: '3px 6px',
                fontSize: '11px',
                borderRadius: '4px',
                border: '1px solid var(--border-color)',
              }}
            />
          </div>
          <button
            type="button"
            onClick={aplicarRangoPersonalizado}
            disabled={fechaInvalida}
            style={{
              padding: '3px 10px',
              fontSize: '11px',
              fontWeight: 600,
              borderRadius: '4px',
              backgroundColor: fechaInvalida ? '#e2e8f0' : 'var(--primary)',
              color: fechaInvalida ? 'var(--text-muted)' : '#ffffff',
              border: 'none',
              cursor: fechaInvalida ? 'not-allowed' : 'pointer',
            }}
          >
            Aplicar
          </button>
          {fechaInvalida && (
            <span style={{ color: '#ef4444', fontSize: '11px' }}>
              La fecha inicial no puede ser posterior a la final.
            </span>
          )}
        </div>
      )}
    </>
  );
};
