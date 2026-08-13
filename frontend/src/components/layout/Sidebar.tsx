import React from 'react';
import { LayoutDashboard, Users, UserCheck, FileSearch, ShieldCheck, X } from 'lucide-react';

export type NavTab = 'resumen' | 'mecanicos' | 'clientes' | 'diagnosticos';

interface SidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  isMobileOpen: boolean;
  onCloseMobile: () => void;
  isDesktopCollapsed?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  isMobileOpen,
  onCloseMobile,
  isDesktopCollapsed = false,
}) => {
  const navItems: { id: NavTab; label: string; icon: React.ReactNode; badge?: string }[] = [
    { id: 'resumen', label: 'Resumen Geral', icon: <LayoutDashboard size={18} /> },
    { id: 'clientes', label: 'Clientes y Solicitudes', icon: <UserCheck size={18} /> },
    { id: 'mecanicos', label: 'Gestión Mecánicos', icon: <Users size={18} /> },
    { id: 'diagnosticos', label: 'Historial Diagnósticos', icon: <FileSearch size={18} /> },
  ];

  const content = (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        justifyContent: 'space-between',
        padding: '20px 12px',
      }}
    >
      <div>
        <div style={{ marginBottom: '24px', padding: '0 8px' }}>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 700,
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Navegación Principal
          </span>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onSelectTab(item.id);
                  onCloseMobile();
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '14px',
                  fontWeight: isActive ? 600 : 500,
                  color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                  backgroundColor: isActive ? 'var(--primary-light)' : 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s ease',
                  position: 'relative',
                }}
              >
                {isActive && (
                  <div
                    style={{
                      position: 'absolute',
                      left: 0,
                      top: '6px',
                      bottom: '6px',
                      width: '3px',
                      backgroundColor: 'var(--primary)',
                      borderRadius: '0 4px 4px 0',
                    }}
                  />
                )}
                <span>{item.icon}</span>
                <span style={{ flex: 1 }}>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Workshop info widget */}
      <div
        style={{
          padding: '14px',
          backgroundColor: 'var(--bg-subtle)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--primary)' }}>
          <ShieldCheck size={16} />
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-main)' }}>
            Taller Carabayllo
          </span>
        </div>
        <p style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
          Base de Datos RAG: 25 Manuales de Servicio Activos.
        </p>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar (Collapsible) */}
      <aside
        style={{
          width: isDesktopCollapsed ? '0px' : '240px',
          opacity: isDesktopCollapsed ? 0 : 1,
          backgroundColor: '#ffffff',
          borderRight: isDesktopCollapsed ? 'none' : '1px solid var(--border-color)',
          flexShrink: 0,
          overflow: 'hidden',
          transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
        className="desktop-only"
      >
        {content}
      </aside>

      {/* Mobile Drawer Overlay */}
      {isMobileOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 50,
            backgroundColor: 'rgba(15, 23, 42, 0.45)',
            backdropFilter: 'blur(3px)',
          }}
          onClick={onCloseMobile}
        >
          <aside
            style={{
              width: '260px',
              height: '100%',
              backgroundColor: '#ffffff',
              boxShadow: 'var(--shadow-lg)',
              position: 'relative',
            }}
            className="animate-drawer-in"
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '16px 20px',
                borderBottom: '1px solid var(--border-color)',
              }}
            >
              <span style={{ fontWeight: 700, fontSize: '15px', color: 'var(--primary)' }}>
                Menú de Taller
              </span>
              <button
                onClick={onCloseMobile}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
              >
                <X size={20} />
              </button>
            </div>
            {content}
          </aside>
        </div>
      )}
    </>
  );
};
