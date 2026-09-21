import React, { useState } from 'react';
import { Wrench, Lock, User, Eye, EyeOff, ShieldCheck } from 'lucide-react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { authApi } from '../../features/auth/api';
import type { UsuarioSesion } from '../../types';
import type { TokenResponseDTO } from '../../types';

interface LoginViewProps {
  onLoginSuccess: (user: UsuarioSesion) => void;
}

export const LoginView: React.FC<LoginViewProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [mostrarPassword, setMostrarPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [cambioPendiente, setCambioPendiente] = useState<TokenResponseDTO | null>(null);
  const [passwordNueva, setPasswordNueva] = useState('');
  const [passwordConfirmacion, setPasswordConfirmacion] = useState('');

  const completarSesion = (tokenRes: TokenResponseDTO) => {
    if (!tokenRes.user) {
      throw new Error('El servidor no devolvió la información del usuario.');
    }
    if (!['administrador', 'admin'].includes(tokenRes.user.rol)) {
      throw new Error('El panel web es exclusivo para administradores. Los mecánicos usan WhatsApp.');
    }
    authApi.establecerAccessToken(tokenRes.access_token);
    onLoginSuccess({
      id: tokenRes.user.id || tokenRes.user.usuario_id,
      username: tokenRes.user.username,
      nombre: tokenRes.user.nombre,
      rol: tokenRes.user.rol,
      taller: tokenRes.user.taller_nombre,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (cambioPendiente) {
      if (
        passwordNueva.length < 12 ||
        !/[a-z]/.test(passwordNueva) ||
        !/[A-Z]/.test(passwordNueva) ||
        !/\d/.test(passwordNueva)
      ) {
        setError('La contraseña nueva debe tener al menos 12 caracteres e incluir mayúsculas, minúsculas y números.');
        return;
      }
      if (passwordNueva === password) {
        setError('La contraseña nueva debe ser diferente de la contraseña temporal actual.');
        return;
      }
      if (passwordNueva !== passwordConfirmacion) {
        setError('Las contraseñas nuevas no coinciden.');
        return;
      }
      setLoading(true);
      try {
        const cambio = await authApi.cambiarPassword(
          cambioPendiente.access_token,
          password,
          passwordNueva,
        );
        completarSesion({
          ...cambioPendiente,
          access_token: cambio.access_token,
          refresh_token: cambio.refresh_token,
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
      setError('Por favor complete su usuario o teléfono y su contraseña.');
      return;
    }

    setLoading(true);

    try {
      const tokenRes = await authApi.login({ username, password });
      if (!tokenRes.user) {
        throw new Error('El servidor no devolvió la información del usuario.');
      }
      if (tokenRes.user.requiere_cambio_password) {
        setCambioPendiente(tokenRes);
      } else {
        completarSesion(tokenRes);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Credenciales inválidas o cuenta no registrada.');
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
        backgroundImage: 'linear-gradient(rgba(15, 23, 42, 0.65), rgba(15, 23, 42, 0.75)), url(/taller_fondo.jpg)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        padding: '20px',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '440px',
          backgroundColor: 'rgba(255, 255, 255, 0.96)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          borderRadius: '16px',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.35)',
          padding: '36px 32px',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px',
          position: 'relative',
          overflow: 'hidden',
        }}
        className="animate-fade-in"
      >
        {/* Header Logo & Welcome text */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '10px' }}>
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '16px',
              backgroundColor: 'var(--primary)',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(234, 88, 12, 0.3)',
            }}
          >
            <Wrench size={28} />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 600,
                color: 'var(--primary)',
                backgroundColor: 'var(--primary-light)',
                padding: '2px 8px',
                borderRadius: '12px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <ShieldCheck size={12} /> Taller Autorizado Carabayllo
            </span>
          </div>

          <h2 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em', marginTop: '2px', marginBottom: '4px' }}>
            CarBot <span style={{ color: 'var(--primary)' }}>Carabayllo</span>
          </h2>
        </div>

        {/* Form Container */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {error && (
            <div
              style={{
                padding: '12px 14px',
                borderRadius: '8px',
                backgroundColor: 'var(--status-danger-bg)',
                color: 'var(--status-danger-text)',
                fontSize: '13px',
                fontWeight: 500,
                lineHeight: 1.4,
              }}
            >
              ⚠️ {error}
            </div>
          )}

          {!cambioPendiente ? (
            <>
              <Input
                label="Usuario administrador"
                placeholder="Ej. administrador"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                icon={<User size={18} />}
                required
              />

              <div style={{ position: 'relative', display: 'flex', flexDirection: 'column' }}>
                <Input
                  label="Contraseña de Acceso"
                  type={mostrarPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  icon={<Lock size={18} />}
                  required
                />
                <button
                  type="button"
                  onClick={() => setMostrarPassword(!mostrarPassword)}
                  style={{
                    position: 'absolute',
                    right: '12px',
                    top: '38px',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: 'var(--text-muted)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '2px',
                  }}
                  title={mostrarPassword ? 'Ocultar contraseña' : 'Ver contraseña'}
                >
                  {mostrarPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </>
          ) : (
            <>
              <div style={{ padding: '12px 14px', borderRadius: '8px', backgroundColor: '#fff7ed', color: '#9a3412', fontSize: '13px', lineHeight: 1.4 }}>
                Por seguridad, debes establecer una contraseña personal antes de ingresar al sistema.
              </div>
              <Input
                label="Nueva Contraseña (mínimo 12 caracteres)"
                type="password"
                placeholder="••••••••••••"
                value={passwordNueva}
                onChange={(e) => setPasswordNueva(e.target.value)}
                icon={<Lock size={18} />}
                required
              />
              <Input
                label="Confirmar Nueva Contraseña"
                type="password"
                placeholder="••••••••••••"
                value={passwordConfirmacion}
                onChange={(e) => setPasswordConfirmacion(e.target.value)}
                icon={<Lock size={18} />}
                required
              />
            </>
          )}

          <Button type="submit" variant="primary" size="lg" style={{ marginTop: '10px', height: '44px', fontWeight: 600 }} disabled={loading}>
            {loading
              ? 'Verificando datos...'
              : cambioPendiente
                ? 'Guardar contraseña e ingresar'
                : 'Ingresar al Sistema'}
          </Button>
        </form>
      </div>
    </div>
  );
};
