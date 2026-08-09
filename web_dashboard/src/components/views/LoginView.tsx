import React, { useState } from 'react';
import { Wrench, Lock, User } from 'lucide-react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { apiService } from '../../services/api';
import type { UsuarioSesion } from '../../types';
import type { TokenResponseDTO } from '../../types/dtos';

interface LoginViewProps {
  onLoginSuccess: (user: UsuarioSesion) => void;
}

export const LoginView: React.FC<LoginViewProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [cambioPendiente, setCambioPendiente] = useState<TokenResponseDTO | null>(null);
  const [passwordNueva, setPasswordNueva] = useState('');
  const [passwordConfirmacion, setPasswordConfirmacion] = useState('');

  const completarSesion = (tokenRes: TokenResponseDTO) => {
    if (!tokenRes.user) {
      throw new Error('El servidor no devolvió la información del usuario.');
    }
    onLoginSuccess({
      username: tokenRes.user.username,
      nombre: tokenRes.user.nombre,
      rol: tokenRes.user.rol,
      taller: tokenRes.user.taller_nombre,
      token: tokenRes.access_token,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (cambioPendiente) {
      if (passwordNueva.length < 12) {
        setError('La contraseña nueva debe tener al menos 12 caracteres.');
        return;
      }
      if (passwordNueva !== passwordConfirmacion) {
        setError('Las contraseñas nuevas no coinciden.');
        return;
      }
      setLoading(true);
      try {
        const cambio = await apiService.cambiarPassword(
          cambioPendiente.access_token,
          password,
          passwordNueva,
        );
        completarSesion({
          ...cambioPendiente,
          access_token: cambio.access_token,
          user: cambioPendiente.user
            ? { ...cambioPendiente.user, requiere_cambio_password: false }
            : undefined,
        });
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'No se pudo cambiar la contraseña.');
      } finally {
        setLoading(false);
      }
      return;
    }

    if (!username || !password) {
      setError('Por favor complete todos los campos.');
      return;
    }

    setLoading(true);

    try {
      const tokenRes = await apiService.login({ username, password });
      if (!tokenRes.user) {
        throw new Error('El servidor no devolvió la información del usuario.');
      }
      if (tokenRes.user.requiere_cambio_password) {
        setCambioPendiente(tokenRes);
      } else {
        completarSesion(tokenRes);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error de autenticación con FastAPI / PostgreSQL.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg-main)',
        padding: '20px',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '420px',
          backgroundColor: '#ffffff',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-color)',
          boxShadow: 'var(--shadow-lg)',
          padding: '32px 28px',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px',
        }}
        className="animate-fade-in"
      >
        {/* Header logo */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '8px' }}>
          <div
            style={{
              width: '54px',
              height: '54px',
              borderRadius: '14px',
              backgroundColor: 'var(--primary)',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: 'var(--shadow-md)',
            }}
          >
            <Wrench size={28} />
          </div>
          <h2 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-main)' }}>
            Panel de Diagnóstico Taller
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            CarBot — Sistema de Tesis ML + RAG + LLM (Carabayllo 2026)
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {error && (
            <div
              style={{
                padding: '10px 14px',
                borderRadius: '8px',
                backgroundColor: 'var(--status-danger-bg)',
                color: 'var(--status-danger-text)',
                fontSize: '13px',
                fontWeight: 500,
              }}
            >
              {error}
            </div>
          )}

          {!cambioPendiente ? (
            <>
              <Input
                label="Usuario o Teléfono"
                placeholder="Ej. administrador o teléfono"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                icon={<User size={18} />}
              />

              <Input
                label="Contraseña de Acceso"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                icon={<Lock size={18} />}
              />
            </>
          ) : (
            <>
              <div style={{ padding: '10px 14px', borderRadius: '8px', backgroundColor: '#fff7ed', color: '#9a3412', fontSize: '13px' }}>
                Por seguridad, debes crear una contraseña personal antes de ingresar.
              </div>
              <Input
                label="Nueva contraseña (mínimo 12 caracteres)"
                type="password"
                value={passwordNueva}
                onChange={(e) => setPasswordNueva(e.target.value)}
                icon={<Lock size={18} />}
              />
              <Input
                label="Confirmar nueva contraseña"
                type="password"
                value={passwordConfirmacion}
                onChange={(e) => setPasswordConfirmacion(e.target.value)}
                icon={<Lock size={18} />}
              />
            </>
          )}

          <Button type="submit" variant="primary" size="lg" style={{ marginTop: '8px' }} disabled={loading}>
            {loading
              ? 'Procesando...'
              : cambioPendiente
                ? 'Guardar contraseña e ingresar'
                : 'Ingresar al Sistema'}
          </Button>
        </form>
      </div>
    </div>
  );
};
