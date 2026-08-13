import React from 'react';
import { Menu, Wrench, User, LogOut } from 'lucide-react';
import type { UsuarioSesion } from '../../types';

interface HeaderProps {
  user: UsuarioSesion | null;
  onLogout: () => void;
  onToggleMobileSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  user,
  onLogout,
  onToggleMobileSidebar,
}) => {
  return (
    <header
      style={{
        height: '64px',
        backgroundColor: '#ffffff',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 20px',
        position: 'sticky',
        top: 0,
        zIndex: 30,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Toggle Menu Button (Always visible on PC and Mobile) */}
        <button
          onClick={onToggleMobileSidebar}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'var(--bg-subtle)',
            border: '1px solid var(--border-color)',
            cursor: 'pointer',
            padding: '6px',
            borderRadius: '6px',
            color: 'var(--text-secondary)',
          }}
          title="Abrir / Cerrar Menú Lateral"
        >
          <Menu size={20} />
        </button>

        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '8px',
              backgroundColor: 'var(--primary)',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '18px',
            }}
          >
            <Wrench size={18} />
          </div>
          <div>
            <h1 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)', lineHeight: 1.2 }}>
              CarBot <span style={{ color: 'var(--primary)', fontWeight: 500, fontSize: '13px' }}>Carabayllo</span>
            </h1>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }} className="desktop-only">
              Sistema de Diagnóstico Vehicular ML+RAG
            </span>
          </div>
        </div>
      </div>

      {/* User profile & actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {user && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              paddingLeft: '12px',
              borderLeft: '1px solid var(--border-color)',
            }}
          >
            <div
              style={{
                width: '34px',
                height: '34px',
                borderRadius: '50%',
                backgroundColor: 'var(--primary-light)',
                border: '1px solid var(--primary-border)',
                color: 'var(--primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 600,
                fontSize: '14px',
              }}
            >
              <User size={18} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }} className="desktop-only">
              <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>
                {user.nombre}
              </span>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                {user.rol.replace('_', ' ')}
              </span>
            </div>

            <button
              onClick={onLogout}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 10px',
                fontSize: '12px',
                fontWeight: 500,
                color: '#be123c',
                backgroundColor: '#ffe4e6',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
              }}
              title="Cerrar Sesión"
            >
              <LogOut size={14} />
              <span className="desktop-only">Salir</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
