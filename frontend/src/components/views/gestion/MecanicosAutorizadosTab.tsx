import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  Search,
} from 'lucide-react';
import type { Mecanico } from '../../../types';
import { useMecanicosAutorizados } from '../../../hooks/useMecanicosAutorizados';
import { MecanicosCardsGrid, MecanicosModals } from './mecanicos';

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
  const {
    busqueda,
    setBusqueda,
    filtroEstado,
    setFiltroEstado,
    notificacionError,
    notificacionExito,
    confirmBloquearModal,
    setConfirmBloquearModal,
    procesandoBloquear,
    confirmRevocarModal,
    setConfirmRevocarModal,
    procesandoRevocacion,
    mecanicosFiltrados,
    totalActivos,
    totalBloqueados,
    handleToggleBloquear,
    handleRevocarAcceso,
  } = useMecanicosAutorizados({ mecanicos, onRecargar });

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

      {/* Compact Filter Bar */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '8px',
          backgroundColor: '#ffffff',
          padding: '8px 12px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: '220px' }}>
          <div
            style={{
              position: 'relative',
              flex: 1,
              maxWidth: '320px',
            }}
          >
            <Search
              size={14}
              style={{
                position: 'absolute',
                left: '9px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)',
              }}
            />
            <input
              type="text"
              placeholder="Buscar mecánico o teléfono..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              style={{
                width: '100%',
                padding: '6px 10px 6px 28px',
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
                padding: '5px 8px',
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
                padding: '5px 8px',
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
                  padding: '5px 8px',
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
      </div>

      {/* Grid de Tarjetas de Mecánicos */}
      <MecanicosCardsGrid
        mecanicosFiltrados={mecanicosFiltrados}
        cargando={cargando}
        busqueda={busqueda}
        onVerConsultasMecanico={onVerConsultasMecanico}
        onConfirmBloquear={(m, estaBloqueando) => setConfirmBloquearModal({ mecanico: m, estaBloqueando })}
        onConfirmRevocar={(m) => setConfirmRevocarModal(m)}
      />

      {/* Modales de Confirmación */}
      <MecanicosModals
        confirmBloquearModal={confirmBloquearModal}
        procesandoBloquear={procesandoBloquear}
        onConfirmBloquear={handleToggleBloquear}
        onCloseBloquear={() => setConfirmBloquearModal(null)}
        confirmRevocarModal={confirmRevocarModal}
        procesandoRevocacion={procesandoRevocacion}
        onConfirmRevocar={handleRevocarAcceso}
        onCloseRevocar={() => setConfirmRevocarModal(null)}
      />
    </div>
  );
};
