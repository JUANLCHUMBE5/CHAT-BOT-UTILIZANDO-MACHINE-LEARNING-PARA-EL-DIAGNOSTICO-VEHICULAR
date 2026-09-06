import React from 'react';
import { AlertTriangle, Loader2 } from 'lucide-react';
import { Modal } from '../../../common/Modal';
import { Button } from '../../../common/Button';
import { Input } from '../../../common/Input';
import type { Mecanico } from '../../../../types';

interface EquipoTallerEditModalProps {
  mecanico: Mecanico | null;
  onClose: () => void;
  onSubmit: (e: React.FormEvent) => Promise<void>;
  nombres: string;
  onNombresChange: (v: string) => void;
  username: string;
  onUsernameChange: (v: string) => void;
  telefono: string;
  onTelefonoChange: (v: string) => void;
  password: string;
  onPasswordChange: (v: string) => void;
  deseaCambiarPassword: boolean;
  onDeseaCambiarPasswordChange: (v: boolean) => void;
  guardando: boolean;
  error: string | null;
}

export const EquipoTallerEditModal: React.FC<EquipoTallerEditModalProps> = ({
  mecanico,
  onClose,
  onSubmit,
  nombres,
  onNombresChange,
  username,
  onUsernameChange,
  telefono,
  onTelefonoChange,
  password,
  onPasswordChange,
  deseaCambiarPassword,
  onDeseaCambiarPasswordChange,
  guardando,
  error,
}) => {
  if (!mecanico) return null;

  const isAdmin = mecanico.rol === 'administrador' || (mecanico.rol as string) === 'admin';

  return (
    <Modal isOpen={!!mecanico} onClose={onClose} title={`Editar Perfil — ${mecanico.nombres}`}>
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
            value={nombres}
            onChange={(e) => onNombresChange(e.target.value)}
            required
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
            Usuario
          </label>
          <Input
            value={username}
            onChange={(e) => onUsernameChange(e.target.value)}
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
            Teléfono WhatsApp
          </label>
          <Input
            value={telefono}
            onChange={(e) => onTelefonoChange(e.target.value)}
          />
        </div>

        {isAdmin && (
          <div style={{ paddingTop: '8px', borderTop: '1px dashed var(--border-color)' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={deseaCambiarPassword}
                onChange={(e) => onDeseaCambiarPasswordChange(e.target.checked)}
              />
              <span>Cambiar contraseña del panel de administración</span>
            </label>

            {deseaCambiarPassword && (
              <div style={{ marginTop: '10px' }}>
                <Input
                  type="password"
                  placeholder="Nueva contraseña (mínimo 12 caracteres, mayúsculas, minúsculas y números)..."
                  value={password}
                  onChange={(e) => onPasswordChange(e.target.value)}
                  required={deseaCambiarPassword}
                />
              </div>
            )}
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
                <span>Guardando...</span>
              </>
            ) : (
              <span>Guardar Cambios</span>
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
