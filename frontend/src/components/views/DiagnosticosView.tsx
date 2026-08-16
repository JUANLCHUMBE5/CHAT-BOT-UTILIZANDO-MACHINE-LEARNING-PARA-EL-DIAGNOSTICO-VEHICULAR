import React, { useState, useMemo } from 'react';
import {
  Search,
  FileText,
  Clock,
  Cpu,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { Modal } from '../common/Modal';
import type { Diagnostico, EstadoDiagnostico, Mecanico, UsuarioSesion } from '../../types';

interface DiagnosticosViewProps {
  diagnosticos: Diagnostico[];
  cargando?: boolean;
  mecanicos: Mecanico[];
  currentUser?: UsuarioSesion | null;
  onActualizarEstado: (id: string, nuevoEstado: EstadoDiagnostico, notas?: string) => Promise<void>;
  onFiltrar?: (filtros: { busqueda?: string; estado?: string; modo?: string; mecanico_id?: string }) => Promise<void>;
  diagnosticoSeleccionadoModal?: Diagnostico | null;
  onCerrarModalDetalle: () => void;
  onAbrirModalDetalle: (diag: Diagnostico) => void;
}

type FiltroFecha = 'todos' | 'hoy' | '7dias' | 'esteMes';
type TipoOrden = 'pendientes_primero' | 'fecha_desc' | 'fecha_asc' | 'confianza_desc' | 'confianza_asc';

export const DiagnosticosView: React.FC<DiagnosticosViewProps> = ({
  diagnosticos,
  cargando = false,
  mecanicos,
  currentUser: _currentUser,
  onActualizarEstado,
  onFiltrar,
  diagnosticoSeleccionadoModal,
  onCerrarModalDetalle,
  onAbrirModalDetalle,
}) => {
  // Filter States
  const [busqueda, setBusqueda] = useState('');
  const [filtroEstado, setFiltroEstado] = useState('todos');
  const [filtroModo, setFiltroModo] = useState('todos');
  const [filtroMecanico, setFiltroMecanico] = useState('todos');
  const [filtroFecha, setFiltroFecha] = useState<FiltroFecha>('todos');
  const [orden, setOrden] = useState<TipoOrden>('pendientes_primero');

  // Pagination States
  const [paginaActual, setPaginaActual] = useState(1);
  const [elementosPorPagina, setElementosPorPagina] = useState(10);

  // Trigger backend filtering with 300ms debounce on search
  React.useEffect(() => {
    const timer = setTimeout(() => {
      if (onFiltrar) {
        onFiltrar({
          busqueda: busqueda.trim() || undefined,
          estado: filtroEstado !== 'todos' ? filtroEstado : undefined,
          modo: filtroModo !== 'todos' ? filtroModo : undefined,
          mecanico_id: filtroMecanico !== 'todos' ? filtroMecanico : undefined,
        });
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [busqueda, filtroEstado, filtroModo, filtroMecanico, onFiltrar]);

  // Reset pagination when filters change
  React.useEffect(() => {
    setPaginaActual(1);
  }, [busqueda, filtroEstado, filtroModo, filtroMecanico, filtroFecha, orden]);

  // Confirmation Form State inside Detail Modal
  const [nuevoEstado, setNuevoEstado] = useState<EstadoDiagnostico>('confirmado');
  const [notasMecanico, setNotasMecanico] = useState('');
  const [guardando, setGuardando] = useState(false);
  const [errorGuardado, setErrorGuardado] = useState('');

  // Process list: Client-side date filter and sorting
  const diagnosticosProcesados = useMemo(() => {
    let result = [...diagnosticos];

    // 1. Date range filter
    if (filtroFecha !== 'todos') {
      const hoy = new Date();
      const hoyStr = hoy.toISOString().slice(0, 10);

      if (filtroFecha === 'hoy') {
        result = result.filter((d) => d.fecha_hora.startsWith(hoyStr));
      } else if (filtroFecha === '7dias') {
        const limite7 = new Date();
        limite7.setDate(hoy.getDate() - 7);
        result = result.filter((d) => new Date(d.fecha_hora) >= limite7);
      } else if (filtroFecha === 'esteMes') {
        const mesActual = hoy.getMonth();
        const anioActual = hoy.getFullYear();
        result = result.filter((d) => {
          const f = new Date(d.fecha_hora);
          return f.getMonth() === mesActual && f.getFullYear() === anioActual;
        });
      }
    }

    // 2. Sorting
    result.sort((a, b) => {
      if (orden === 'pendientes_primero') {
        const esPendienteA = a.estado === 'generado' || a.estado === 'en_revision' ? 0 : 1;
        const esPendienteB = b.estado === 'generado' || b.estado === 'en_revision' ? 0 : 1;
        if (esPendienteA !== esPendienteB) {
          return esPendienteA - esPendienteB;
        }
        return new Date(b.fecha_hora).getTime() - new Date(a.fecha_hora).getTime();
      }

      if (orden === 'fecha_desc') {
        return new Date(b.fecha_hora).getTime() - new Date(a.fecha_hora).getTime();
      }

      if (orden === 'fecha_asc') {
        return new Date(a.fecha_hora).getTime() - new Date(b.fecha_hora).getTime();
      }

      if (orden === 'confianza_desc') {
        return b.confianza - a.confianza;
      }

      if (orden === 'confianza_asc') {
        return a.confianza - b.confianza;
      }

      return 0;
    });

    return result;
  }, [diagnosticos, filtroFecha, orden]);

  // Pagination calculation
  const totalPaginas = Math.ceil(diagnosticosProcesados.length / elementosPorPagina) || 1;
  const diagnosticosPaginados = useMemo(() => {
    const inicio = (paginaActual - 1) * elementosPorPagina;
    return diagnosticosProcesados.slice(inicio, inicio + elementosPorPagina);
  }, [diagnosticosProcesados, paginaActual, elementosPorPagina]);

  const handleCambiarPagina = (nuevaPagina: number) => {
    if (nuevaPagina >= 1 && nuevaPagina <= totalPaginas) {
      setPaginaActual(nuevaPagina);
    }
  };

  const handleGuardarConfirmacion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!diagnosticoSeleccionadoModal) return;

    // Requirement: Mandate observation when discarded
    if (nuevoEstado === 'descartado' && !notasMecanico.trim()) {
      setErrorGuardado('Es obligatorio ingresar una observación o motivo detallado al descartar un diagnóstico.');
      return;
    }

    setGuardando(true);
    setErrorGuardado('');
    try {
      await onActualizarEstado(diagnosticoSeleccionadoModal.id, nuevoEstado, notasMecanico.trim() || undefined);
      onCerrarModalDetalle();
    } catch (err: unknown) {
      setErrorGuardado(err instanceof Error ? err.message : 'No se pudo guardar la confirmación.');
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
            Historial y Confirmación de Diagnósticos
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Filtra, revisa las 3 secciones generadas por ML+RAG y confirma los diagnósticos mecánicos.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>
            Total: {diagnosticosProcesados.length} registros
          </span>
        </div>
      </div>

      {/* Filter and Sort Panel */}
      <Card style={{ padding: '16px' }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '12px',
          }}
        >
          <Input
            placeholder="Buscar placa, síntoma o falla..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            icon={<Search size={18} />}
          />

          <Select
            value={filtroEstado}
            onChange={(e) => setFiltroEstado(e.target.value)}
            options={[
              { value: 'todos', label: 'Todos los estados' },
              { value: 'generado', label: 'Estado: Generado' },
              { value: 'en_revision', label: 'Estado: En Revisión' },
              { value: 'confirmado', label: 'Estado: Confirmado' },
              { value: 'descartado', label: 'Estado: Descartado' },
            ]}
          />

          <Select
            value={filtroFecha}
            onChange={(e) => setFiltroFecha(e.target.value as FiltroFecha)}
            options={[
              { value: 'todos', label: 'Periodo: Todo el historial' },
              { value: 'hoy', label: 'Periodo: Hoy' },
              { value: '7dias', label: 'Periodo: Últimos 7 días' },
              { value: 'esteMes', label: 'Periodo: Este mes' },
            ]}
          />

          <Select
            value={orden}
            onChange={(e) => setOrden(e.target.value as TipoOrden)}
            options={[
              { value: 'pendientes_primero', label: 'Orden: Pendientes primero' },
              { value: 'fecha_desc', label: 'Orden: Más recientes primero' },
              { value: 'fecha_asc', label: 'Orden: Más antiguos primero' },
              { value: 'confianza_desc', label: 'Orden: Mayor confianza' },
              { value: 'confianza_asc', label: 'Orden: Menor confianza' },
            ]}
          />

          <Select
            value={filtroModo}
            onChange={(e) => setFiltroModo(e.target.value)}
            options={[
              { value: 'todos', label: 'Todos los modos' },
              { value: 'completo_ml_rag_llm', label: 'Modo: ML + RAG + LLM' },
              { value: 'diagnostico_degradado_ml_rag', label: 'Modo: Degradado (ML+RAG)' },
              { value: 'saludo', label: 'Modo: Saludo / Regla' },
            ]}
          />

          <Select
            value={filtroMecanico}
            onChange={(e) => setFiltroMecanico(e.target.value)}
            options={[
              { value: 'todos', label: 'Todos los mecánicos' },
              ...mecanicos.map((m) => ({ value: m.id, label: m.nombres })),
            ]}
          />
        </div>
      </Card>

      {/* Diagnostics Table */}
      <Card style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr
                style={{
                  backgroundColor: 'var(--bg-subtle)',
                  borderBottom: '1px solid var(--border-color)',
                  fontSize: '12px',
                  fontWeight: 600,
                  color: 'var(--text-secondary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                <th style={{ padding: '12px 16px' }}>Placa / Vehículo</th>
                <th style={{ padding: '12px 16px' }}>Síntoma del Cliente</th>
                <th style={{ padding: '12px 16px' }}>Falla Predicha (ML)</th>
                <th style={{ padding: '12px 16px' }}>Confianza</th>
                <th style={{ padding: '12px 16px' }}>Modo</th>
                <th style={{ padding: '12px 16px' }}>Estado</th>
                <th style={{ padding: '12px 16px', textAlign: 'right' }}>Detalle</th>
              </tr>
            </thead>
            <tbody>
              {cargando ? (
                <tr>
                  <td colSpan={7} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                      <RefreshCw size={24} className="animate-spin" style={{ color: 'var(--primary)' }} />
                      <span style={{ fontSize: '14px' }}>Cargando diagnósticos del taller...</span>
                    </div>
                  </td>
                </tr>
              ) : diagnosticosPaginados.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                      <AlertCircle size={36} style={{ color: 'var(--text-muted)', opacity: 0.6 }} />
                      <p style={{ margin: 0, fontSize: '15px', fontWeight: 600, color: 'var(--text-main)' }}>
                        No se encontraron diagnósticos
                      </p>
                      <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)' }}>
                        Intenta ajustar o limpiar los filtros de búsqueda, estado o periodo.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                diagnosticosPaginados.map((d) => (
                  <tr
                    key={d.id}
                    className="table-row-hover"
                    style={{
                      borderBottom: '1px solid var(--border-color)',
                      fontSize: '14px',
                      backgroundColor: '#ffffff',
                    }}
                  >
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontWeight: 700, color: 'var(--primary)' }}>
                          {d.placa_vehiculo}
                        </span>
                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                          {d.marca_modelo}
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: '14px 16px', maxWidth: '240px', color: 'var(--text-main)' }}>
                      <p style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', margin: 0 }}>
                        "{d.sintoma_original}"
                      </p>
                    </td>
                    <td style={{ padding: '14px 16px', fontWeight: 600, color: 'var(--text-main)' }}>
                      {d.falla_predicha}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{ fontWeight: 700, color: d.confianza >= 85 ? 'var(--status-success-text)' : 'var(--status-warning-text)' }}>
                        {d.confianza}%
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <Badge type={d.modo_diagnostico} size="sm" />
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <Badge type={d.estado} />
                    </td>
                    <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setNuevoEstado(d.estado === 'generado' ? 'confirmado' : d.estado);
                          setNotasMecanico(d.notas_mecanico || '');
                          setErrorGuardado('');
                          onAbrirModalDetalle(d);
                        }}
                      >
                        Ver / Confirmar
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        {!cargando && diagnosticosProcesados.length > 0 && (
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '12px 16px',
              borderTop: '1px solid var(--border-color)',
              backgroundColor: 'var(--bg-main)',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: 'var(--text-secondary)' }}>
              <span>Mostrar</span>
              <select
                value={elementosPorPagina}
                onChange={(e) => {
                  setElementosPorPagina(Number(e.target.value));
                  setPaginaActual(1);
                }}
                style={{
                  padding: '4px 8px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-color)',
                  fontSize: '12px',
                  backgroundColor: '#ffffff',
                }}
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
              <span>por página</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                Página {paginaActual} de {totalPaginas}
              </span>
              <button
                type="button"
                onClick={() => handleCambiarPagina(paginaActual - 1)}
                disabled={paginaActual <= 1}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '32px',
                  height: '32px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-color)',
                  backgroundColor: '#ffffff',
                  color: paginaActual <= 1 ? 'var(--text-muted)' : 'var(--text-main)',
                  cursor: paginaActual <= 1 ? 'not-allowed' : 'pointer',
                }}
              >
                <ChevronLeft size={16} />
              </button>
              <button
                type="button"
                onClick={() => handleCambiarPagina(paginaActual + 1)}
                disabled={paginaActual >= totalPaginas}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '32px',
                  height: '32px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-color)',
                  backgroundColor: '#ffffff',
                  color: paginaActual >= totalPaginas ? 'var(--text-muted)' : 'var(--text-main)',
                  cursor: paginaActual >= totalPaginas ? 'not-allowed' : 'pointer',
                }}
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </Card>

      {/* Modal Detail & Mechanic Confirmation */}
      {diagnosticoSeleccionadoModal && (
        <Modal
          isOpen={!!diagnosticoSeleccionadoModal}
          onClose={onCerrarModalDetalle}
          title={`Diagnóstico Técnico — Placa ${diagnosticoSeleccionadoModal.placa_vehiculo}`}
          maxWidth="940px"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Meta header */}
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                backgroundColor: 'var(--primary-light)',
                borderRadius: '8px',
                border: '1px solid var(--primary-border)',
                gap: '10px',
              }}
            >
              <div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Mecánico Atendiendo:</span>
                <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>
                  {diagnosticoSeleccionadoModal.mecanico_nombre}
                </p>
              </div>
              <div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Fecha y Hora:</span>
                <p style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-main)', margin: 0 }}>
                  {diagnosticoSeleccionadoModal.fecha_hora}
                </p>
              </div>
              <div>
                <Badge type={diagnosticoSeleccionadoModal.estado} />
              </div>
            </div>

            {/* Sintoma original */}
            <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '12px 16px', borderRadius: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Síntoma procesado desde WhatsApp:
              </span>
              <p style={{ fontSize: '14px', fontStyle: 'italic', color: 'var(--text-main)', marginTop: '4px', margin: '4px 0 0 0' }}>
                "{diagnosticoSeleccionadoModal.sintoma_original}"
              </p>
            </div>

            {/* Trazabilidad visual por etapas */}
            <div style={{ border: '1px solid var(--border-color)', borderRadius: '10px', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', marginBottom: '12px', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Cpu size={18} color="var(--primary)" />
                  <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                    Trazabilidad del procesamiento
                  </h4>
                </div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Total registrado: <strong>{diagnosticoSeleccionadoModal.duracion_ms} ms</strong>
                  {diagnosticoSeleccionadoModal.desde_cache ? ' · Respuesta desde caché' : ''}
                </span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(165px, 1fr))', gap: '10px' }}>
                {diagnosticoSeleccionadoModal.etapas_procesamiento.map((etapa, index) => {
                  const completada = etapa.estado === 'completado';
                  const enCola = etapa.estado === 'en_cola';
                  const color = completada ? '#059669' : enCola ? '#d97706' : '#64748b';
                  const fondo = completada ? '#ecfdf5' : enCola ? '#fffbeb' : '#f8fafc';
                  return (
                    <div key={`${etapa.clave}-${index}`} style={{ padding: '12px', borderRadius: '8px', backgroundColor: fondo, border: `1px solid ${color}25` }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '5px' }}>
                        <span style={{ width: '20px', height: '20px', borderRadius: '50%', backgroundColor: color, color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700 }}>
                          {index + 1}
                        </span>
                        <strong style={{ fontSize: '12px', color: 'var(--text-main)' }}>{etapa.nombre}</strong>
                      </div>
                      <div style={{ fontSize: '11px', color, fontWeight: 700, textTransform: 'uppercase' }}>{etapa.estado.replace('_', ' ')}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '3px' }}>{etapa.duracion_ms} ms</div>
                      {etapa.detalle && <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '5px', lineHeight: 1.35 }}>{etapa.detalle}</div>}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Section 1: comparación real de probabilidades ML */}
            <div style={{ border: '1px solid var(--border-color)', borderRadius: '10px', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <Cpu size={18} color="var(--primary)" />
                <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>
                  1. Comparación del clasificador ML
                </h4>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '0 0 14px 0' }}>
                Las barras muestran las tres clases con mayor probabilidad para este diagnóstico específico.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {diagnosticoSeleccionadoModal.predicciones_ml.map((prediccion) => {
                  const color = prediccion.orden === 1 ? '#2563eb' : prediccion.orden === 2 ? '#7c3aed' : '#64748b';
                  return (
                    <div key={`${prediccion.orden}-${prediccion.falla}`}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', marginBottom: '5px', fontSize: '12px' }}>
                        <span style={{ color: 'var(--text-main)', fontWeight: prediccion.orden === 1 ? 700 : 500 }}>
                          {prediccion.orden}. {prediccion.falla}
                        </span>
                        <strong style={{ color, whiteSpace: 'nowrap' }}>{prediccion.probabilidad}%</strong>
                      </div>
                      <div style={{ width: '100%', height: '10px', borderRadius: '999px', backgroundColor: '#e2e8f0', overflow: 'hidden' }}>
                        <div style={{ width: `${Math.max(1, Math.min(100, prediccion.probabilidad))}%`, height: '100%', borderRadius: '999px', backgroundColor: color, transition: 'width 0.3s ease' }} />
                      </div>
                    </div>
                  );
                })}
              </div>
              <div style={{ display: 'flex', gap: '16px', marginTop: '14px', paddingTop: '12px', borderTop: '1px solid var(--border-color)', fontSize: '12px', color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
                <span>Hipótesis elegida: <strong>{diagnosticoSeleccionadoModal.falla_predicha}</strong></span>
                <span>Modelo: <strong>{diagnosticoSeleccionadoModal.version_modelo_ml || 'Versión no registrada'}</strong></span>
              </div>
            </div>

            {/* Section 2: Procedimiento RAG */}
            <div style={{ border: '1px solid var(--border-color)', borderRadius: '10px', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <FileText size={18} color="var(--primary)" />
                  <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>
                    2. Evidencia recuperada por RAG
                  </h4>
                </div>
                {diagnosticoSeleccionadoModal.similitud_rag !== undefined && (
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    Similitud RAG: <strong>{diagnosticoSeleccionadoModal.similitud_rag}%</strong>
                  </span>
                )}
              </div>
              {diagnosticoSeleccionadoModal.fuente_manual && (
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px', fontStyle: 'italic' }}>
                  Referencia: {diagnosticoSeleccionadoModal.fuente_manual}
                </div>
              )}
              <pre
                style={{
                  fontSize: '13px',
                  fontFamily: 'inherit',
                  whiteSpace: 'pre-wrap',
                  backgroundColor: 'var(--bg-subtle)',
                  padding: '12px',
                  borderRadius: '6px',
                  color: 'var(--text-main)',
                  lineHeight: 1.5,
                  margin: 0,
                }}
              >
                {diagnosticoSeleccionadoModal.procedimiento_rag}
              </pre>
            </div>

            {/* Section 3: Tiempo & Gravedad */}
            <div style={{ border: '1px solid var(--border-color)', borderRadius: '10px', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <Clock size={18} color="var(--primary)" />
                <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>
                  ⏱️ 3. Tiempo Estimado y Gravedad
                </h4>
              </div>
              <pre
                style={{
                  fontSize: '13px',
                  fontFamily: 'inherit',
                  whiteSpace: 'pre-wrap',
                  color: 'var(--text-secondary)',
                  margin: 0,
                }}
              >
                {diagnosticoSeleccionadoModal.tiempo_gravedad}
              </pre>
            </div>

            {/* Sintesis LLM */}
            {diagnosticoSeleccionadoModal.sintesis_llm && (
              <div style={{ border: '1px solid var(--border-color)', borderRadius: '10px', padding: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <FileText size={18} color="var(--primary)" />
                  <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>
                    3. Síntesis técnica de Gemini
                  </h4>
                </div>
                <pre style={{ fontSize: '13px', fontFamily: 'inherit', whiteSpace: 'pre-wrap', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                  {diagnosticoSeleccionadoModal.sintesis_llm}
                </pre>
                <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginTop: '12px', paddingTop: '10px', borderTop: '1px solid var(--border-color)', fontSize: '11px', color: 'var(--text-muted)' }}>
                  <span>Modelo: <strong>{diagnosticoSeleccionadoModal.llm_modelo || 'No registrado'}</strong></span>
                  <span>Tokens entrada: <strong>{diagnosticoSeleccionadoModal.tokens_entrada}</strong></span>
                  <span>Tokens salida: <strong>{diagnosticoSeleccionadoModal.tokens_salida}</strong></span>
                </div>
              </div>
            )}

            {/* Formulario de validación administrativa */}
            <form
              onSubmit={handleGuardarConfirmacion}
              style={{
                backgroundColor: '#fff7ed',
                border: '1px solid #ffedd5',
                borderRadius: '10px',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px',
              }}
            >
              {errorGuardado && (
                <div style={{ padding: '10px 14px', borderRadius: '6px', backgroundColor: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', fontSize: '13px' }}>
                  {errorGuardado}
                </div>
              )}
              <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--primary)', margin: 0 }}>
                Validación administrativa del diagnóstico
              </h4>

              <Select
                label="Estado de validación"
                value={nuevoEstado}
                onChange={(e) => setNuevoEstado(e.target.value as EstadoDiagnostico)}
                options={[
                  { value: 'confirmado', label: '✅ Confirmado (Falla verificada físicamente)' },
                  { value: 'en_revision', label: '⏳ En Revisión (Desmontando componentes)' },
                  { value: 'descartado', label: '❌ Descartado (Falla fue diferente a la predicha)' },
                ]}
              />

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                  Observación técnica del administrador {nuevoEstado === 'descartado' && <span style={{ color: '#ef4444' }}>* (Obligatoria al descartar)</span>}
                </label>
                <Input
                  placeholder={nuevoEstado === 'descartado' ? 'Indique el motivo técnico por el cual se descarta...' : 'Ej. Se verificó con escáner OBD-II y pastillas cambiadas.'}
                  value={notasMecanico}
                  onChange={(e) => setNotasMecanico(e.target.value)}
                  required={nuevoEstado === 'descartado'}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <Button type="button" variant="secondary" onClick={onCerrarModalDetalle}>
                  Cancelar
                </Button>
                <Button type="submit" variant="primary" disabled={guardando}>
                  {guardando ? 'Guardando...' : 'Guardar Confirmación'}
                </Button>
              </div>
            </form>
          </div>
        </Modal>
      )}
    </div>
  );
};
