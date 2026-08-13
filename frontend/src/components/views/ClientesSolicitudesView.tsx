import React, { useState, useEffect, useCallback } from 'react';
import {
  UserCheck,
  UserX,
  Search,
  CheckCircle,
  Clock,
  MessageSquare,
  ShieldAlert,
  Copy,
  Check,
  RefreshCw,
  Sparkles,
  Smartphone,
  Info
} from 'lucide-react';
import type { Cliente, SolicitudAcceso } from '../../types';
import { getErrorMessage } from '../../utils/errors';
import { apiService } from '../../services/api';

interface ClientesSolicitudesViewProps {
  onRecargarMecanicos?: () => void;
}

export const ClientesSolicitudesView: React.FC<ClientesSolicitudesViewProps> = ({
  onRecargarMecanicos,
}) => {
  const [subTab, setSubTab] = useState<'solicitudes' | 'clientes'>('solicitudes');
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [solicitudes, setSolicitudes] = useState<SolicitudAcceso[]>([]);
  const [busqueda, setBusqueda] = useState('');
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Modal aprobación exitosa
  const [modalAprobado, setModalAprobado] = useState<{
    abierto: boolean;
    nombreUsuario: string;
    passwordTemporal: string;
    telefono: string;
  } | null>(null);
  const [copiado, setCopiado] = useState(false);

  const cargarDatos = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const [listaClientes, listaSolicitudes] = await Promise.all([
        apiService.getClientes(busqueda),
        apiService.getSolicitudesAcceso(),
      ]);
      setClientes(listaClientes);
      setSolicitudes(listaSolicitudes);
    } catch (error: unknown) {
      setError(getErrorMessage(error, 'Error al cargar los datos'));
    } finally {
      setCargando(false);
    }
  }, [busqueda]);

  useEffect(() => {
    cargarDatos();
  }, [cargarDatos]);

  const handleAprobarSolicitud = async (sol: SolicitudAcceso) => {
    try {
      const res = await apiService.aprobarSolicitudAcceso(sol.id);
      setModalAprobado({
        abierto: true,
        nombreUsuario: sol.usuario_nombre,
        passwordTemporal: res.password_temporal,
        telefono: sol.telefono,
      });
      await cargarDatos();
      if (onRecargarMecanicos) onRecargarMecanicos();
    } catch (error: unknown) {
      alert(getErrorMessage(error, 'Error al aprobar solicitud'));
    }
  };

  const handleRechazarSolicitud = async (id: string) => {
    if (!confirm('¿Estás seguro de rechazar esta solicitud de acceso?')) return;
    try {
      await apiService.rechazarSolicitudAcceso(id);
      await cargarDatos();
    } catch (error: unknown) {
      alert(getErrorMessage(error, 'Error al rechazar solicitud'));
    }
  };

  const handleToggleBloquear = async (cliente: Cliente) => {
    const accion = cliente.bloqueado ? 'desbloquear' : 'bloquear';
    if (!confirm(`¿Deseas ${accion} el contacto de ${cliente.nombres}?`)) return;
    try {
      await apiService.toggleBloquearCliente(cliente.id);
      await cargarDatos();
    } catch (error: unknown) {
      alert(getErrorMessage(error, 'Error al modificar estado de bloqueo'));
    }
  };

  const handleCopiarClave = () => {
    if (modalAprobado?.passwordTemporal) {
      navigator.clipboard.writeText(modalAprobado.passwordTemporal);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2500);
    }
  };

  const solicitudesPendientes = solicitudes.filter((s) => s.estado === 'pendiente');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
            Clientes y Solicitudes de Acceso
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Gestiona los contactos de WhatsApp, consultas del taller y autorizaciones de mecánicos.
          </p>
        </div>

        <button
          onClick={cargarDatos}
          disabled={cargando}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 14px',
            backgroundColor: '#ffffff',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '13px',
            fontWeight: 500,
            cursor: 'pointer',
            color: 'var(--text-secondary)',
          }}
        >
          <RefreshCw size={14} className={cargando ? 'animate-spin' : ''} />
          <span>Actualizar</span>
        </button>
      </div>

      {/* Stats Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div
          style={{
            padding: '18px',
            backgroundColor: '#ffffff',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
          }}
        >
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#3b82f6',
            }}
          >
            <Clock size={22} />
          </div>
          <div>
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Solicitudes Pendientes
            </div>
            <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-main)', marginTop: '2px' }}>
              {solicitudesPendientes.length}
            </div>
          </div>
        </div>

        <div
          style={{
            padding: '18px',
            backgroundColor: '#ffffff',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
          }}
        >
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#10b981',
            }}
          >
            <MessageSquare size={22} />
          </div>
          <div>
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Clientes Registrados
            </div>
            <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-main)', marginTop: '2px' }}>
              {clientes.length}
            </div>
          </div>
        </div>

        <div
          style={{
            padding: '18px',
            backgroundColor: '#ffffff',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
          }}
        >
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ef4444',
            }}
          >
            <ShieldAlert size={22} />
          </div>
          <div>
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Contactos Bloqueados
            </div>
            <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-main)', marginTop: '2px' }}>
              {clientes.filter((c) => c.bloqueado).length}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs navigation */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border-color)', gap: '8px' }}>
        <button
          onClick={() => setSubTab('solicitudes')}
          style={{
            padding: '10px 18px',
            fontSize: '14px',
            fontWeight: 600,
            color: subTab === 'solicitudes' ? 'var(--primary)' : 'var(--text-secondary)',
            borderBottom: subTab === 'solicitudes' ? '2px solid var(--primary)' : '2px solid transparent',
            background: 'none',
            borderTop: 'none',
            borderLeft: 'none',
            borderRight: 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <span>Solicitudes de Mecánico</span>
          {solicitudesPendientes.length > 0 && (
            <span
              style={{
                backgroundColor: '#ef4444',
                color: '#ffffff',
                fontSize: '11px',
                fontWeight: 700,
                padding: '2px 7px',
                borderRadius: '10px',
              }}
            >
              {solicitudesPendientes.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setSubTab('clientes')}
          style={{
            padding: '10px 18px',
            fontSize: '14px',
            fontWeight: 600,
            color: subTab === 'clientes' ? 'var(--primary)' : 'var(--text-secondary)',
            borderBottom: subTab === 'clientes' ? '2px solid var(--primary)' : '2px solid transparent',
            background: 'none',
            borderTop: 'none',
            borderLeft: 'none',
            borderRight: 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <span>Directorio de Clientes ({clientes.length})</span>
        </button>
      </div>

      {error && (
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: '#fee2e2',
            color: '#b91c1c',
            borderRadius: 'var(--radius-sm)',
            fontSize: '13px',
          }}
        >
          {error}
        </div>
      )}

      {/* Contenido según pestaña */}
      {subTab === 'solicitudes' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {solicitudesPendientes.length === 0 ? (
            <div
              style={{
                padding: '40px 20px',
                textAlign: 'center',
                backgroundColor: '#ffffff',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-color)',
              }}
            >
              <CheckCircle size={36} color="#10b981" style={{ margin: '0 auto 12px' }} />
              <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-main)' }}>
                No hay solicitudes de acceso pendientes
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', maxWidth: '400px', margin: '6px auto 0' }}>
                Cuando un cliente solicite acceso como mecánico desde el chatbot de WhatsApp, aparecerá en esta lista para su autorización.
              </p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
              {solicitudesPendientes.map((sol) => (
                <div
                  key={sol.id}
                  style={{
                    backgroundColor: '#ffffff',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-color)',
                    padding: '20px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    boxShadow: 'var(--shadow-sm)',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <h4 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                          {sol.usuario_nombre}
                        </h4>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px', color: 'var(--text-secondary)', fontSize: '13px' }}>
                          <Smartphone size={14} />
                          <span>{sol.telefono}</span>
                        </div>
                      </div>
                      <span
                        style={{
                          fontSize: '11px',
                          fontWeight: 600,
                          backgroundColor: 'rgba(245, 158, 11, 0.1)',
                          color: '#d97706',
                          padding: '4px 8px',
                          borderRadius: '6px',
                        }}
                      >
                        Pendiente
                      </span>
                    </div>

                    <div style={{ marginTop: '14px', padding: '10px 12px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px', fontSize: '12px' }}>
                      <div style={{ color: 'var(--text-muted)' }}>Fecha de Solicitud:</div>
                      <div style={{ fontWeight: 600, color: 'var(--text-main)', marginTop: '2px' }}>
                        {sol.solicitado_en}
                      </div>
                      {sol.observaciones && (
                        <div style={{ marginTop: '6px', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                          "{sol.observaciones}"
                        </div>
                      )}
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                    <button
                      onClick={() => handleAprobarSolicitud(sol)}
                      style={{
                        flex: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px',
                        padding: '10px',
                        backgroundColor: '#10b981',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '13px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'background-color 0.15s ease',
                      }}
                    >
                      <UserCheck size={16} />
                      <span>Aprobar Mecánico</span>
                    </button>

                    <button
                      onClick={() => handleRechazarSolicitud(sol.id)}
                      style={{
                        padding: '10px 14px',
                        backgroundColor: 'transparent',
                        color: '#ef4444',
                        border: '1px solid #fca5a5',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '13px',
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      <UserX size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Historial de solicitudes anteriores */}
          {solicitudes.some((s) => s.estado !== 'pendiente') && (
            <div style={{ marginTop: '24px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)', marginBottom: '12px' }}>
                Historial de Solicitudes Procesadas
              </h3>
              <div
                style={{
                  backgroundColor: '#ffffff',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-color)',
                  overflowX: 'auto',
                }}
              >
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ backgroundColor: 'var(--bg-subtle)', borderBottom: '1px solid var(--border-color)' }}>
                      <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Usuario</th>
                      <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Teléfono / ID</th>
                      <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Estado</th>
                      <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Solicitado</th>
                      <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Revisado Por</th>
                      <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Fecha Respuesta</th>
                    </tr>
                  </thead>
                  <tbody>
                    {solicitudes
                      .filter((s) => s.estado !== 'pendiente')
                      .map((s) => (
                        <tr key={s.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                          <td style={{ padding: '12px 16px', fontWeight: 600 }}>{s.usuario_nombre}</td>
                          <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{s.telefono}</td>
                          <td style={{ padding: '12px 16px' }}>
                            <span
                              style={{
                                fontSize: '11px',
                                fontWeight: 700,
                                padding: '3px 8px',
                                borderRadius: '4px',
                                backgroundColor: s.estado === 'aprobada' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                                color: s.estado === 'aprobada' ? '#10b981' : '#ef4444',
                              }}
                            >
                              {s.estado.toUpperCase()}
                            </span>
                          </td>
                          <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{s.solicitado_en}</td>
                          <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{s.revisado_por || 'Administrador'}</td>
                          <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{s.revisado_en || '-'}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Directorio de Clientes */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Barra de búsqueda */}
          <div style={{ display: 'flex', gap: '12px' }}>
            <div
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 14px',
                backgroundColor: '#ffffff',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
              }}
            >
              <Search size={16} color="var(--text-muted)" />
              <input
                type="text"
                placeholder="Buscar por nombre o últimos 4 dígitos..."
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                style={{
                  border: 'none',
                  outline: 'none',
                  width: '100%',
                  fontSize: '13px',
                  backgroundColor: 'transparent',
                }}
              />
            </div>
          </div>

          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-color)',
              overflowX: 'auto',
            }}
          >
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--bg-subtle)', borderBottom: '1px solid var(--border-color)' }}>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Contacto</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Identificador / Teléfono</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Tipo ID</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Fecha Registro</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Última Interacción</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Estado</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-secondary)', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {clientes.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                      No se encontraron contactos de clientes registrados.
                    </td>
                  </tr>
                ) : (
                  clientes.map((c) => (
                    <tr key={c.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '12px 16px' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{c.nombres}</div>
                        {c.tiene_solicitud_pendiente && (
                          <span style={{ fontSize: '11px', color: '#d97706', fontWeight: 600 }}>
                            • Solicitud de mecánico pendiente
                          </span>
                        )}
                      </td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                        {c.telefono}
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span
                          style={{
                            fontSize: '11px',
                            fontWeight: 600,
                            padding: '2px 6px',
                            borderRadius: '4px',
                            backgroundColor: 'var(--bg-subtle)',
                            color: 'var(--text-secondary)',
                          }}
                        >
                          {c.tipo_identificador}
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{c.fecha_registro}</td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{c.ultima_interaccion}</td>
                      <td style={{ padding: '12px 16px' }}>
                        <span
                          style={{
                            fontSize: '11px',
                            fontWeight: 700,
                            padding: '3px 8px',
                            borderRadius: '4px',
                            backgroundColor: c.bloqueado ? '#fee2e2' : '#dcfce7',
                            color: c.bloqueado ? '#b91c1c' : '#15803d',
                          }}
                        >
                          {c.bloqueado ? 'BLOQUEADO' : 'ACTIVO'}
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                        <button
                          onClick={() => handleToggleBloquear(c)}
                          style={{
                            padding: '6px 10px',
                            fontSize: '12px',
                            fontWeight: 600,
                            color: c.bloqueado ? '#15803d' : '#b91c1c',
                            backgroundColor: c.bloqueado ? '#dcfce7' : '#fee2e2',
                            border: 'none',
                            borderRadius: 'var(--radius-sm)',
                            cursor: 'pointer',
                          }}
                        >
                          {c.bloqueado ? 'Desbloquear' : 'Bloquear'}
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal Aprobación Exitosa */}
      {modalAprobado && modalAprobado.abierto && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.6)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
            padding: '16px',
          }}
        >
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: 'var(--radius-md)',
              width: '100%',
              maxWidth: '460px',
              padding: '24px',
              boxShadow: 'var(--shadow-lg)',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#10b981' }}>
              <div
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  backgroundColor: '#dcfce7',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Sparkles size={22} color="#10b981" />
              </div>
              <div>
                <h3 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                  ¡Mecánico Autorizado con Éxito!
                </h3>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0 }}>
                  Se ha generado la clave temporal y encolado la notificación por WhatsApp.
                </p>
              </div>
            </div>

            <div style={{ padding: '14px', backgroundColor: 'var(--bg-subtle)', borderRadius: '8px', fontSize: '13px' }}>
              <div style={{ color: 'var(--text-secondary)' }}>Mecánico:</div>
              <div style={{ fontWeight: 700, fontSize: '15px', color: 'var(--text-main)', marginTop: '2px' }}>
                {modalAprobado.nombreUsuario}
              </div>
              <div style={{ color: 'var(--text-secondary)', marginTop: '4px', fontSize: '12px' }}>
                Teléfono: {modalAprobado.telefono}
              </div>
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
                Contraseña Temporal Generada:
              </label>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 14px',
                  backgroundColor: '#f1f5f9',
                  borderRadius: '6px',
                  border: '1px dashed #cbd5e1',
                  fontFamily: 'monospace',
                  fontSize: '16px',
                  fontWeight: 700,
                  color: 'var(--primary)',
                }}
              >
                <span>{modalAprobado.passwordTemporal}</span>
                <button
                  onClick={handleCopiarClave}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '4px 8px',
                    backgroundColor: '#ffffff',
                    border: '1px solid #cbd5e1',
                    borderRadius: '4px',
                    fontSize: '12px',
                    cursor: 'pointer',
                  }}
                >
                  {copiado ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                  <span>{copiado ? 'Copiado' : 'Copiar'}</span>
                </button>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '11px', color: 'var(--text-secondary)' }}>
              <Info size={16} color="var(--primary)" style={{ flexShrink: 0, marginTop: '2px' }} />
              <span>
                El usuario ya puede diagnosticar fallas vía WhatsApp y deberá cambiar esta contraseña al ingresar al panel web.
              </span>
            </div>

            <button
              onClick={() => setModalAprobado(null)}
              style={{
                width: '100%',
                padding: '10px',
                backgroundColor: 'var(--primary)',
                color: '#ffffff',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer',
                marginTop: '8px',
              }}
            >
              Aceptar y Cerrar
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
