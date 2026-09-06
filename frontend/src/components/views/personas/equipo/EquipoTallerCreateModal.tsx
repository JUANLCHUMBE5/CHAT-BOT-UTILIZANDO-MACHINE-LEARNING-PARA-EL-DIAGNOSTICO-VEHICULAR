import React from 'react';
import { PlusCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { Modal } from '../../../common/Modal';
import { Button } from '../../../common/Button';
import { Input } from '../../../common/Input';
import type { MecanicoRol } from '../../../../types';

interface EquipoTallerCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (e: React.FormEvent) => Promise<void>;
  nombre: string;
  onNombreChange: (v: string) => void;
  username: string;
  onUsernameChange: (v: string) => void;
  telefono: string;
  onTelefonoChange: (v: string) => void;
  password: string;
  onPasswordChange: (v: string) => void;
  rol: MecanicoRol;
  onRolChange: (v: MecanicoRol) => void;
  guardando: boolean;
  error: string | null;
  esAdmin: boolean;
}

export const EquipoTallerCreateModal: React.FC<EquipoTallerCreateModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  nombre,
  onNombreChange,
  username,
  onUsernameChange,
  telefono,
  onTelefonoChange,
  password,
  onPasswordChange,
  rol,
  onRolChange,
  guardando,
  error,
  esAdmin,
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Registrar Personal Técnico">
      <form onSubmit={onSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {error && (
          <div
            style={{
              padding: '10px 14px',
              borderRadius: '8px',
              backgroundColor: '#fee2e2',
              color: '#991b1b',
              fontSize: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
            Nombres y Apellidos *
          </label>
          <Input
            placeholder="Ej. Carlos Mendoza"
            value={nombre}
            onChange={(e) => onNombreChange(e.target.value)}
            required
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
            Usuario (Opcional)
          </label>
          <Input
            placeholder="Ej. cmendoza"
            value={username}
            onChange={(e) => onUsernameChange(e.target.value)}
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
            Teléfono WhatsApp *
          </label>
          <Input
            placeholder="Ej. +51 987654321"
            value={telefono}
            onChange={(e) => onTelefonoChange(e.target.value)}
            required
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
            Rol Asignado
          </label>
          <select
            value={rol}
            onChange={(e) => onRolChange(e.target.value as MecanicoRol)}
            style={{
              width: '100%',
              padding: '9px 12px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)',
              fontSize: '13px',
              backgroundColor: '#ffffff',
            }}
          >
            <option value="mecanico">Mecánico</option>
            <option value="jefe_taller">Jefe de Taller</option>
            {esAdmin && <option value="administrador">Administrador (Acceso al Panel Web)</option>}
          </select>
        </div>

        {rol === 'administrador' && (
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
              Contraseña de Acceso al Panel * (Mínimo 12 caracteres, mayúsculas, minúsculas y números)
            </label>
            <Input
              type="password"
              placeholder="Contraseña robusta para el panel..."
              value={password}
              onChange={(e) => onPasswordChange(e.target.value)}
              required
            />
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
          <Button type="button" variant="secondary" onClick={onClose} disabled={guardando}>
            Cancelar
          </Button>
          <Button type="submit" variant="primary" disabled={guardando}>
            {guardando ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                <span>Registrando...</span>
              </>
            ) : (
              <>
                <PlusCircle size={14} />
                <span>Registrar Personal</span>
              </>
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
