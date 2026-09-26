import React, { useState, useMemo, useEffect } from 'react';
import { Search, Lock, Unlock, ChevronLeft, ChevronRight, Users, MessageSquare, History } from 'lucide-react';
import type { Cliente } from '../../../types';
import { ConfirmModal } from '../../common/ConfirmModal';
import { getErrorMessage } from '../../../utils/errors';
import { apiService, enmascararIdentificadorSensible } from '../../../services/api';

export interface ClientesTabProps {
  clientes: Cliente[];
  cargando: boolean;
  onRecargar: () => void;
  onVerHistorialDiagnosticos?: (cliente: Cliente) => void;
}

export const ClientesTab: React.FC<ClientesTabProps> = ({
  clientes,
  cargando,
  onRecargar,
  onVerHistorialDiagnosticos,
}) => {
  const [busqueda, setBusqueda] = useState('');
  const [paginaActual, setPaginaActual] = useState(1);
  const [elementosPorPagina, setElementosPorPagina] = useState(10);

  // Modal confirmación de bloqueo/desbloqueo
  const [clienteAccionModal, setClienteAccionModal] = useState<{
    cliente: Cliente;
    accion: 'bloquear' | 'desbloquear';
  } | null>(null);
  const [procesandoAccion, setProcesandoAccion] = useState(false);
  const [notificacionError, setNotificacionError] = useState<string | null>(null);

  // Filtering by search term
  const clientesFiltrados = useMemo(() => {
    if (!busqueda.trim()) return clientes;
    const term = busqueda.toLowerCase().trim();
    return clientes.filter(
      (c) =>
        (c.nombres && c.nombres.toLowerCase().includes(term)) ||
        (c.telefono && c.telefono.toLowerCase().includes(term)) ||
        (c.tipo_identificador && c.tipo_identificador.toLowerCase().includes(term))
    );
  }, [clientes, busqueda]);

  // Total and Pagination calculations
  const total = clientesFiltrados.length;
  const totalPaginas = Math.max(1, Math.ceil(total / elementosPorPagina));

  useEffect(() => {
    if (paginaActual > totalPaginas && totalPaginas > 0) {
      setPaginaActual(totalPaginas);
    }
  }, [totalPaginas, paginaActual]);

  const clientesPaginados = useMemo(() => {
    const inicio = (paginaActual - 1) * elementosPorPagina;
    return clientesFiltrados.slice(inicio, inicio + elementosPorPagina);
  }, [clientesFiltrados, paginaActual, elementosPorPagina]);

  const inicioRegistro = total === 0 ? 0 : (paginaActual - 1) * elementosPorPagina + 1;
  const finRegistro = Math.min(paginaActual * elementosPorPagina, total);

  const handleCambiarPagina = (nuevaPagina: number) => {
    if (nuevaPagina >= 1 && nuevaPagina <= totalPaginas) {
      setPaginaActual(nuevaPagina);
    }
  };

  const handleConfirmarAccionBloqueo = async () => {
    if (!clienteAccionModal) return;
    setProcesandoAccion(true);
    setNotificacionError(null);
    try {
      await apiService.toggleBloquearCliente(clienteAccionModal.cliente.id);
      setClienteAccionModal(null);
      onRecargar();
    } catch (error: unknown) {
      setNotificacionError(getErrorMessage(error, 'Error al modificar estado de bloqueo'));
    } finally {
      setProcesandoAccion(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {notificacionError && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '10px 14px',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-sm)',
            color: '#b91c1c',
            fontSize: '12px',
          }}
        >
          <span style={{ flex: 1 }}>{notificacionError}</span>
          <button
            type="button"
            onClick={() => setNotificacionError(null)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#b91c1c', fontWeight: 700 }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Barra de Controles: Búsqueda y Selector de Paginación */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '10px',
          backgroundColor: '#ffffff',
          padding: '8px 12px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
        }}
      >
        <div style={{ position: 'relative', minWidth: '220px', flex: '1 1 260px', maxWidth: '380px' }}>
          <Search
            size={14}
            style={{
              position: 'absolute',
              left: '10px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)',
            }}
          />
          <input
            type="text"
            value={busqueda}
            onChange={(e) => {
              setBusqueda(e.target.value);
              setPaginaActual(1);
            }}
            placeholder="Buscar por nombre o teléfono..."
            style={{
              width: '100%',
              padding: '6px 10px 6px 30px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)',
              fontSize: '12px',
              boxSizing: 'border-box',
              outline: 'none',
            }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
          <span>Mostrar:</span>
          <select
            value={elementosPorPagina}
            onChange={(e) => {
              setElementosPorPagina(Number(e.target.value));
              setPaginaActual(1);
            }}
            style={{
              padding: '5px 8px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)',
              fontSize: '12px',
              backgroundColor: '#ffffff',
            }}
          >
            <option value={5}>5 por página</option>
            <option value={10}>10 por página</option>
            <option value={20}>20 por página</option>
            <option value={50}>50 por página</option>
          </select>
        </div>
      </div>

      {/* 1. Vista Desktop: Tabla */}
      <div
        className="responsive-table-desktop"
        style={{
          backgroundColor: '#ffffff',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
          overflow: 'hidden',
        }}
      >
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12.5px' }}>
          <thead>
            <tr style={{ backgroundColor: 'var(--bg-main)', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              <th style={{ padding: '10px 14px', fontWeight: 700 }}>Usuario WhatsApp</th>
              <th style={{ padding: '10px 14px', fontWeight: 700 }}>Teléfono Enmascarado</th>
              <th style={{ padding: '10px 14px', fontWeight: 700 }}>Estado</th>
              <th style={{ padding: '10px 14px', fontWeight: 700 }}>Fecha Registro</th>
              <th style={{ padding: '10px 14px', fontWeight: 700 }}>Última Interacción</th>
              <th style={{ padding: '10px 14px', fontWeight: 700, textAlign: 'right' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {cargando ? (
              <tr>
                <td colSpan={6} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  Cargando directorio de usuarios WhatsApp...
                </td>
              </tr>
            ) : clientesPaginados.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <Users size={32} style={{ margin: '0 auto 8px auto', opacity: 0.5 }} />
                  <div>No se encontraron usuarios WhatsApp registrados que coincidan con la búsqueda.</div>
                </td>
              </tr>
            ) : (
              clientesPaginados.map((cliente) => {
                const telSeguro = enmascararIdentificadorSensible(cliente.telefono, 'telefono') || cliente.telefono;
                const estaBloqueado = Boolean(cliente.bloqueado);

                return (
                  <tr key={cliente.id} className="table-row-hover" style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '10px 14px', fontWeight: 600, color: 'var(--text-main)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div
                          style={{
                            width: '26px',
                            height: '26px',
                            borderRadius: '50%',
                            backgroundColor: '#f0fdf4',
                            color: '#16a34a',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            border: '1px solid #bbf7d0',
                            flexShrink: 0,
                          }}
                        >
                          <MessageSquare size={13} />
                        </div>
                        <div>
                          <div>{cliente.nombres}</div>
                          {cliente.tiene_solicitud_pendiente && (
                            <span
                              style={{
                                backgroundColor: 'rgba(245, 158, 11, 0.15)',
                                color: '#b45309',
                                fontSize: '10px',
                                fontWeight: 700,
                                padding: '1px 5px',
                                borderRadius: '8px',
                              }}
                            >
                              Solicitud Pendiente
                            </span>
                          )}
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: '10px 14px', color: 'var(--text-secondary)' }}>
                      {telSeguro}
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: '10px',
                          fontSize: '11px',
                          fontWeight: 700,
                          display: 'inline-block',
                          backgroundColor: estaBloqueado
                            ? 'rgba(239, 68, 68, 0.15)'
                            : !cliente.activo
                            ? '#f1f5f9'
                            : 'rgba(16, 185, 129, 0.15)',
                          color: estaBloqueado ? '#b91c1c' : !cliente.activo ? '#64748b' : '#047857',
                        }}
                      >
                        {estaBloqueado ? 'Bloqueado' : !cliente.activo ? 'Inactivo' : 'Activo'}
                      </span>
                    </td>
                    <td style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>
                      {cliente.fecha_registro}
                    </td>
                    <td style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>
                      {cliente.ultima_interaccion || 'Sin interacciones'}
                    </td>
                    <td style={{ padding: '10px 14px', textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                        {onVerHistorialDiagnosticos && (
                          <button
                            type="button"
                            onClick={() => onVerHistorialDiagnosticos(cliente)}
                            title="Ver historial de diagnósticos"
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              padding: '4px 8px',
                              backgroundColor: '#ffffff',
                              border: '1px solid var(--border-color)',
                              borderRadius: '6px',
                              fontSize: '11px',
                              fontWeight: 600,
                              color: 'var(--primary)',
                              cursor: 'pointer',
                            }}
                          >
                            <History size={12} />
                            <span>Ver historial</span>
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() =>
                            setClienteAccionModal({
                              cliente,
                              accion: estaBloqueado ? 'desbloquear' : 'bloquear',
                            })
                          }
                          title={estaBloqueado ? 'Desbloquear usuario' : 'Bloquear usuario'}
                          style={{
                            background: 'none',
                            border: '1px solid var(--border-color)',
                            cursor: 'pointer',
                            color: estaBloqueado ? '#059669' : '#dc2626',
                            padding: '4px 6px',
                            borderRadius: '6px',
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          {estaBloqueado ? <Unlock size={13} /> : <Lock size={13} />}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* 2. Vista Móvil: Cards Feed */}
      <div className="responsive-cards-mobile">
        {cargando ? (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
            Cargando usuarios WhatsApp...
          </div>
        ) : clientesPaginados.length === 0 ? (
          <div style={{ padding: '24px', textAlign: 'center', backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '12px' }}>
            No se encontraron usuarios WhatsApp registrados.
          </div>
        ) : (
          clientesPaginados.map((cliente) => {
            const telSeguro = enmascararIdentificadorSensible(cliente.telefono, 'telefono') || cliente.telefono;
            const estaBloqueado = Boolean(cliente.bloqueado);

            return (
              <div
                key={cliente.id}
                style={{
                  backgroundColor: '#ffffff',
                  borderRadius: '8px',
                  border: '1px solid var(--border-color)',
                  padding: '10px 12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.03)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <MessageSquare size={14} style={{ color: '#16a34a' }} />
                    <span style={{ fontWeight: 700, fontSize: '13px', color: 'var(--text-main)' }}>
                      {cliente.nombres}
                    </span>
                  </div>
                  <span
                    style={{
                      padding: '2px 6px',
                      borderRadius: '8px',
                      fontSize: '10px',
                      fontWeight: 700,
                      backgroundColor: estaBloqueado ? '#fee2e2' : !cliente.activo ? '#f1f5f9' : '#dcfce7',
                      color: estaBloqueado ? '#b91c1c' : !cliente.activo ? '#64748b' : '#15803d',
                    }}
                  >
                    {estaBloqueado ? 'Bloqueado' : !cliente.activo ? 'Inactivo' : 'Activo'}
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)' }}>
                  <span>📱 {telSeguro}</span>
                  <span style={{ color: 'var(--text-muted)' }}>Reg: {cliente.fecha_registro}</span>
                </div>

                <div style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>
                  Última actividad: {cliente.ultima_interaccion || 'Sin interacciones'}
                </div>

                <div style={{ display: 'flex', gap: '6px', paddingTop: '6px', borderTop: '1px solid #f1f5f9' }}>
                  {onVerHistorialDiagnosticos && (
                    <button
                      type="button"
                      onClick={() => onVerHistorialDiagnosticos(cliente)}
                      style={{
                        flex: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '4px',
                        padding: '6px 10px',
                        backgroundColor: '#f8fafc',
                        border: '1px solid var(--border-color)',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: 600,
                        color: 'var(--primary)',
                        cursor: 'pointer',
                      }}
                    >
                      <History size={13} />
                      <span>Ver historial</span>
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() =>
                      setClienteAccionModal({
                        cliente,
                        accion: estaBloqueado ? 'desbloquear' : 'bloquear',
                      })
                    }
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '6px 10px',
                      backgroundColor: '#ffffff',
                      border: `1px solid ${estaBloqueado ? '#86efac' : '#fca5a5'}`,
                      borderRadius: '6px',
                      fontSize: '11px',
                      fontWeight: 600,
                      color: estaBloqueado ? '#059669' : '#dc2626',
                      cursor: 'pointer',
                    }}
                  >
                    {estaBloqueado ? <Unlock size={13} /> : <Lock size={13} />}
                    <span>{estaBloqueado ? 'Desbloquear' : 'Bloquear'}</span>
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Barra de Paginación Corregida */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '10px 12px',
          backgroundColor: '#ffffff',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
          flexWrap: 'wrap',
          gap: '10px',
          fontSize: '12px',
          color: 'var(--text-secondary)',
        }}
      >
        <div>
          Mostrando{' '}
          <strong>{inicioRegistro}</strong>{' '}
          a{' '}
          <strong>{finRegistro}</strong>{' '}
          de <strong>{total}</strong> usuarios WhatsApp
        </div>

        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <button
            type="button"
            onClick={() => handleCambiarPagina(paginaActual - 1)}
            disabled={paginaActual <= 1 || cargando}
            style={{
              padding: '5px 10px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              backgroundColor: '#ffffff',
              color: paginaActual <= 1 ? 'var(--text-muted)' : 'var(--text-main)',
              cursor: paginaActual <= 1 ? 'not-allowed' : 'pointer',
              opacity: paginaActual <= 1 ? 0.5 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '11.5px',
              fontWeight: 600,
            }}
          >
            <ChevronLeft size={13} />
            <span>Anterior</span>
          </button>

          <span style={{ fontWeight: 600, color: 'var(--text-main)', padding: '0 4px' }}>
            {paginaActual} / {totalPaginas}
          </span>

          <button
            type="button"
            onClick={() => handleCambiarPagina(paginaActual + 1)}
            disabled={paginaActual >= totalPaginas || cargando}
            style={{
              padding: '5px 10px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              backgroundColor: '#ffffff',
              color: paginaActual >= totalPaginas ? 'var(--text-muted)' : 'var(--text-main)',
              cursor: paginaActual >= totalPaginas ? 'not-allowed' : 'pointer',
              opacity: paginaActual >= totalPaginas ? 0.5 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '11.5px',
              fontWeight: 600,
            }}
          >
            <span>Siguiente</span>
            <ChevronRight size={13} />
          </button>
        </div>
      </div>

      {/* Modal de Bloqueo/Desbloqueo */}
      {clienteAccionModal && (
        <ConfirmModal
          isOpen={Boolean(clienteAccionModal)}
          onClose={() => setClienteAccionModal(null)}
          onConfirm={handleConfirmarAccionBloqueo}
          cargando={procesandoAccion}
          title={
            clienteAccionModal.accion === 'bloquear'
              ? 'Confirmar Bloqueo de Usuario'
              : 'Confirmar Desbloqueo de Usuario'
          }
          variant={clienteAccionModal.accion === 'bloquear' ? 'danger' : 'success'}
          confirmText={
            clienteAccionModal.accion === 'bloquear' ? 'Sí, Bloquear' : 'Sí, Desbloquear'
          }
          message={
            <div>
              <p style={{ margin: '0 0 8px 0' }}>
                ¿Deseas <strong>{clienteAccionModal.accion}</strong> al usuario{' '}
                <strong>{clienteAccionModal.cliente.nombres}</strong> ({enmascararIdentificadorSensible(clienteAccionModal.cliente.telefono, 'telefono')})?
              </p>
              {clienteAccionModal.accion === 'bloquear' && (
                <p style={{ margin: 0, fontSize: '11.5px', color: '#b91c1c', fontWeight: 500 }}>
                  El usuario bloqueado no podrá interactuar con CarBot ni solicitar acceso de taller.
                </p>
              )}
            </div>
          }
        />
      )}
    </div>
  );
};
