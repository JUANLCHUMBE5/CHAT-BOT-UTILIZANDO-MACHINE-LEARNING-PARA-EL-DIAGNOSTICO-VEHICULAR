import React from 'react';
import {
  ShieldAlert,
  Power,
  Lock,
  Unlock,
  Pencil,
  Loader2,
} from 'lucide-react';
import type { Mecanico, MecanicoRol } from '../../../../types';
import type { RowGuards } from '../../../../hooks/useEquipoTallerActions';

interface EquipoTallerTableProps {
  mecanicos: Mecanico[];
  cargando: boolean;
  evaluateRowGuards: (m: Mecanico) => RowGuards;
  onAbrirEdicion: (m: Mecanico) => void;
  onConfirmActivar: (data: { mecanico: Mecanico; estaActivando: boolean }) => void;
  onConfirmBloquear: (data: { mecanico: Mecanico; estaBloqueando: boolean }) => void;
  onSeleccionarRol: (m: Mecanico, rol: MecanicoRol) => void;
  onConfirmRevocar: (m: Mecanico) => void;
}

export const EquipoTallerTable: React.FC<EquipoTallerTableProps> = ({
  mecanicos,
  cargando,
  evaluateRowGuards,
  onAbrirEdicion,
  onConfirmActivar,
  onConfirmBloquear,
  onSeleccionarRol,
  onConfirmRevocar,
}) => {
  const getRoleBadgeStyle = (rol: string) => {
    switch (rol) {
      case 'administrador':
      case 'admin':
        return { label: 'Administrador', bg: 'rgba(99, 102, 241, 0.15)', color: '#4338ca' };
      case 'jefe_taller':
      case 'supervisor':
        return { label: 'Jefe de Taller', bg: 'rgba(245, 158, 11, 0.15)', color: '#b45309' };
      default:
        return { label: 'Mecánico', bg: 'rgba(16, 185, 129, 0.15)', color: '#047857' };
    }
  };

  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        borderRadius: '12px',
        border: '1px solid var(--border-color)',
        overflow: 'hidden',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr
              style={{
                backgroundColor: 'var(--bg-subtle)',
                borderBottom: '1px solid var(--border-color)',
                fontSize: '11px',
                fontWeight: 700,
                color: 'var(--text-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              <th style={{ padding: '14px 18px' }}>Nombre y Usuario</th>
              <th style={{ padding: '14px 18px' }}>Teléfono WhatsApp</th>
              <th style={{ padding: '14px 18px' }}>Rol en el Sistema</th>
              <th style={{ padding: '14px 18px' }}>Estado de Cuenta</th>
              <th style={{ padding: '14px 18px', textAlign: 'right' }}>Acciones Administrativas</th>
            </tr>
          </thead>
          <tbody>
            {cargando ? (
              <tr>
                <td colSpan={5} style={{ padding: '48px 18px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                    <Loader2 size={24} className="animate-spin" style={{ color: 'var(--primary)' }} />
                    <span>Cargando equipo del taller...</span>
                  </div>
                </td>
              </tr>
            ) : mecanicos.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ padding: '48px 18px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No se encontró personal registrado en el taller.
                </td>
              </tr>
            ) : (
              mecanicos.map((m) => {
                const guards = evaluateRowGuards(m);
                const roleBadge = getRoleBadgeStyle(m.rol);

                return (
                  <tr
                    key={m.id}
                    className="table-row-hover"
                    style={{
                      borderBottom: '1px solid var(--border-color)',
                      backgroundColor: guards.isSelf ? 'rgba(238, 242, 255, 0.25)' : '#ffffff',
                    }}
                  >
                    {/* Nombre y Usuario */}
                    <td style={{ padding: '14px 18px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '13px' }}>
                            {m.nombres}
                          </span>
                          {guards.isSelf && (
                            <span
                              style={{
                                fontSize: '9px',
                                fontWeight: 700,
                                backgroundColor: '#eef2ff',
                                color: '#4338ca',
                                padding: '1px 6px',
                                borderRadius: '8px',
                                border: '1px solid #c7d2fe',
                              }}
                            >
                              Tú
                            </span>
                          )}
                        </div>
                        {m.username && (
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                            @{m.username}
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Teléfono */}
                    <td style={{ padding: '14px 18px', color: 'var(--text-secondary)' }}>
                      {m.telefono || '—'}
                    </td>

                    {/* Rol */}
                    <td style={{ padding: '14px 18px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            padding: '3px 10px',
                            borderRadius: '12px',
                            fontSize: '11px',
                            fontWeight: 700,
                            backgroundColor: roleBadge.bg,
                            color: roleBadge.color,
                          }}
                        >
                          {roleBadge.label}
                        </span>

                        {/* Role Selector */}
                        <select
                          aria-label={`Cambiar rol para ${m.nombres}`}
                          value={m.rol}
                          onChange={(e) => onSeleccionarRol(m, e.target.value as MecanicoRol)}
                          disabled={!guards.canChangeRole(m.rol === 'mecanico' ? 'administrador' : 'mecanico')}
                          style={{
                            fontSize: '11px',
                            padding: '3px 6px',
                            borderRadius: '6px',
                            border: '1px solid var(--border-color)',
                            backgroundColor: guards.restrictedByHierarchy ? '#f8fafc' : '#ffffff',
                            color: 'var(--text-secondary)',
                            cursor: guards.restrictedByHierarchy ? 'not-allowed' : 'pointer',
                          }}
                        >
                          <option value="mecanico">Mecánico</option>
                          <option value="jefe_taller">Jefe de Taller</option>
                          <option value="administrador">Administrador</option>
                        </select>
                      </div>
                    </td>

                    {/* Estado */}
                    <td style={{ padding: '14px 18px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span
                            style={{
                              width: '7px',
                              height: '7px',
                              borderRadius: '50%',
                              backgroundColor: m.activo ? '#10b981' : '#94a3b8',
                            }}
                          />
                          <span style={{ fontSize: '12px', fontWeight: 600, color: m.activo ? '#047857' : '#64748b' }}>
                            {m.activo ? 'Activo' : 'Inactivo'}
                          </span>
                        </div>
                        {m.bloqueado && (
                          <span
                            style={{
                              fontSize: '10px',
                              fontWeight: 700,
                              color: '#be123c',
                              backgroundColor: '#ffe4e6',
                              padding: '1px 6px',
                              borderRadius: '6px',
                              width: 'fit-content',
                            }}
                          >
                            Bloqueado
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Acciones */}
                    <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '6px' }}>
                        {/* Editar */}
                        <button
                          type="button"
                          onClick={() => onAbrirEdicion(m)}
                          title={guards.editTooltip || 'Editar datos de perfil'}
                          disabled={!guards.canEdit}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            padding: '5px 9px',
                            borderRadius: '6px',
                            fontSize: '11px',
                            fontWeight: 600,
                            border: '1px solid var(--border-color)',
                            backgroundColor: guards.canEdit ? '#ffffff' : '#f8fafc',
                            color: guards.canEdit ? 'var(--text-main)' : 'var(--text-muted)',
                            cursor: guards.canEdit ? 'pointer' : 'not-allowed',
                          }}
                        >
                          <Pencil size={12} />
                          <span>Editar</span>
                        </button>

                        {/* Activar / Desactivar */}
                        <button
                          type="button"
                          onClick={() => onConfirmActivar({ mecanico: m, estaActivando: !m.activo })}
                          title={guards.activeTooltip || (m.activo ? 'Desactivar acceso' : 'Activar acceso')}
                          disabled={!guards.canToggleActive}
                          style={{
                            padding: '5px 8px',
                            borderRadius: '6px',
                            fontSize: '11px',
                            fontWeight: 600,
                            border: '1px solid var(--border-color)',
                            backgroundColor: guards.canToggleActive ? '#ffffff' : '#f8fafc',
                            color: m.activo ? '#d97706' : '#059669',
                            cursor: guards.canToggleActive ? 'pointer' : 'not-allowed',
                          }}
                        >
                          <Power size={13} />
                        </button>

                        {/* Bloquear / Desbloquear */}
                        <button
                          type="button"
                          onClick={() => onConfirmBloquear({ mecanico: m, estaBloqueando: !m.bloqueado })}
                          title={guards.blockTooltip || (m.bloqueado ? 'Desbloquear cuenta' : 'Bloquear cuenta')}
                          disabled={!guards.canToggleBlock}
                          style={{
                            padding: '5px 8px',
                            borderRadius: '6px',
                            fontSize: '11px',
                            fontWeight: 600,
                            border: '1px solid var(--border-color)',
                            backgroundColor: guards.canToggleBlock ? '#ffffff' : '#f8fafc',
                            color: m.bloqueado ? '#059669' : '#e11d48',
                            cursor: guards.canToggleBlock ? 'pointer' : 'not-allowed',
                          }}
                        >
                          {m.bloqueado ? <Unlock size={13} /> : <Lock size={13} />}
                        </button>

                        {/* Revocar */}
                        <button
                          type="button"
                          onClick={() => onConfirmRevocar(m)}
                          title={guards.revokeTooltip || 'Revocar acceso'}
                          disabled={!guards.canRevoke}
                          style={{
                            padding: '5px 8px',
                            borderRadius: '6px',
                            fontSize: '11px',
                            fontWeight: 600,
                            border: '1px solid var(--border-color)',
                            backgroundColor: guards.canRevoke ? '#ffffff' : '#f8fafc',
                            color: guards.canRevoke ? '#be123c' : 'var(--text-muted)',
                            cursor: guards.canRevoke ? 'pointer' : 'not-allowed',
                          }}
                        >
                          <ShieldAlert size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
