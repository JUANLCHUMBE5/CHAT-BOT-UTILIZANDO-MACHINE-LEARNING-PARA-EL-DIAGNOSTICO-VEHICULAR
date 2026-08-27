import React, { useState, useMemo } from 'react';
import {
  Lock,
  Unlock,
  CheckCircle2,
  AlertTriangle,
  Search,
  Wrench,
  UserX,
  Smartphone,
  Calendar,
  FileSearch,
} from 'lucide-react';
import type { Mecanico } from '../../../types';
import { ConfirmModal } from '../../common/ConfirmModal';
import { Card } from '../../common/Card';
import { getErrorMessage } from '../../../utils/errors';
import { apiService, enmascararIdentificadorSensible } from '../../../services/api';

export interface MecanicosAutorizadosTabProps {
  mecanicos: Mecanico[];
  cargando: boolean;
  onRecargar: () => void;
  onVerConsultasMecanico?: (mecanicoId: string) => void;
}

export const MecanicosAutorizadosTab: React.FC<MecanicosAutorizadosTabProps> = ({
  mecanicos,
  cargando,
  onRecargar,
  onVerConsultasMecanico,
}) => {
  const [busqueda, setBusqueda] = useState('');
  const [filtroEstado, setFiltroEstado] = useState<'todos' | 'activos' | 'bloqueados'>('todos');

  // Feedback notifications
  const [notificacionError, setNotificacionError] = useState<string | null>(null);
  const [notificacionExito, setNotificacionExito] = useState<string | null>(null);

  // Confirmation Modals
  const [confirmBloquearModal, setConfirmBloquearModal] = useState<{
    mecanico: Mecanico;
    estaBloqueando: boolean;
  } | null>(null);
  const [procesandoBloquear, setProcesandoBloquear] = useState(false);

  const [confirmRevocarModal, setConfirmRevocarModal] = useState<Mecanico | null>(null);
  const [procesandoRevocacion, setProcesandoRevocacion] = useState(false);

  // Filtrado de mecánicos
  const mecanicosFiltrados = useMemo(() => {
    return mecanicos.filter((m) => {
      const cumpleBusqueda =
        !busqueda ||
        m.nombres.toLowerCase().includes(busqueda.toLowerCase()) ||
        m.telefono.includes(busqueda);

      if (!cumpleBusqueda) return false;

      if (filtroEstado === 'activos') return m.activo && !m.bloqueado;
      if (filtroEstado === 'bloqueados') return m.bloqueado;
      return true;
    });
  }, [mecanicos, busqueda, filtroEstado]);

  const totalActivos = mecanicos.filter((m) => m.activo && !m.bloqueado).length;
  const totalBloqueados = mecanicos.filter((m) => m.bloqueado).length;

  const handleToggleBloquear = async () => {
    if (!confirmBloquearModal) return;
    setProcesandoBloquear(true);
    setNotificacionError(null);
    setNotificacionExito(null);

    const { mecanico, estaBloqueando } = confirmBloquearModal;
    try {
      await apiService.toggleBloquearMecanico(mecanico.id);
      setNotificacionExito(
        estaBloqueando
          ? `Mecánico "${mecanico.nombres}" bloqueado. Ya no podrá consultar diagnósticos por WhatsApp.`
          : `Mecánico "${mecanico.nombres}" desbloqueado exitosamente.`
      );
      setConfirmBloquearModal(null);
      onRecargar();
    } catch (error: unknown) {
      setNotificacionError(getErrorMessage(error, 'Error al cambiar estado de bloqueo del mecánico'));
    } finally {
      setProcesandoBloquear(false);
    }
  };

  const handleRevocarAcceso = async () => {
    if (!confirmRevocarModal) return;
    setProcesandoRevocacion(true);
    setNotificacionError(null);
    setNotificacionExito(null);

    try {
      await apiService.eliminarMecanico(confirmRevocarModal.id);
      setNotificacionExito(
        `Acceso revocado para "${confirmRevocarModal.nombres}". Su número de WhatsApp ahora tiene rol de cliente.`
      );
      setConfirmRevocarModal(null);
      onRecargar();
    } catch (error: unknown) {
      setNotificacionError(getErrorMessage(error, 'Error al revocar acceso al mecánico'));
    } finally {
      setProcesandoRevocacion(false);
    }
  };

  const formatearFecha = (fechaStr?: string) => {
    if (!fechaStr) return 'N/A';
    try {
      const d = new Date(fechaStr);
      return d.toLocaleDateString('es-PE', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      });
    } catch {
      return fechaStr;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Feedback Alerts */}
      {notificacionExito && (
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: 'var(--radius-md)',
            color: '#059669',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <CheckCircle2 size={16} />
          <span>{notificacionExito}</span>
        </div>
      )}

      {notificacionError && (
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-md)',
            color: '#ef4444',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <AlertTriangle size={16} />
          <span>{notificacionError}</span>
        </div>
      )}

      {/* Header Info & Filter Bar */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '12px',
          backgroundColor: '#ffffff',
          padding: '14px 16px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: '260px' }}>
          <div
            style={{
              position: 'relative',
              flex: 1,
              maxWidth: '360px',
            }}
          >
            <Search
              size={15}
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
              placeholder="Buscar mecánico por nombre o teléfono..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px 8px 32px',
                fontSize: '12px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
                outline: 'none',
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '4px' }}>
            <button
              type="button"
              onClick={() => setFiltroEstado('todos')}
              style={{
                padding: '6px 10px',
                fontSize: '11px',
                fontWeight: 600,
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: filtroEstado === 'todos' ? 'var(--primary)' : 'var(--bg-subtle)',
                color: filtroEstado === 'todos' ? '#ffffff' : 'var(--text-secondary)',
              }}
            >
              Todos ({mecanicos.length})
            </button>
            <button
              type="button"
              onClick={() => setFiltroEstado('activos')}
              style={{
                padding: '6px 10px',
                fontSize: '11px',
                fontWeight: 600,
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: filtroEstado === 'activos' ? '#059669' : 'var(--bg-subtle)',
                color: filtroEstado === 'activos' ? '#ffffff' : 'var(--text-secondary)',
              }}
            >
              Activos ({totalActivos})
            </button>
            {totalBloqueados > 0 && (
              <button
                type="button"
                onClick={() => setFiltroEstado('bloqueados')}
                style={{
                  padding: '6px 10px',
                  fontSize: '11px',
                  fontWeight: 600,
                  borderRadius: '6px',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: filtroEstado === 'bloqueados' ? '#dc2626' : 'var(--bg-subtle)',
                  color: filtroEstado === 'bloqueados' ? '#ffffff' : 'var(--text-secondary)',
                }}
              >
                Bloqueados ({totalBloqueados})
              </button>
            )}
          </div>
        </div>

        <div style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Smartphone size={13} color="var(--primary)" />
          <span>Mecánicos autorizados para realizar consultas diagnósticas vía WhatsApp</span>
        </div>
      </div>

      {/* List of Mechanics */}
      {cargando && mecanicos.length === 0 ? (
        <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
          Cargando lista de mecánicos autorizados...
        </div>
      ) : mecanicosFiltrados.length === 0 ? (
        <Card style={{ padding: '40px 20px', textAlign: 'center' }}>
          <Wrench size={32} style={{ margin: '0 auto 10px auto', color: 'var(--text-muted)', opacity: 0.6 }} />
          <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', margin: '0 0 4px 0' }}>
            No se encontraron mecánicos autorizados
          </h4>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0 }}>
            {busqueda
              ? 'No hay resultados que coincidan con la búsqueda.'
              : 'Las solicitudes aprobadas desde WhatsApp aparecerán automáticamente aquí.'}
          </p>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {mecanicosFiltrados.map((m) => {
            const estaBloqueado = m.bloqueado;
            const telefonoSeguro = enmascararIdentificadorSensible(m.telefono, 'telefono') || m.telefono;

            return (
              <Card
                key={m.id}
                style={{
                  padding: '14px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '14px',
                  flexWrap: 'wrap',
                  borderLeft: estaBloqueado ? '4px solid #ef4444' : '4px solid #10b981',
                }}
              >
                {/* Mechanic Profile Info */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: '220px', flex: 1 }}>
                  <div
                    style={{
                      width: '40px',
                      height: '40px',
                      borderRadius: '50%',
                      backgroundColor: estaBloqueado ? '#fee2e2' : '#e0e7ff',
                      color: estaBloqueado ? '#dc2626' : '#4338ca',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      fontSize: '14px',
                      flexShrink: 0,
                    }}
                  >
                    {m.nombres ? m.nombres.slice(0, 2).toUpperCase() : 'ME'}
                  </div>

                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                        {m.nombres}
                      </h4>
                      <span
                        style={{
                          fontSize: '10px',
                          fontWeight: 700,
                          padding: '1px 6px',
                          borderRadius: '4px',
                          backgroundColor: estaBloqueado ? '#fee2e2' : '#dcfce7',
                          color: estaBloqueado ? '#b91c1c' : '#15803d',
                        }}
                      >
                        {estaBloqueado ? 'BLOQUEADO' : 'AUTORIZADO'}
                      </span>
                    </div>

                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        marginTop: '3px',
                        fontSize: '11px',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Smartphone size={12} style={{ color: 'var(--primary)' }} />
                        <strong>{telefonoSeguro}</strong>
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Calendar size={12} />
                        Autorizado: {formatearFecha(m.fecha_registro)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Diagnostics Count / Activity */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '16px',
                    padding: '6px 12px',
                    backgroundColor: 'var(--bg-subtle)',
                    borderRadius: '8px',
                  }}
                >
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '14px', fontWeight: 800, color: 'var(--primary)' }}>
                      {m.total_diagnosticos ?? 0}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 500 }}>
                      Consultas
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {onVerConsultasMecanico && (
                    <button
                      type="button"
                      onClick={() => onVerConsultasMecanico(m.id)}
                      title="Ver consultas de este mecánico"
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px',
                        padding: '7px 11px',
                        backgroundColor: '#f8fafc',
                        border: '1px solid var(--border-color)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '11px',
                        fontWeight: 600,
                        color: 'var(--text-secondary)',
                        cursor: 'pointer',
                      }}
                    >
                      <FileSearch size={13} />
                      <span className="desktop-only">Historial</span>
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={() =>
                      setConfirmBloquearModal({
                        mecanico: m,
                        estaBloqueando: !estaBloqueado,
                      })
                    }
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      padding: '7px 11px',
                      backgroundColor: estaBloqueado ? '#ecfdf5' : '#fff7ed',
                      border: estaBloqueado ? '1px solid #a7f3d0' : '1px solid #fed7aa',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '11px',
                      fontWeight: 600,
                      color: estaBloqueado ? '#059669' : '#d97706',
                      cursor: 'pointer',
                    }}
                  >
                    {estaBloqueado ? <Unlock size={13} /> : <Lock size={13} />}
                    <span>{estaBloqueado ? 'Desbloquear' : 'Bloquear'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setConfirmRevocarModal(m)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      padding: '7px 11px',
                      backgroundColor: '#fef2f2',
                      border: '1px solid #fecaca',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '11px',
                      fontWeight: 600,
                      color: '#dc2626',
                      cursor: 'pointer',
                    }}
                  >
                    <UserX size={13} />
                    <span>Revocar</span>
                  </button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Confirmation Modal for Block / Unblock */}
      <ConfirmModal
        isOpen={Boolean(confirmBloquearModal)}
        onClose={() => setConfirmBloquearModal(null)}
        onConfirm={handleToggleBloquear}
        cargando={procesandoBloquear}
        title={confirmBloquearModal?.estaBloqueando ? 'Bloquear Mecánico' : 'Desbloquear Mecánico'}
        message={
          confirmBloquearModal?.estaBloqueando
            ? `¿Está seguro de bloquear al mecánico "${confirmBloquearModal?.mecanico.nombres}"? No podrá realizar consultas ni diagnósticos por WhatsApp mientras esté bloqueado.`
            : `¿Desea desbloquear al mecánico "${confirmBloquearModal?.mecanico.nombres}" para que pueda volver a utilizar CarBot por WhatsApp?`
        }
        confirmText={confirmBloquearModal?.estaBloqueando ? 'Sí, Bloquear' : 'Sí, Desbloquear'}
        variant={confirmBloquearModal?.estaBloqueando ? 'danger' : 'primary'}
      />

      {/* Confirmation Modal for Revoking Access */}
      <ConfirmModal
        isOpen={Boolean(confirmRevocarModal)}
        onClose={() => setConfirmRevocarModal(null)}
        onConfirm={handleRevocarAcceso}
        cargando={procesandoRevocacion}
        title="Revocar Acceso de Mecánico"
        message={`¿Está seguro de revocar los permisos de mecánico a "${confirmRevocarModal?.nombres}" (${enmascararIdentificadorSensible(confirmRevocarModal?.telefono || '', 'telefono')})? Su número volverá a ser tratado como cliente estándar de WhatsApp.`}
        confirmText="Sí, Revocar Acceso"
        variant="danger"
      />
    </div>
  );
};
