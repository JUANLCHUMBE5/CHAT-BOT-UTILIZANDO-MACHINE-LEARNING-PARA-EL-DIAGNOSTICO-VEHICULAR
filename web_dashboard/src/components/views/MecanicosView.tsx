import React, { useState } from 'react';
import { UserPlus, Shield, ShieldOff, Lock, Unlock, Phone, Search, Trash2, CheckCircle } from 'lucide-react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { Modal } from '../common/Modal';
import type { Mecanico } from '../../types';

interface MecanicosViewProps {
  mecanicos: Mecanico[];
  onRegistrarMecanico: (data: { nombres: string; telefono: string; password: string; rol: 'mecanico' | 'jefe_taller' | 'administrador' }) => Promise<void>;
  onToggleActivar: (id: string) => void;
  onToggleBloquear: (id: string) => void;
  onEliminarMecanico: (id: string) => Promise<void>;
  onCambiarRol?: (id: string, nuevoRol: 'mecanico' | 'jefe_taller' | 'administrador') => void;
}

export const MecanicosView: React.FC<MecanicosViewProps> = ({
  mecanicos,
  onRegistrarMecanico,
  onToggleActivar,
  onToggleBloquear,
  onEliminarMecanico,
  onCambiarRol,
}) => {
  const [busqueda, setBusqueda] = useState('');
  const [modalRegistroAbierto, setModalRegistroAbierto] = useState(false);

  // Deletion modal & notification state
  const [mecanicoAEliminar, setMecanicoAEliminar] = useState<Mecanico | null>(null);
  const [eliminando, setEliminando] = useState(false);
  const [mensajeExito, setMensajeExito] = useState<string | null>(null);
  const [modalError, setModalError] = useState<string | null>(null);

  // Form state
  const [nombres, setNombres] = useState('');
  const [telefono, setTelefono] = useState('');
  const [password, setPassword] = useState('');
  const [rol, setRol] = useState<'mecanico' | 'jefe_taller' | 'administrador'>('mecanico');
  const [formError, setFormError] = useState('');
  const [guardando, setGuardando] = useState(false);

  const mecanicosFiltrados = mecanicos.filter(
    (m) =>
      m.nombres.toLowerCase().includes(busqueda.toLowerCase()) ||
      m.telefono.includes(busqueda)
  );

  const handleSubmitRegistro = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nombres.trim() || !telefono.trim() || !password.trim()) {
      setFormError('Nombre, teléfono y contraseña son requeridos.');
      return;
    }
    if (password.trim().length < 6) {
      setFormError('La contraseña debe tener al menos 6 caracteres.');
      return;
    }

    setGuardando(true);
    setFormError('');
    try {
      await onRegistrarMecanico({ nombres: nombres.trim(), telefono: telefono.trim(), password: password.trim(), rol });
      setNombres('');
      setTelefono('');
      setPassword('');
      setRol('mecanico');
      setModalRegistroAbierto(false);
      setMensajeExito('Mecánico registrado y autorizando exitosamente.');
      setTimeout(() => setMensajeExito(null), 4000);
    } catch (err: any) {
      setFormError(err?.message || 'Error al registrar el mecánico en el servidor.');
    } finally {
      setGuardando(false);
    }
  };

  const handleConfirmarEliminacion = async () => {
    if (!mecanicoAEliminar) return;
    setEliminando(true);
    setModalError(null);
    try {
      await onEliminarMecanico(mecanicoAEliminar.id);
      const nombreGuardado = mecanicoAEliminar.nombres;
      setMecanicoAEliminar(null);
      setMensajeExito(`Mecánico ${nombreGuardado} eliminado exitosamente del sistema.`);
      setTimeout(() => setMensajeExito(null), 4000);
    } catch (err: any) {
      setModalError(err?.message || 'No se pudo conectar con el servidor backend FastAPI.');
    } finally {
      setEliminando(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top action bar */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
        }}
      >
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-main)' }}>
            Gestión de Mecánicos del Taller
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Registra, activa, bloquea o elimina a los mecánicos autorizados del taller.
          </p>
        </div>

        <Button
          variant="primary"
          icon={<UserPlus size={18} />}
          onClick={() => setModalRegistroAbierto(true)}
        >
          Registrar Mecánico
        </Button>
      </div>

      {/* Banner de Mensaje de Éxito */}
      {mensajeExito && (
        <div
          style={{
            padding: '12px 16px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--status-success-bg)',
            color: 'var(--status-success-text)',
            fontSize: '14px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
          className="animate-fade-in"
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle size={18} />
            <span>{mensajeExito}</span>
          </div>
          <button
            onClick={() => setMensajeExito(null)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontWeight: 700 }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Filter / Search Bar */}
      <Card style={{ padding: '14px' }}>
        <Input
          placeholder="Buscar mecánico por nombre o teléfono WhatsApp..."
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          icon={<Search size={18} />}
        />
      </Card>

      {/* Mechanics Table */}
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
                <th style={{ padding: '12px 16px' }}>Mecánico / Personal</th>
                <th style={{ padding: '12px 16px' }}>Teléfono WhatsApp</th>
                <th style={{ padding: '12px 16px' }}>Rol</th>
                <th style={{ padding: '12px 16px' }}>Estado</th>
                <th style={{ padding: '12px 16px' }}>Diagnósticos</th>
                <th style={{ padding: '12px 16px' }}>Último Acceso</th>
                <th style={{ padding: '12px 16px', textAlign: 'right' }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {mecanicosFiltrados.map((m) => (
                <tr
                  key={m.id}
                  style={{
                    borderBottom: '1px solid var(--border-color)',
                    fontSize: '14px',
                    backgroundColor: m.bloqueado ? '#fff1f2' : '#ffffff',
                  }}
                >
                  <td style={{ padding: '14px 16px', fontWeight: 600, color: 'var(--text-main)' }}>
                    {m.nombres}
                  </td>
                  <td style={{ padding: '14px 16px', color: 'var(--text-secondary)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Phone size={14} color="var(--primary)" />
                      <span>{m.telefono}</span>
                    </div>
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    {onCambiarRol ? (
                      <select
                        value={m.rol}
                        onChange={(e) => onCambiarRol(m.id, e.target.value as any)}
                        style={{
                          padding: '4px 8px',
                          borderRadius: '6px',
                          border: '1px solid var(--border-color)',
                          fontSize: '12px',
                          fontWeight: 600,
                          backgroundColor: m.rol === 'administrador' ? 'var(--primary-light)' : 'var(--bg-subtle)',
                          color: m.rol === 'administrador' ? 'var(--primary)' : 'var(--text-main)',
                          cursor: 'pointer',
                        }}
                      >
                        <option value="mecanico">Mecánico</option>
                        <option value="jefe_taller">Jefe de Taller</option>
                        <option value="administrador">Administrador</option>
                      </select>
                    ) : (
                      <span style={{ textTransform: 'capitalize', color: 'var(--text-secondary)' }}>
                        {m.rol.replace('_', ' ')}
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    {m.bloqueado ? (
                      <Badge type="bloqueado" label="Bloqueado" />
                    ) : m.activo ? (
                      <Badge type="activo" label="Activo" />
                    ) : (
                      <Badge type="inactivo" label="Inactivo" />
                    )}
                  </td>
                  <td style={{ padding: '14px 16px', fontWeight: 600 }}>
                    {m.total_diagnosticos} atenciones
                  </td>
                  <td style={{ padding: '14px 16px', fontSize: '13px', color: 'var(--text-muted)' }}>
                    {m.ultimo_acceso}
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '8px' }}>
                      {/* Activar / Desactivar toggle */}
                      <Button
                        variant={m.activo ? 'secondary' : 'outline'}
                        size="sm"
                        onClick={() => onToggleActivar(m.id)}
                        disabled={m.bloqueado}
                      >
                        {m.activo ? <ShieldOff size={14} /> : <Shield size={14} />}
                        <span>{m.activo ? 'Desactivar' : 'Activar'}</span>
                      </Button>

                      {/* Bloquear toggle */}
                      <Button
                        variant={m.bloqueado ? 'secondary' : 'danger'}
                        size="sm"
                        onClick={() => onToggleBloquear(m.id)}
                      >
                        {m.bloqueado ? <Unlock size={14} /> : <Lock size={14} />}
                        <span>{m.bloqueado ? 'Desbloquear' : 'Bloquear'}</span>
                      </Button>

                      {/* Eliminar botón abre modal en el centro */}
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => setMecanicoAEliminar(m)}
                      >
                        <Trash2 size={14} />
                        <span>Eliminar</span>
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Modal Registrar Nuevo Mecánico */}
      <Modal
        isOpen={modalRegistroAbierto}
        onClose={() => setModalRegistroAbierto(false)}
        title="Registrar Nuevo Mecánico en Taller"
      >
        <form onSubmit={handleSubmitRegistro} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {formError && (
            <div style={{ padding: '10px', borderRadius: '6px', backgroundColor: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', fontSize: '13px' }}>
              {formError}
            </div>
          )}

          <Input
            label="Nombre Completo del Mecánico"
            placeholder="Ej. Pedro Luis Mendoza"
            value={nombres}
            onChange={(e) => setNombres(e.target.value)}
            required
          />

          <Input
            label="Número de WhatsApp Autorizado"
            placeholder="Ej. +51 987 654 321"
            value={telefono}
            onChange={(e) => setTelefono(e.target.value)}
            required
          />

          <Input
            label="Contraseña de Acceso (Mínimo 6 caracteres)"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <Select
            label="Rol de Trabajo"
            value={rol}
            onChange={(e) => setRol(e.target.value as any)}
            options={[
              { value: 'mecanico', label: 'Mecánico de Diagnóstico' },
              { value: 'jefe_taller', label: 'Jefe de Taller' },
              { value: 'administrador', label: 'Administrador General' },
            ]}
          />

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
            <Button type="button" variant="secondary" onClick={() => setModalRegistroAbierto(false)} disabled={guardando}>
              Cancelar
            </Button>
            <Button type="submit" variant="primary" disabled={guardando}>
              {guardando ? 'Guardando...' : 'Guardar y Autorizar'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal Centrado de Confirmación de Eliminación */}
      {mecanicoAEliminar && (
        <Modal
          isOpen={Boolean(mecanicoAEliminar)}
          onClose={() => {
            setMecanicoAEliminar(null);
            setModalError(null);
          }}
          title="Confirmar Eliminación"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {modalError && (
              <div style={{ padding: '10px 14px', borderRadius: '6px', backgroundColor: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', fontSize: '13px', fontWeight: 500 }}>
                ⚠️ {modalError}
              </div>
            )}

            <p style={{ fontSize: '14px', color: 'var(--text-main)', lineHeight: 1.5 }}>
              ¿Está seguro que desea eliminar a <strong>{mecanicoAEliminar.nombres}</strong> ({mecanicoAEliminar.telefono})?
            </p>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Sus diagnósticos anteriores se mantendrán guardados en el historial del taller.
            </p>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setMecanicoAEliminar(null);
                  setModalError(null);
                }}
                disabled={eliminando}
              >
                Cancelar
              </Button>
              <Button
                type="button"
                variant="danger"
                disabled={eliminando}
                onClick={handleConfirmarEliminacion}
              >
                {eliminando ? 'Eliminando...' : 'Sí, Eliminar'}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
