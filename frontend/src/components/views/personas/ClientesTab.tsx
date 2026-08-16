import React, { useState, useMemo } from 'react';
import { Search, Lock, Unlock, ChevronLeft, ChevronRight, Users } from 'lucide-react';
import type { Cliente } from '../../../types';
import { ConfirmModal } from '../../common/ConfirmModal';
import { getErrorMessage } from '../../../utils/errors';
import { apiService } from '../../../services/api';

export interface ClientesTabProps {
  clientes: Cliente[];
  cargando: boolean;
  onRecargar: () => void;
}

export const ClientesTab: React.FC<ClientesTabProps> = ({
  clientes,
  cargando,
  onRecargar,
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
        c.nombres.toLowerCase().includes(term) ||
        c.telefono.toLowerCase().includes(term) ||
        (c.tipo_identificador && c.tipo_identificador.toLowerCase().includes(term))
    );
  }, [clientes, busqueda]);

  // Pagination calculations
  const totalPaginas = Math.ceil(clientesFiltrados.length / elementosPorPagina) || 1;
  const clientesPaginados = useMemo(() => {
    const inicio = (paginaActual - 1) * elementosPorPagina;
    return clientesFiltrados.slice(inicio, inicio + elementosPorPagina);
  }, [clientesFiltrados, paginaActual, elementosPorPagina]);

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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {notificacionError && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '12px 16px',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-sm)',
            color: '#b91c1c',
            fontSize: '13px',
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

      {/* Controls Bar: Search & Page Size */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ position: 'relative', minWidth: '280px', flex: 1, maxWidth: '420px' }}>
          <Search
            size={16}
            style={{
              position: 'absolute',
              left: '12px',
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
            placeholder="Buscar por nombre, teléfono o placa..."
            style={{
              width: '100%',
              padding: '9px 12px 9px 36px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)',
              fontSize: '13px',
              boxSizing: 'border-box',
            }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: 'var(--text-secondary)' }}>
          <span>Mostrar:</span>
          <select
            value={elementosPorPagina}
            onChange={(e) => {
              setElementosPorPagina(Number(e.target.value));
              setPaginaActual(1);
            }}
            style={{
              padding: '6px 10px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)',
              fontSize: '13px',
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

      {/* Directory Table */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr style={{ backgroundColor: 'var(--bg-main)', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Cliente</th>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Teléfono / WhatsApp</th>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Estado</th>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Fecha Registro</th>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Última Interacción</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, textAlign: 'right' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {cargando ? (
              <tr>
                <td colSpan={6} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  Cargando directorio de clientes...
                </td>
              </tr>
            ) : clientesPaginados.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <Users size={36} style={{ marginBottom: '8px', opacity: 0.5 }} />
                  <div>No se encontraron clientes registrados que coincidan con la búsqueda.</div>
                </td>
              </tr>
            ) : (
              clientesPaginados.map((cliente) => {
                // Status derivation
                let statusLabel = 'Activo';
                let badgeStyle = { backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#047857' };

                if (cliente.bloqueado) {
                  statusLabel = 'Bloqueado';
                  badgeStyle = { backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#b91c1c' };
                } else if (!cliente.activo) {
                  statusLabel = 'Inactivo';
                  badgeStyle = { backgroundColor: 'rgba(245, 158, 11, 0.15)', color: '#b45309' };
                }

                return (
                  <tr key={cliente.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-main)' }}>
                      {cliente.nombres}
                      {cliente.tiene_solicitud_pendiente && (
                        <span
                          style={{
                            marginLeft: '8px',
                            padding: '2px 6px',
                            borderRadius: '8px',
                            fontSize: '10px',
                            fontWeight: 700,
                            backgroundColor: 'rgba(59, 130, 246, 0.15)',
                            color: '#1d4ed8',
                          }}
                        >
                          Solicitud Pendiente
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                      {cliente.telefono}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span
                        style={{
                          padding: '4px 10px',
                          borderRadius: '12px',
                          fontSize: '11px',
                          fontWeight: 600,
                          ...badgeStyle,
                        }}
                      >
                        {statusLabel}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                      {cliente.fecha_registro}
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                      {cliente.ultima_interaccion}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                      <button
                        type="button"
                        onClick={() =>
                          setClienteAccionModal({
                            cliente,
                            accion: cliente.bloqueado ? 'desbloquear' : 'bloquear',
                          })
                        }
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '6px 12px',
                          backgroundColor: cliente.bloqueado ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                          color: cliente.bloqueado ? '#047857' : '#b91c1c',
                          border: 'none',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '12px',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        {cliente.bloqueado ? <Unlock size={14} /> : <Lock size={14} />}
                        <span>{cliente.bloqueado ? 'Desbloquear' : 'Bloquear'}</span>
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', padding: '4px 0' }}>
        <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Mostrando {clientesFiltrados.length === 0 ? 0 : (paginaActual - 1) * elementosPorPagina + 1} a{' '}
          {Math.min(paginaActual * elementosPorPagina, clientesFiltrados.length)} de {clientesFiltrados.length} clientes
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            type="button"
            onClick={() => handleCambiarPagina(paginaActual - 1)}
            disabled={paginaActual === 1}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '6px 10px',
              backgroundColor: '#ffffff',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '13px',
              color: 'var(--text-secondary)',
              cursor: paginaActual === 1 ? 'not-allowed' : 'pointer',
              opacity: paginaActual === 1 ? 0.5 : 1,
            }}
          >
            <ChevronLeft size={16} />
            <span>Anterior</span>
          </button>

          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', padding: '0 8px' }}>
            Página {paginaActual} de {totalPaginas}
          </span>

          <button
            type="button"
            onClick={() => handleCambiarPagina(paginaActual + 1)}
            disabled={paginaActual === totalPaginas}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '6px 10px',
              backgroundColor: '#ffffff',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '13px',
              color: 'var(--text-secondary)',
              cursor: paginaActual === totalPaginas ? 'not-allowed' : 'pointer',
              opacity: paginaActual === totalPaginas ? 0.5 : 1,
            }}
          >
            <span>Siguiente</span>
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {/* Block/Unblock Confirmation Modal (replaces browser confirm()) */}
      {clienteAccionModal && (
        <ConfirmModal
          isOpen={!!clienteAccionModal}
          onClose={() => setClienteAccionModal(null)}
          onConfirm={handleConfirmarAccionBloqueo}
          cargando={procesandoAccion}
          title={
            clienteAccionModal.accion === 'bloquear'
              ? 'Confirmar Bloqueo de Cliente'
              : 'Confirmar Desbloqueo de Cliente'
          }
          variant={clienteAccionModal.accion === 'bloquear' ? 'danger' : 'success'}
          confirmText={
            clienteAccionModal.accion === 'bloquear' ? 'Sí, Bloquear' : 'Sí, Desbloquear'
          }
          message={
            <div>
              <p style={{ margin: '0 0 10px 0' }}>
                ¿Deseas <strong>{clienteAccionModal.accion}</strong> el contacto de{' '}
                <strong>{clienteAccionModal.cliente.nombres}</strong> ({clienteAccionModal.cliente.telefono})?
              </p>
              {clienteAccionModal.accion === 'bloquear' && (
                <p style={{ margin: 0, fontSize: '12px', color: '#b91c1c', fontWeight: 500 }}>
                  Al bloquear este cliente, no podrá enviar mensajes ni realizar consultas de diagnóstico al chatbot de WhatsApp.
                </p>
              )}
            </div>
          }
        />
      )}
    </div>
  );
};
