import React from 'react';
import { Search, X, FileText } from 'lucide-react';
import type { Diagnostico, Mecanico } from '../../types';
import { DiagnosticosTabla, DiagnosticoDetalleModal } from './diagnosticos';
import { Card } from '../common/Card';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { limitesDiagnosticos, type Periodo } from '../../utils/periodo';
import { useDiagnosticosFilter } from './diagnosticos/hooks/useDiagnosticosFilter';
import { DiagnosticosPeriodoBar } from './diagnosticos/DiagnosticosPeriodoBar';

export interface DiagnosticosViewProps {
  diagnosticos: Diagnostico[];
  totalDiagnosticos: number;
  cargando?: boolean;
  mecanicos: Mecanico[];
  initialFiltroMecanico?: string;
  onFiltroMecanicoSeleccionado?: (id: string) => void;
  onFiltrar?: (filtros: {
    busqueda?: string;
    estado?: string;
    modo?: string;
    mecanico_id?: string;
    limite?: number;
    offset?: number;
    fecha_desde?: string;
    fecha_hasta?: string;
  }) => Promise<void>;
  error?: string | null;
  refreshKey?: number;
  diagnosticoSeleccionadoModal?: Diagnostico | null;
  onCerrarModalDetalle: () => void;
  onAbrirModalDetalle: (diag: Diagnostico) => void;
  periodoExterno?: Periodo;
}

export const DiagnosticosView: React.FC<DiagnosticosViewProps> = ({
  diagnosticos,
  totalDiagnosticos,
  cargando = false,
  mecanicos,
  initialFiltroMecanico,
  onFiltroMecanicoSeleccionado,
  onFiltrar,
  error,
  refreshKey = 0,
  diagnosticoSeleccionadoModal,
  onCerrarModalDetalle,
  onAbrirModalDetalle,
  periodoExterno,
}) => {
  const {
    filtros,
    setFiltros,
    periodo,
    rangoFechas,
    setRangoFechas,
    mostrarRangoFechas,
    setMostrarRangoFechas,
    totalPaginas,
    mecanicoSeleccionado,
    seleccionarPresetPeriodo,
    fechaInvalida,
    aplicarRangoPersonalizado,
  } = useDiagnosticosFilter({
    totalDiagnosticos,
    mecanicos,
    initialFiltroMecanico,
    onFiltrar,
    refreshKey,
    periodoExterno,
  });

  const ejecutarFiltroActual = () => {
    void onFiltrar?.({
      busqueda: filtros.busqueda.trim() || undefined,
      estado: filtros.estado || undefined,
      mecanico_id: filtros.mecanico !== 'todos' ? filtros.mecanico : undefined,
      limite: 10,
      offset: (filtros.pagina - 1) * 10,
      ...limitesDiagnosticos(periodo),
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {error && (
        <div className="inline-error" role="alert">
          {error}
        </div>
      )}

      {/* Tarjeta Unificada de Control y Período */}
      <Card
        style={{
          padding: '12px 16px',
          backgroundColor: '#ffffff',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '10px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                backgroundColor: 'rgba(234, 88, 12, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--primary)',
              }}
            >
              <FileText size={16} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                <h3 style={{ fontSize: '15px', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
                  Historial de Diagnósticos
                </h3>
                <span
                  style={{
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontSize: '11px',
                    fontWeight: 700,
                    backgroundColor: 'rgba(234, 88, 12, 0.1)',
                    color: 'var(--primary)',
                  }}
                >
                  {totalDiagnosticos} registros
                </span>

                {mecanicoSeleccionado && (
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '5px',
                      padding: '2px 8px',
                      borderRadius: '8px',
                      backgroundColor: '#f1f5f9',
                      border: '1px solid var(--border-color)',
                      fontSize: '11px',
                      fontWeight: 600,
                      color: 'var(--text-main)',
                    }}
                  >
                    <span>Mecánico: {mecanicoSeleccionado.nombres}</span>
                    <button
                      type="button"
                      onClick={() => {
                        setFiltros((f) => ({ ...f, mecanico: 'todos', pagina: 1 }));
                        onFiltroMecanicoSeleccionado?.('todos');
                      }}
                      style={{
                        border: 'none',
                        background: 'transparent',
                        padding: '1px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        color: 'var(--text-muted)',
                      }}
                      title="Quitar filtro de mecánico"
                    >
                      <X size={12} />
                    </button>
                  </span>
                )}
              </div>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Mostrando {diagnosticos.length} por página · Auditoría técnica vehicular y trazabilidad IA
              </span>
            </div>
          </div>

          <DiagnosticosPeriodoBar
            periodo={periodo}
            periodoExterno={periodoExterno}
            mostrarRangoFechas={mostrarRangoFechas}
            setMostrarRangoFechas={setMostrarRangoFechas}
            seleccionarPresetPeriodo={seleccionarPresetPeriodo}
            rangoFechas={rangoFechas}
            setRangoFechas={setRangoFechas}
            aplicarRangoPersonalizado={aplicarRangoPersonalizado}
            fechaInvalida={fechaInvalida}
            cargando={cargando}
            onActualizar={ejecutarFiltroActual}
          />
        </div>

        {/* Barra de Filtros Compacta e Integrada */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            flexWrap: 'wrap',
            paddingTop: '8px',
            borderTop: '1px solid #f1f5f9',
          }}
        >
          <div style={{ flex: '1 1 240px', minWidth: '180px' }}>
            <Input
              placeholder="Buscar síntoma, falla o mecánico..."
              value={filtros.busqueda}
              onChange={(event) =>
                setFiltros((f) => ({ ...f, busqueda: event.target.value, pagina: 1 }))
              }
              icon={<Search size={14} />}
              style={{
                height: '34px',
                padding: '0 12px 0 34px',
                fontSize: '12.5px',
              }}
            />
          </div>

          <div style={{ width: '160px', flexShrink: 0 }}>
            <Select
              value={filtros.estado}
              onChange={(event) =>
                setFiltros((f) => ({ ...f, estado: event.target.value, pagina: 1 }))
              }
              style={{
                height: '34px',
                padding: '0 10px',
                fontSize: '12.5px',
              }}
              options={[
                { value: '', label: 'Todos los estados' },
                ...['generado', 'en_revision', 'confirmado', 'descartado'].map((value) => ({
                  value,
                  label: value.replace('_', ' '),
                })),
              ]}
            />
          </div>

          {mecanicos.length > 0 && (
            <div style={{ width: '180px', flexShrink: 0 }}>
              <Select
                value={filtros.mecanico}
                onChange={(event) => {
                  setFiltros((f) => ({ ...f, mecanico: event.target.value, pagina: 1 }));
                  onFiltroMecanicoSeleccionado?.(event.target.value);
                }}
                style={{
                  height: '34px',
                  padding: '0 10px',
                  fontSize: '12.5px',
                }}
                options={[
                  { value: 'todos', label: 'Todos los mecánicos' },
                  ...mecanicos.map((mecanico) => ({ value: mecanico.id, label: mecanico.nombres })),
                ]}
              />
            </div>
          )}

          {Boolean(filtros.busqueda.trim() || filtros.estado || filtros.mecanico !== 'todos') && (
            <button
              type="button"
              onClick={() => {
                setFiltros((f) => ({ ...f, busqueda: '', estado: '', mecanico: 'todos', pagina: 1 }));
                onFiltroMecanicoSeleccionado?.('todos');
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '0 10px',
                height: '34px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#ffffff',
                color: 'var(--text-secondary)',
                fontSize: '11.5px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
              title="Limpiar filtros"
            >
              <X size={12} />
              <span>Limpiar</span>
            </button>
          )}
        </div>
      </Card>

      {/* Tabla de Diagnósticos */}
      <DiagnosticosTabla
        diagnosticosPaginados={diagnosticos}
        cargando={cargando}
        totalProcesados={totalDiagnosticos}
        paginaActual={filtros.pagina}
        totalPaginas={totalPaginas}
        elementosPorPagina={10}
        onCambiarPagina={(pagina) =>
          setFiltros((f) => ({ ...f, pagina: Math.max(1, Math.min(pagina, totalPaginas)) }))
        }
        onElementosPorPaginaChange={() => {}}
        onVerDetalle={onAbrirModalDetalle}
      />

      <DiagnosticoDetalleModal
        diagnostico={diagnosticoSeleccionadoModal || null}
        isOpen={Boolean(diagnosticoSeleccionadoModal)}
        onClose={onCerrarModalDetalle}
      />
    </div>
  );
};
