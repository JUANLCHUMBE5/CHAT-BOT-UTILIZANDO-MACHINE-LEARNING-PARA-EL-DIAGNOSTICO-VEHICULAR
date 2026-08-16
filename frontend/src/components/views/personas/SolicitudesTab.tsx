import React, { useState } from 'react';
import {
  UserCheck,
  UserX,
  Clock,
  Sparkles,
  AlertTriangle,
  ShieldCheck,
  History
} from 'lucide-react';
import type { SolicitudAcceso } from '../../../types';
import { Modal } from '../../common/Modal';
import { getErrorMessage } from '../../../utils/errors';
import { apiService } from '../../../services/api';

export interface SolicitudesTabProps {
  solicitudes: SolicitudAcceso[];
  cargando: boolean;
  onRecargar: () => void;
}

export const SolicitudesTab: React.FC<SolicitudesTabProps> = ({
  solicitudes,
  cargando,
  onRecargar,
}) => {
  const [subSeccion, setSubSeccion] = useState<'pendientes' | 'historial'>('pendientes');

  // Approval modal state
  const [modalAprobado, setModalAprobado] = useState<{
    abierto: boolean;
    nombreUsuario: string;
    telefono: string;
  } | null>(null);
  const [aprobandoId, setAprobandoId] = useState<string | null>(null);

  // Rejection modal state
  const [modalRechazo, setModalRechazo] = useState<{
    abierto: boolean;
    solicitud: SolicitudAcceso | null;
  } | null>(null);
  const [motivoRechazo, setMotivoRechazo] = useState('');
  const [rechazando, setRechazando] = useState(false);
  const [errorRechazo, setErrorRechazo] = useState<string | null>(null);

  // Notification banners (replaces alert)
  const [notificacionError, setNotificacionError] = useState<string | null>(null);

  const pendientes = solicitudes.filter((s) => s.estado === 'pendiente');
  const historial = solicitudes.filter((s) => s.estado !== 'pendiente');

  const handleAprobarSolicitud = async (sol: SolicitudAcceso) => {
    setAprobandoId(sol.id);
    setNotificacionError(null);
    try {
      await apiService.aprobarSolicitudAcceso(sol.id);
      setModalAprobado({
        abierto: true,
        nombreUsuario: sol.usuario_nombre,
        telefono: sol.telefono,
      });
      onRecargar();
    } catch (error: unknown) {
      setNotificacionError(getErrorMessage(error, 'Error al aprobar la solicitud'));
    } finally {
      setAprobandoId(null);
    }
  };

  const handleAbrirModalRechazo = (sol: SolicitudAcceso) => {
    setModalRechazo({ abierto: true, solicitud: sol });
    setMotivoRechazo('');
    setErrorRechazo(null);
  };

  const handleConfirmarRechazo = async () => {
    if (!modalRechazo?.solicitud) return;
    const motivoTrimmed = motivoRechazo.trim();
    if (!motivoTrimmed) {
      setErrorRechazo('El motivo de rechazo es obligatorio y no puede estar vacío.');
      return;
    }

    setRechazando(true);
    setErrorRechazo(null);
    try {
      await apiService.rechazarSolicitudAcceso(modalRechazo.solicitud.id, motivoTrimmed);
      setModalRechazo(null);
      setMotivoRechazo('');
      onRecargar();
    } catch (error: unknown) {
      setErrorRechazo(getErrorMessage(error, 'Error al rechazar la solicitud'));
    } finally {
      setRechazando(false);
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
          <AlertTriangle size={18} style={{ flexShrink: 0 }} />
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

      {/* Sub-section Navigation */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
        <button
          type="button"
          onClick={() => setSubSeccion('pendientes')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            fontSize: '13px',
            fontWeight: 600,
            cursor: 'pointer',
            backgroundColor: subSeccion === 'pendientes' ? '#3b82f6' : 'transparent',
            color: subSeccion === 'pendientes' ? '#ffffff' : 'var(--text-secondary)',
            transition: 'all 0.2s ease',
          }}
        >
          <Clock size={16} />
          <span>Pendientes por Revisar</span>
          <span
            style={{
              padding: '2px 8px',
              borderRadius: '12px',
              fontSize: '11px',
              fontWeight: 700,
              backgroundColor: subSeccion === 'pendientes' ? 'rgba(255, 255, 255, 0.25)' : 'rgba(245, 158, 11, 0.15)',
              color: subSeccion === 'pendientes' ? '#ffffff' : '#d97706',
            }}
          >
            {pendientes.length}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setSubSeccion('historial')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            fontSize: '13px',
            fontWeight: 600,
            cursor: 'pointer',
            backgroundColor: subSeccion === 'historial' ? '#3b82f6' : 'transparent',
            color: subSeccion === 'historial' ? '#ffffff' : 'var(--text-secondary)',
            transition: 'all 0.2s ease',
          }}
        >
          <History size={16} />
          <span>Historial de Solicitudes</span>
          <span
            style={{
              padding: '2px 8px',
              borderRadius: '12px',
              fontSize: '11px',
              fontWeight: 700,
              backgroundColor: subSeccion === 'historial' ? 'rgba(255, 255, 255, 0.25)' : 'var(--bg-card-hover)',
              color: subSeccion === 'historial' ? '#ffffff' : 'var(--text-muted)',
            }}
          >
            {historial.length}
          </span>
        </button>
      </div>

      {/* Sub-section Content */}
      {subSeccion === 'pendientes' ? (
        <div>
          {pendientes.length === 0 ? (
            <div
              style={{
                padding: '48px 24px',
                textAlign: 'center',
                backgroundColor: '#ffffff',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-muted)',
              }}
            >
              <ShieldCheck size={48} style={{ color: '#10b981', marginBottom: '12px', opacity: 0.8 }} />
              <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-main)', margin: '0 0 6px 0' }}>
                No hay solicitudes pendientes
              </h3>
              <p style={{ fontSize: '13px', margin: 0, color: 'var(--text-secondary)' }}>
                Todas las solicitudes de acceso al taller han sido procesadas.
              </p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
              {pendientes.map((sol) => (
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
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                      <div>
                        <h4 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>
                          {sol.usuario_nombre}
                        </h4>
                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                          {sol.telefono}
                        </span>
                      </div>
                      <span
                        style={{
                          padding: '4px 10px',
                          borderRadius: '12px',
                          fontSize: '11px',
                          fontWeight: 600,
                          backgroundColor: 'rgba(245, 158, 11, 0.12)',
                          color: '#b45309',
                          textTransform: 'capitalize',
                        }}
                      >
                        Rol: {sol.rol_solicitado || 'Mecánico'}
                      </span>
                    </div>

                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <div>
                        <strong style={{ color: 'var(--text-main)' }}>Fecha: </strong>
                        {sol.solicitado_en}
                      </div>
                      {sol.observaciones && (
                        <div style={{ fontStyle: 'italic', backgroundColor: 'var(--bg-main)', padding: '8px 10px', borderRadius: '6px' }}>
                          "{sol.observaciones}"
                        </div>
                      )}
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '10px', paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
                    <button
                      type="button"
                      onClick={() => handleAprobarSolicitud(sol)}
                      disabled={aprobandoId === sol.id || cargando}
                      style={{
                        flex: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px',
                        padding: '9px 14px',
                        backgroundColor: '#10b981',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '13px',
                        fontWeight: 600,
                        cursor: aprobandoId === sol.id ? 'not-allowed' : 'pointer',
                      }}
                    >
                      <UserCheck size={16} />
                      <span>{aprobandoId === sol.id ? 'Aprobando...' : 'Aprobar Mecánico'}</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleAbrirModalRechazo(sol)}
                      disabled={aprobandoId === sol.id || cargando}
                      style={{
                        padding: '9px 14px',
                        backgroundColor: '#ffffff',
                        color: '#ef4444',
                        border: '1px solid #fca5a5',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '13px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                    >
                      <UserX size={16} />
                      <span>Rechazar</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Historial view */
        <div style={{ backgroundColor: '#ffffff', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--bg-main)', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Usuario</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Teléfono / ID</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Estado</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Solicitado</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Revisado por / Fecha</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Motivo / Observaciones</th>
              </tr>
            </thead>
            <tbody>
              {historial.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No hay solicitudes registradas en el historial.
                  </td>
                </tr>
              ) : (
                historial.map((s) => (
                  <tr key={s.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-main)' }}>
                      {s.usuario_nombre}
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                      {s.telefono}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      {s.estado === 'aprobada' ? (
                        <span style={{ padding: '4px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 600, backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#047857' }}>
                          APROBADA
                        </span>
                      ) : (
                        <span style={{ padding: '4px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 600, backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#b91c1c' }}>
                          RECHAZADA
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                      {s.solicitado_en}
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                      {s.revisado_por || 'Sistema'} <br />
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{s.revisado_en || '-'}</span>
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)', maxWidth: '240px' }}>
                      {s.observaciones || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Confirmación de autorización exclusiva por WhatsApp */}
      {modalAprobado && (
        <Modal
          isOpen={modalAprobado.abierto}
          onClose={() => setModalAprobado(null)}
          title="Mecánico Aprobado Exitosamente"
          maxWidth="500px"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', backgroundColor: 'rgba(16, 185, 129, 0.08)', padding: '14px', borderRadius: 'var(--radius-md)' }}>
              <Sparkles size={28} color="#10b981" />
              <div>
                <h4 style={{ margin: 0, fontSize: '15px', fontWeight: 600, color: '#047857' }}>
                  {modalAprobado.nombreUsuario}
                </h4>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  Su número quedó autorizado para trabajar con el chatbot de WhatsApp.
                </span>
              </div>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(59, 130, 246, 0.08)',
                border: '1px solid rgba(59, 130, 246, 0.25)',
                borderRadius: 'var(--radius-md)',
                padding: '12px 14px',
                display: 'flex',
                gap: '10px',
                alignItems: 'flex-start',
              }}
            >
              <ShieldCheck size={18} color="#2563eb" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div style={{ fontSize: '12px', color: '#1e40af', lineHeight: 1.4 }}>
                <strong>Acceso por WhatsApp:</strong> el mecánico no recibe usuario ni contraseña para esta web. Ya puede escribir desde <strong>{modalAprobado.telefono}</strong> y enviar síntomas o notas de voz a CarBot.
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
              <button
                type="button"
                onClick={() => setModalAprobado(null)}
                style={{
                  padding: '8px 20px',
                  backgroundColor: 'var(--text-main)',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Entendido y Cerrar
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Rejection Modal with Mandatory Motive */}
      {modalRechazo && (
        <Modal
          isOpen={modalRechazo.abierto}
          onClose={() => setModalRechazo(null)}
          title="Rechazar Solicitud de Acceso"
          maxWidth="480px"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
              Ingresa el motivo del rechazo para <strong>{modalRechazo.solicitud?.usuario_nombre}</strong>. Este motivo se registrará en el historial de auditoría.
            </p>

            {errorRechazo && (
              <div
                style={{
                  padding: '10px 14px',
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: 'var(--radius-sm)',
                  color: '#ef4444',
                  fontSize: '13px',
                }}
              >
                {errorRechazo}
              </div>
            )}

            <div>
              <label
                htmlFor="motivo-rechazo-input"
                style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}
              >
                Motivo del Rechazo <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <textarea
                id="motivo-rechazo-input"
                value={motivoRechazo}
                onChange={(e) => {
                  setMotivoRechazo(e.target.value);
                  if (errorRechazo) setErrorRechazo(null);
                }}
                placeholder="Ej: No pertenece al personal técnico autorizado del taller..."
                rows={3}
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-color)',
                  fontSize: '13px',
                  fontFamily: 'inherit',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
              <button
                type="button"
                onClick={() => setModalRechazo(null)}
                disabled={rechazando}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#ffffff',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '13px',
                  fontWeight: 500,
                  color: 'var(--text-secondary)',
                  cursor: rechazando ? 'not-allowed' : 'pointer',
                }}
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleConfirmarRechazo}
                disabled={rechazando || !motivoRechazo.trim()}
                style={{
                  padding: '8px 18px',
                  backgroundColor: !motivoRechazo.trim() || rechazando ? '#cbd5e1' : '#ef4444',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: !motivoRechazo.trim() || rechazando ? 'not-allowed' : 'pointer',
                }}
              >
                {rechazando ? 'Procesando...' : 'Confirmar Rechazo'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
