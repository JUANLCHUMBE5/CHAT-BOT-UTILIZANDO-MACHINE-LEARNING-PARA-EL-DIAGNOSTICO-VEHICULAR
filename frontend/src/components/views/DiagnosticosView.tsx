import React, { useState, useMemo } from 'react';
import {
  Search,
  Clock,
  Cpu,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  RefreshCw,
  Users,
  UserCheck,
  MessageSquare,
  Sparkles,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Calendar,
  ShieldCheck,
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

export const DiagnosticosView: React.FC<DiagnosticosViewProps> = ({
  diagnosticos,
  cargando = false,
  mecanicos,
  currentUser,
  onActualizarEstado,
  onFiltrar,
  diagnosticoSeleccionadoModal,
  onCerrarModalDetalle,
  onAbrirModalDetalle,
}) => {
  // Filter States
  const [busqueda, setBusqueda] = useState('');
  const [filtroEstado, setFiltroEstado] = useState('todos');
  const [filtroMecanico, setFiltroMecanico] = useState('todos');
  const [filtroFecha, setFiltroFecha] = useState<FiltroFecha>('todos');
  const orden = 'pendientes_primero';

  // Pagination States
  const [paginaActual, setPaginaActual] = useState(1);
  const [elementosPorPagina, setElementosPorPagina] = useState(10);

  // Resolution of Current User Mechanic ID for quick scoping
  const miMecanico = useMemo(() => {
    if (!currentUser) return null;
    if (currentUser.id) {
      const porId = mecanicos.find((m) => m.id === currentUser.id);
      if (porId) return porId;
    }
    if (currentUser.username) {
      const porUser = mecanicos.find(
        (m) => m.username && m.username.toLowerCase() === currentUser.username.toLowerCase()
      );
      if (porUser) return porUser;
    }
    if (currentUser.nombre) {
      const porNom = mecanicos.find(
        (m) => m.nombres && m.nombres.toLowerCase().trim() === currentUser.nombre.toLowerCase().trim()
      );
      if (porNom) return porNom;
    }
    return null;
  }, [currentUser, mecanicos]);

  const miMecanicoId = miMecanico?.id || currentUser?.id || null;

  // Calculate count of current user queries in the loaded dataset
  const conteoMisConsultas = useMemo(() => {
    if (!miMecanicoId && !currentUser?.nombre) return 0;
    return diagnosticos.filter((d) => {
      if (miMecanicoId && d.mecanico_id === miMecanicoId) return true;
      if (
        currentUser?.nombre &&
        d.mecanico_nombre &&
        d.mecanico_nombre.toLowerCase().trim() === currentUser.nombre.toLowerCase().trim()
      ) {
        return true;
      }
      return false;
    }).length;
  }, [diagnosticos, miMecanicoId, currentUser]);

  const esModoMisConsultas =
    filtroMecanico !== 'todos' &&
    (filtroMecanico === miMecanicoId || (miMecanico && filtroMecanico === miMecanico.id));

  // Trigger backend filtering with 300ms debounce on search
  React.useEffect(() => {
    const timer = setTimeout(() => {
      if (onFiltrar) {
        onFiltrar({
          busqueda: busqueda.trim() || undefined,
          estado: filtroEstado !== 'todos' ? filtroEstado : undefined,
          mecanico_id: filtroMecanico !== 'todos' ? filtroMecanico : undefined,
        });
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [busqueda, filtroEstado, filtroMecanico, onFiltrar]);

  // Reset pagination when filters change
  React.useEffect(() => {
    setPaginaActual(1);
  }, [busqueda, filtroEstado, filtroMecanico, filtroFecha]);

  // Confirmation Form State inside Detail Modal
  const [nuevoEstado, setNuevoEstado] = useState<EstadoDiagnostico>('confirmado');
  const [notasMecanico, setNotasMecanico] = useState('');
  const [guardando, setGuardando] = useState(false);
  const [errorGuardado, setErrorGuardado] = useState('');

  // Process list: Client-side date filter and sorting
  const diagnosticosProcesados = useMemo(() => {
    let result = [...diagnosticos];

    // 1. Date range filter with ISO parsing safety
    if (filtroFecha !== 'todos') {
      const hoy = new Date();
      const hoyStr = hoy.toISOString().slice(0, 10);

      if (filtroFecha === 'hoy') {
        result = result.filter((d) => d.fecha_hora.startsWith(hoyStr));
      } else if (filtroFecha === '7dias') {
        const limite7 = new Date();
        limite7.setDate(hoy.getDate() - 7);
        result = result.filter((d) => {
          const f = new Date(d.fecha_hora.replace(' ', 'T'));
          return !isNaN(f.getTime()) && f >= limite7;
        });
      } else if (filtroFecha === 'esteMes') {
        const mesActual = hoy.getMonth();
        const anioActual = hoy.getFullYear();
        result = result.filter((d) => {
          const f = new Date(d.fecha_hora.replace(' ', 'T'));
          return !isNaN(f.getTime()) && f.getMonth() === mesActual && f.getFullYear() === anioActual;
        });
      }
    }

    // 2. Sorting
    result.sort((a, b) => {
      const fechaA = new Date(a.fecha_hora.replace(' ', 'T')).getTime() || 0;
      const fechaB = new Date(b.fecha_hora.replace(' ', 'T')).getTime() || 0;

      if (orden === 'pendientes_primero') {
        const esPendienteA = a.estado === 'generado' || a.estado === 'en_revision' ? 0 : 1;
        const esPendienteB = b.estado === 'generado' || b.estado === 'en_revision' ? 0 : 1;
        if (esPendienteA !== esPendienteB) {
          return esPendienteA - esPendienteB;
        }
        return fechaB - fechaA;
      }

      if (orden === 'fecha_desc') {
        return fechaB - fechaA;
      }

      if (orden === 'fecha_asc') {
        return fechaA - fechaB;
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

  // Helper to check if a diagnostic belongs to current user
  const esMiDiagnostico = (d: Diagnostico) => {
    if (miMecanicoId && d.mecanico_id === miMecanicoId) return true;
    if (
      currentUser?.nombre &&
      d.mecanico_nombre &&
      d.mecanico_nombre.toLowerCase().trim() === currentUser.nombre.toLowerCase().trim()
    ) {
      return true;
    }
    return false;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header with Scope Switcher in 1 clean line */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-main)', margin: 0, letterSpacing: '-0.02em' }}>
            Historial de Diagnósticos
          </h2>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Mostrando <strong>{diagnosticosProcesados.length}</strong> de {diagnosticos.length} consultas registradas
          </span>
        </div>

        {/* Scope Switcher: Todo el Taller vs Mis Consultas */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            type="button"
            onClick={() => setFiltroMecanico('todos')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '8px',
              fontSize: '12px',
              fontWeight: 600,
              border: filtroMecanico === 'todos' ? '1px solid var(--primary)' : '1px solid var(--border-color)',
              backgroundColor: filtroMecanico === 'todos' ? 'var(--primary)' : '#ffffff',
              color: filtroMecanico === 'todos' ? '#ffffff' : 'var(--text-secondary)',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            <Users size={14} />
            <span>Todo el Taller</span>
            <span
              style={{
                padding: '1px 6px',
                borderRadius: '10px',
                fontSize: '10px',
                fontWeight: 700,
                backgroundColor: filtroMecanico === 'todos' ? 'rgba(255,255,255,0.25)' : '#f1f5f9',
                color: filtroMecanico === 'todos' ? '#ffffff' : 'var(--text-muted)',
              }}
            >
              {diagnosticos.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => {
              if (miMecanicoId) {
                setFiltroMecanico(miMecanicoId);
              }
            }}
            disabled={!miMecanicoId && !currentUser}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '8px',
              fontSize: '12px',
              fontWeight: 600,
              border: esModoMisConsultas ? '1px solid #4f46e5' : '1px solid var(--border-color)',
              backgroundColor: esModoMisConsultas ? '#4f46e5' : '#ffffff',
              color: esModoMisConsultas ? '#ffffff' : 'var(--text-secondary)',
              cursor: !miMecanicoId && !currentUser ? 'not-allowed' : 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            <UserCheck size={14} />
            <span>Mis Consultas</span>
            <span
              style={{
                padding: '1px 6px',
                borderRadius: '10px',
                fontSize: '10px',
                fontWeight: 700,
                backgroundColor: esModoMisConsultas ? 'rgba(255,255,255,0.25)' : '#f1f5f9',
                color: esModoMisConsultas ? '#ffffff' : 'var(--text-muted)',
              }}
            >
              {conteoMisConsultas}
            </span>
          </button>
        </div>
      </div>

      {/* Single-Row Clean Filter Bar */}
      <Card style={{ padding: '12px 14px' }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr minmax(160px, 200px) minmax(160px, 180px)',
            gap: '10px',
            alignItems: 'center',
          }}
        >
          <Input
            placeholder="Buscar por síntoma, diagnóstico o solicitante..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            icon={<Search size={16} />}
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
              { value: 'todos', label: 'Periodo: Todo' },
              { value: 'hoy', label: 'Periodo: Hoy' },
              { value: '7dias', label: 'Últimos 7 días' },
              { value: 'esteMes', label: 'Este mes' },
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
                  fontSize: '11px',
                  fontWeight: 700,
                  color: 'var(--text-secondary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                <th style={{ padding: '12px 16px' }}>Solicitante</th>
                <th style={{ padding: '12px 16px' }}>Vehículo</th>
                <th style={{ padding: '12px 16px' }}>Síntoma Reportado</th>
                <th style={{ padding: '12px 16px' }}>Diagnóstico IA</th>
                <th style={{ padding: '12px 16px' }}>Estado</th>
                <th style={{ padding: '12px 16px', textAlign: 'right' }}>Acción</th>
              </tr>
            </thead>
            <tbody>
              {cargando ? (
                <tr>
                  <td colSpan={6} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                      <RefreshCw size={22} className="animate-spin" style={{ color: 'var(--primary)' }} />
                      <span style={{ fontSize: '13px' }}>Cargando diagnósticos...</span>
                    </div>
                  </td>
                </tr>
              ) : diagnosticosPaginados.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                      <AlertCircle size={32} style={{ color: 'var(--text-muted)', opacity: 0.6 }} />
                      <p style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: 'var(--text-main)' }}>
                        No se encontraron registros
                      </p>
                      <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-secondary)' }}>
                        Prueba con otros términos de búsqueda o selecciona "Todo el Taller".
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                diagnosticosPaginados.map((d) => {
                  const esMio = esMiDiagnostico(d);
                  const tienePlaca =
                    d.placa_vehiculo &&
                    d.placa_vehiculo.trim() !== '' &&
                    !d.placa_vehiculo.toLowerCase().includes('sin placa');

                  return (
                    <tr
                      key={d.id}
                      className="table-row-hover"
                      style={{
                        borderBottom: '1px solid var(--border-color)',
                        fontSize: '13px',
                        backgroundColor: esMio ? 'rgba(238, 242, 255, 0.2)' : '#ffffff',
                      }}
                    >
                      {/* Solicitante */}
                      <td style={{ padding: '12px 16px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div
                            style={{
                              width: '30px',
                              height: '30px',
                              borderRadius: '8px',
                              backgroundColor: esMio ? '#eef2ff' : '#f1f5f9',
                              color: esMio ? '#4f46e5' : '#475569',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              flexShrink: 0,
                              border: `1px solid ${esMio ? '#c7d2fe' : '#e2e8f0'}`,
                            }}
                          >
                            {esMio ? <UserCheck size={15} /> : <MessageSquare size={14} />}
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '13px' }}>
                                {d.mecanico_nombre || d.cliente_nombre || 'Usuario'}
                              </span>
                              {esMio && (
                                <span
                                  style={{
                                    fontSize: '9px',
                                    fontWeight: 700,
                                    backgroundColor: '#eef2ff',
                                    color: '#4338ca',
                                    padding: '1px 5px',
                                    borderRadius: '8px',
                                    border: '1px solid #c7d2fe',
                                  }}
                                >
                                  Tú
                                </span>
                              )}
                            </div>
                            {d.cliente_telefono && (
                              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                                {d.cliente_telefono}
                              </span>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Vehículo */}
                      <td style={{ padding: '12px 16px' }}>
                        {tienePlaca ? (
                          <div style={{ display: 'flex', flexDirection: 'column' }}>
                            <span style={{ fontWeight: 700, color: 'var(--primary)', fontSize: '13px' }}>
                              {d.placa_vehiculo}
                            </span>
                            {d.marca_modelo && !d.marca_modelo.toLowerCase().includes('no registrado') && (
                              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                                {d.marca_modelo}
                              </span>
                            )}
                          </div>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>—</span>
                        )}
                      </td>

                      {/* Síntoma */}
                      <td style={{ padding: '12px 16px', maxWidth: '240px', color: 'var(--text-main)' }}>
                        <p style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', margin: 0, fontSize: '13px' }} title={d.sintoma_original}>
                          "{d.sintoma_original}"
                        </p>
                      </td>

                      {/* Diagnóstico ML */}
                      <td style={{ padding: '12px 16px' }}>
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '13px' }}>
                            {d.falla_predicha}
                          </span>
                          <span style={{ fontSize: '11px', fontWeight: 600, color: d.confianza >= 80 ? 'var(--status-success-text)' : 'var(--text-muted)' }}>
                            {d.confianza}% confianza
                          </span>
                        </div>
                      </td>

                      {/* Estado */}
                      <td style={{ padding: '12px 16px' }}>
                        <Badge type={d.estado} />
                      </td>

                      {/* Acción Ver Detalle */}
                      <td style={{ padding: '12px 16px', textAlign: 'right' }}>
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
                          Ver Detalle
                        </Button>
                      </td>
                    </tr>
                  );
                })
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

      {/* ========================================================================= */}
      {/* MODAL DETALLE & CONFIRMACIÓN TÉCNICA REDISEÑADO                           */}
      {/* ========================================================================= */}
      {diagnosticoSeleccionadoModal && (
        <Modal
          isOpen={!!diagnosticoSeleccionadoModal}
          onClose={onCerrarModalDetalle}
          title={`Detalle de Diagnóstico — ${diagnosticoSeleccionadoModal.placa_vehiculo}`}
          maxWidth="920px"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', padding: '4px 0' }}>

            {/* 1. Header Meta Card: Resumen de Auditoría y Atribución */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                padding: '16px 20px',
                backgroundColor: 'var(--bg-subtle)',
                borderRadius: '12px',
                border: '1px solid var(--border-color)',
                gap: '16px',
                alignItems: 'center',
              }}
            >
              {/* Usuario / Solicitante */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                  <UserCheck size={13} style={{ color: '#2563eb' }} />
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.04em' }}>
                    Usuario / Solicitante
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <p style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                    {diagnosticoSeleccionadoModal.mecanico_nombre || diagnosticoSeleccionadoModal.cliente_nombre || 'Usuario'}
                  </p>
                  {esMiDiagnostico(diagnosticoSeleccionadoModal) && (
                    <span style={{ fontSize: '10px', fontWeight: 700, backgroundColor: '#eef2ff', color: '#4338ca', padding: '2px 7px', borderRadius: '10px', border: '1px solid #c7d2fe' }}>
                      Tú
                    </span>
                  )}
                </div>
                {diagnosticoSeleccionadoModal.cliente_telefono && (
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px', display: 'block' }}>
                    {diagnosticoSeleccionadoModal.cliente_telefono}
                  </span>
                )}
              </div>

              {/* Vehículo Asociado */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.04em' }}>
                    Vehículo / Registro
                  </span>
                </div>
                <p style={{ fontSize: '14px', fontWeight: 700, color: 'var(--primary)', margin: 0 }}>
                  {diagnosticoSeleccionadoModal.placa_vehiculo}
                </p>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px', display: 'block' }}>
                  {diagnosticoSeleccionadoModal.marca_modelo}
                </span>
              </div>

              {/* Fecha y Estado */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Calendar size={13} style={{ color: 'var(--text-muted)' }} />
                  <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    {diagnosticoSeleccionadoModal.fecha_hora}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Badge type={diagnosticoSeleccionadoModal.estado} />
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>
                    {diagnosticoSeleccionadoModal.placa_vehiculo}
                  </span>
                </div>
              </div>
            </div>

            {/* 2. WhatsApp Message Speech Bubble */}
            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                backgroundColor: '#f0fdf4',
                border: '1px solid #bbf7d0',
                borderRadius: '12px',
                padding: '14px 18px',
              }}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  backgroundColor: '#22c55e',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  marginTop: '2px',
                }}
              >
                <MessageSquare size={16} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: '#166534', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Mensaje Recibido por WhatsApp
                  </span>
                  <span style={{ fontSize: '11px', color: '#15803d' }}>
                    Canal WhatsApp
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: '14px', fontWeight: 500, color: '#14532d', fontStyle: 'italic', lineHeight: 1.45 }}>
                  "{diagnosticoSeleccionadoModal.sintoma_original}"
                </p>
              </div>
            </div>

            {/* 3. Pipeline Stepper: Trazabilidad de 4 Etapas */}
            <div style={{ border: '1px solid var(--border-color)', borderRadius: '12px', padding: '18px', backgroundColor: '#ffffff' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Cpu size={18} style={{ color: 'var(--primary)' }} />
                  <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                    Trazabilidad del Pipeline de Procesamiento
                  </h4>
                </div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', backgroundColor: 'var(--bg-subtle)', padding: '4px 10px', borderRadius: '20px', border: '1px solid var(--border-color)' }}>
                  ⏱️ Latencia Total: <strong>{diagnosticoSeleccionadoModal.duracion_ms} ms</strong>
                  {diagnosticoSeleccionadoModal.desde_cache ? ' · ⚡ Desde Caché' : ''}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
                {diagnosticoSeleccionadoModal.etapas_procesamiento.map((etapa, index) => {
                  const completada = etapa.estado === 'completado';
                  const enCola = etapa.estado === 'en_cola';
                  const degradado = etapa.estado === 'degradado';
                  const badgeColor = completada ? '#059669' : enCola ? '#d97706' : degradado ? '#e11d48' : '#64748b';
                  const badgeBg = completada ? '#ecfdf5' : enCola ? '#fffbeb' : degradado ? '#fff1f2' : '#f8fafc';

                  return (
                    <div
                      key={`${etapa.clave}-${index}`}
                      style={{
                        padding: '12px 14px',
                        borderRadius: '10px',
                        backgroundColor: badgeBg,
                        border: `1px solid ${badgeColor}30`,
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                          <span
                            style={{
                              width: '22px',
                              height: '22px',
                              borderRadius: '50%',
                              backgroundColor: badgeColor,
                              color: '#ffffff',
                              display: 'inline-flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '11px',
                              fontWeight: 700,
                            }}
                          >
                            {index + 1}
                          </span>
                          <span style={{ fontSize: '10px', fontWeight: 700, color: badgeColor, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                            {etapa.estado.replace('_', ' ')}
                          </span>
                        </div>
                        <strong style={{ fontSize: '12px', color: 'var(--text-main)', display: 'block', lineHeight: 1.3 }}>
                          {etapa.nombre}
                        </strong>
                      </div>

                      <div style={{ marginTop: '8px', paddingTop: '6px', borderTop: `1px dashed ${badgeColor}25` }}>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          {etapa.duracion_ms} ms
                        </span>
                        {etapa.detalle && (
                          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px', lineHeight: 1.3 }}>
                            {etapa.detalle}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 4. Section 1: Comparación del Clasificador ML */}
            <div style={{ border: '1px solid var(--border-color)', borderRadius: '12px', padding: '18px', backgroundColor: '#ffffff' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ width: '28px', height: '28px', borderRadius: '6px', backgroundColor: '#eff6ff', color: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Cpu size={16} />
                  </div>
                  <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                    1. Comparación del Clasificador ML (SVM / TF-IDF)
                  </h4>
                </div>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Modelo: <strong>{diagnosticoSeleccionadoModal.version_modelo_ml || '2.2.0-external-audited'}</strong>
                </span>
              </div>

              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '0 0 14px 0' }}>
                Distribución de probabilidades por clase calculadas para este síntoma:
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {diagnosticoSeleccionadoModal.predicciones_ml.map((prediccion) => {
                  const esPrincipal = prediccion.orden === 1;
                  const barColor = esPrincipal ? 'linear-gradient(90deg, #2563eb 0%, #3b82f6 100%)' : prediccion.orden === 2 ? 'linear-gradient(90deg, #7c3aed 0%, #a855f7 100%)' : '#94a3b8';
                  const textColor = esPrincipal ? '#2563eb' : prediccion.orden === 2 ? '#7c3aed' : '#64748b';

                  return (
                    <div key={`${prediccion.orden}-${prediccion.falla}`} style={{ backgroundColor: esPrincipal ? '#f8faff' : '#ffffff', padding: esPrincipal ? '10px 12px' : '6px 0', borderRadius: '8px', border: esPrincipal ? '1px solid #dbeafe' : 'none' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', marginBottom: '6px', fontSize: '13px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ color: 'var(--text-main)', fontWeight: esPrincipal ? 700 : 500 }}>
                            {prediccion.orden}. {prediccion.falla}
                          </span>
                          {esPrincipal && (
                            <span style={{ fontSize: '10px', fontWeight: 700, backgroundColor: '#eff6ff', color: '#1d4ed8', padding: '1px 6px', borderRadius: '6px', border: '1px solid #bfdbfe' }}>
                              Predicción Ganadora
                            </span>
                          )}
                        </div>
                        <strong style={{ color: textColor, fontSize: '13px', whiteSpace: 'nowrap' }}>
                          {prediccion.probabilidad}%
                        </strong>
                      </div>
                      <div style={{ width: '100%', height: '8px', borderRadius: '999px', backgroundColor: '#e2e8f0', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${Math.max(1, Math.min(100, prediccion.probabilidad))}%`,
                            height: '100%',
                            borderRadius: '999px',
                            background: barColor,
                            transition: 'width 0.4s ease',
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              <div style={{ display: 'flex', gap: '16px', marginTop: '14px', paddingTop: '12px', borderTop: '1px solid var(--border-color)', fontSize: '12px', color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
                <span>🎯 Hipótesis Seleccionada: <strong>{diagnosticoSeleccionadoModal.falla_predicha}</strong></span>
                <span>📊 Confianza: <strong>{diagnosticoSeleccionadoModal.confianza}%</strong></span>
              </div>
            </div>

            {/* 5. Section 2: Evidencia Recuperada por RAG */}
            <div style={{ border: '1px solid var(--border-color)', borderRadius: '12px', padding: '18px', backgroundColor: '#ffffff' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ width: '28px', height: '28px', borderRadius: '6px', backgroundColor: '#f0fdf4', color: '#16a34a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <BookOpen size={16} />
                  </div>
                  <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                    2. Evidencia Recuperada por RAG (Manuales Técnicos)
                  </h4>
                </div>
                {diagnosticoSeleccionadoModal.similitud_rag !== undefined && (
                  <span
                    style={{
                      fontSize: '12px',
                      fontWeight: 600,
                      padding: '3px 10px',
                      borderRadius: '12px',
                      backgroundColor: diagnosticoSeleccionadoModal.similitud_rag > 0 ? '#ecfdf5' : '#f1f5f9',
                      color: diagnosticoSeleccionadoModal.similitud_rag > 0 ? '#059669' : '#64748b',
                      border: `1px solid ${diagnosticoSeleccionadoModal.similitud_rag > 0 ? '#a7f3d0' : '#e2e8f0'}`,
                    }}
                  >
                    Similitud RAG: <strong>{diagnosticoSeleccionadoModal.similitud_rag}%</strong>
                  </span>
                )}
              </div>

              {diagnosticoSeleccionadoModal.fuente_manual && (
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px', fontStyle: 'italic' }}>
                  Referencia documental: {diagnosticoSeleccionadoModal.fuente_manual}
                </div>
              )}

              <pre
                style={{
                  fontSize: '13px',
                  fontFamily: 'inherit',
                  whiteSpace: 'pre-wrap',
                  backgroundColor: 'var(--bg-subtle)',
                  padding: '14px',
                  borderRadius: '8px',
                  color: 'var(--text-main)',
                  lineHeight: 1.5,
                  margin: 0,
                  border: '1px solid var(--border-color)',
                }}
              >
                {diagnosticoSeleccionadoModal.procedimiento_rag}
              </pre>
            </div>

            {/* 6. Section 3: Tiempo Estimado y Gravedad */}
            <div style={{ border: '1px solid var(--border-color)', borderRadius: '12px', padding: '18px', backgroundColor: '#ffffff' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <div style={{ width: '28px', height: '28px', borderRadius: '6px', backgroundColor: '#fffbeb', color: '#d97706', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Clock size={16} />
                </div>
                <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                  3. Tiempo Estimado y Gravedad
                </h4>
              </div>
              <div
                style={{
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  backgroundColor: 'var(--bg-subtle)',
                  padding: '12px 14px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-color)',
                  lineHeight: 1.5,
                }}
              >
                {diagnosticoSeleccionadoModal.tiempo_gravedad}
              </div>
            </div>

            {/* 7. Section 4: Síntesis Técnica Gemini (si existe) */}
            {diagnosticoSeleccionadoModal.sintesis_llm && (
              <div style={{ border: '1px solid var(--border-color)', borderRadius: '12px', padding: '18px', backgroundColor: '#ffffff' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '28px', height: '28px', borderRadius: '6px', backgroundColor: '#faf5ff', color: '#9333ea', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Sparkles size={16} />
                    </div>
                    <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                      4. Síntesis Técnica de Gemini
                    </h4>
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    Modelo: <strong>{diagnosticoSeleccionadoModal.llm_modelo || 'Gemini-1.5-Flash'}</strong>
                  </span>
                </div>

                <div
                  style={{
                    fontSize: '13px',
                    whiteSpace: 'pre-wrap',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.55,
                    backgroundColor: 'var(--bg-subtle)',
                    padding: '14px',
                    borderRadius: '8px',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  {diagnosticoSeleccionadoModal.sintesis_llm}
                </div>

                <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginTop: '12px', paddingTop: '10px', borderTop: '1px solid var(--border-color)', fontSize: '11px', color: 'var(--text-muted)' }}>
                  <span>📥 Tokens Entrada: <strong>{diagnosticoSeleccionadoModal.tokens_entrada}</strong></span>
                  <span>📤 Tokens Salida: <strong>{diagnosticoSeleccionadoModal.tokens_salida}</strong></span>
                </div>
              </div>
            )}

            {/* 8. Formulario de Validación Administrativa Rediseñado */}
            <form
              onSubmit={handleGuardarConfirmacion}
              style={{
                backgroundColor: '#f8fafc',
                border: '1px solid #cbd5e1',
                borderRadius: '12px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldCheck size={20} style={{ color: 'var(--primary)' }} />
                <div>
                  <h4 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                    Validación Administrativa del Diagnóstico
                  </h4>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '2px 0 0 0' }}>
                    Selecciona el estado de confirmación técnica para auditar el resultado en la base de datos.
                  </p>
                </div>
              </div>

              {errorGuardado && (
                <div style={{ padding: '10px 14px', borderRadius: '8px', backgroundColor: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertCircle size={16} />
                  <span>{errorGuardado}</span>
                </div>
              )}

              {/* Botones Interactivos de Estado (Selector Visual) */}
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--text-main)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Estado de Validación:
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
                  {/* Confirmado */}
                  <button
                    type="button"
                    onClick={() => setNuevoEstado('confirmado')}
                    style={{
                      padding: '12px 14px',
                      borderRadius: '10px',
                      border: nuevoEstado === 'confirmado' ? '2px solid #059669' : '1px solid #e2e8f0',
                      backgroundColor: nuevoEstado === 'confirmado' ? '#ecfdf5' : '#ffffff',
                      color: nuevoEstado === 'confirmado' ? '#065f46' : 'var(--text-secondary)',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      boxShadow: nuevoEstado === 'confirmado' ? '0 2px 6px rgba(5,150,105,0.15)' : 'none',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, fontSize: '13px', marginBottom: '2px' }}>
                      <CheckCircle2 size={16} style={{ color: '#059669' }} />
                      <span>Confirmado</span>
                    </div>
                    <span style={{ fontSize: '11px', color: nuevoEstado === 'confirmado' ? '#047857' : 'var(--text-muted)', display: 'block' }}>
                      Falla verificada físicamente
                    </span>
                  </button>

                  {/* En Revisión */}
                  <button
                    type="button"
                    onClick={() => setNuevoEstado('en_revision')}
                    style={{
                      padding: '12px 14px',
                      borderRadius: '10px',
                      border: nuevoEstado === 'en_revision' ? '2px solid #d97706' : '1px solid #e2e8f0',
                      backgroundColor: nuevoEstado === 'en_revision' ? '#fffbeb' : '#ffffff',
                      color: nuevoEstado === 'en_revision' ? '#92400e' : 'var(--text-secondary)',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      boxShadow: nuevoEstado === 'en_revision' ? '0 2px 6px rgba(217,119,6,0.15)' : 'none',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, fontSize: '13px', marginBottom: '2px' }}>
                      <AlertTriangle size={16} style={{ color: '#d97706' }} />
                      <span>En Revisión</span>
                    </div>
                    <span style={{ fontSize: '11px', color: nuevoEstado === 'en_revision' ? '#b45309' : 'var(--text-muted)', display: 'block' }}>
                      Desmontando o evaluando
                    </span>
                  </button>

                  {/* Descartado */}
                  <button
                    type="button"
                    onClick={() => setNuevoEstado('descartado')}
                    style={{
                      padding: '12px 14px',
                      borderRadius: '10px',
                      border: nuevoEstado === 'descartado' ? '2px solid #e11d48' : '1px solid #e2e8f0',
                      backgroundColor: nuevoEstado === 'descartado' ? '#fff1f2' : '#ffffff',
                      color: nuevoEstado === 'descartado' ? '#9f1239' : 'var(--text-secondary)',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      boxShadow: nuevoEstado === 'descartado' ? '0 2px 6px rgba(225,29,72,0.15)' : 'none',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, fontSize: '13px', marginBottom: '2px' }}>
                      <XCircle size={16} style={{ color: '#e11d48' }} />
                      <span>Descartado</span>
                    </div>
                    <span style={{ fontSize: '11px', color: nuevoEstado === 'descartado' ? '#be123c' : 'var(--text-muted)', display: 'block' }}>
                      Falla diferente a predicción
                    </span>
                  </button>
                </div>
              </div>

              {/* Observación técnica del administrador */}
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--text-main)', marginBottom: '6px' }}>
                  Observación Técnica del Administrador / Revisor: {nuevoEstado === 'descartado' && <span style={{ color: '#ef4444' }}>* (Obligatoria al descartar)</span>}
                </label>
                <Input
                  placeholder={nuevoEstado === 'descartado' ? 'Indique el motivo técnico por el cual se descarta...' : 'Ej. Se verificó con escáner OBD-II y pastillas cambiadas.'}
                  value={notasMecanico}
                  onChange={(e) => setNotasMecanico(e.target.value)}
                  required={nuevoEstado === 'descartado'}
                />
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '4px' }}>
                <Button type="button" variant="secondary" onClick={onCerrarModalDetalle}>
                  Cancelar
                </Button>
                <Button type="submit" variant="primary" disabled={guardando}>
                  {guardando ? 'Guardando...' : 'Guardar Validación'}
                </Button>
              </div>
            </form>
          </div>
        </Modal>
      )}
    </div>
  );
};
