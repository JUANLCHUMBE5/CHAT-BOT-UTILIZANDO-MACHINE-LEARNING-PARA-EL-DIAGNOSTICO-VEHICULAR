import React from 'react';
import {
  Calendar,
  FileSearch,
  Lock,
  Unlock,
  UserX,
  Wrench,
} from 'lucide-react';
import { Card } from '../../../common/Card';
import { enmascararIdentificadorSensible } from '../../../../services/api';
import type { Mecanico } from '../../../../types';

interface MecanicosCardsGridProps {
  mecanicosFiltrados: Mecanico[];
  cargando: boolean;
  busqueda: string;
  onVerConsultasMecanico?: (id: string) => void;
  onConfirmBloquear: (m: Mecanico, estaBloqueando: boolean) => void;
  onConfirmRevocar: (m: Mecanico) => void;
}

export const MecanicosCardsGrid: React.FC<MecanicosCardsGridProps> = ({
  mecanicosFiltrados,
  cargando,
  busqueda,
  onVerConsultasMecanico,
  onConfirmBloquear,
  onConfirmRevocar,
}) => {
  const formatearFecha = (fechaStr?: string) => {
    if (!fechaStr) return 'N/A';
    try {
      const d = new Date(fechaStr);
      return d.toLocaleDateString('es-PE', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      });
    } catch {
      return fechaStr;
    }
  };

  if (cargando && mecanicosFiltrados.length === 0) {
    return (
      <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
        Cargando lista de mecánicos autorizados...
      </div>
    );
  }

  if (mecanicosFiltrados.length === 0) {
    return (
      <Card style={{ padding: '40px 20px', textAlign: 'center' }}>
        <Wrench size={32} style={{ margin: '0 auto 10px auto', color: 'var(--text-muted)', opacity: 0.6 }} />
        <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', margin: '0 0 4px 0' }}>
          No se encontraron mecánicos autorizados
        </h4>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0 }}>
          {busqueda
            ? 'No hay resultados que coincidan con la búsqueda.'
            : 'Las solicitudes aprobadas desde WhatsApp aparecerán automáticamente aquí.'}
        </p>
      </Card>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
      {mecanicosFiltrados.map((m) => {
        const estaBloqueado = m.bloqueado;
        const telefonoSeguro = enmascararIdentificadorSensible(m.telefono, 'telefono') || m.telefono;

        return (
          <Card
            key={m.id}
            style={{
              padding: '8px 12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              backgroundColor: estaBloqueado ? 'rgba(239, 68, 68, 0.02)' : '#ffffff',
            }}
          >
            {/* Top row: Name, Badge, Phone, Diagnostics */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', minWidth: 0 }}>
                <Wrench size={13} style={{ color: estaBloqueado ? '#ef4444' : 'var(--primary)', flexShrink: 0 }} />
                <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
                  {m.nombres}
                </h4>
                <span
                  style={{
                    padding: '1px 5px',
                    borderRadius: '6px',
                    fontSize: '9px',
                    fontWeight: 700,
                    backgroundColor: estaBloqueado ? '#fee2e2' : '#dcfce7',
                    color: estaBloqueado ? '#b91c1c' : '#15803d',
                    textTransform: 'uppercase',
                  }}
                >
                  {estaBloqueado ? 'Bloqueado' : 'Activo'}
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 600 }}>
                  📱 {telefonoSeguro}
                </span>
              </div>

              {/* Compact Diagnostics Pill */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '3px',
                  padding: '2px 6px',
                  backgroundColor: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '5px',
                  fontSize: '10px',
                  fontWeight: 700,
                  color: 'var(--text-main)',
                  flexShrink: 0,
                }}
              >
                <span>{m.total_diagnosticos || 0}</span>
                <span style={{ fontSize: '9px', color: 'var(--text-muted)', fontWeight: 500 }}>diag.</span>
              </div>
            </div>

            {/* Bottom row: Dates and Action Buttons inline */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '8px',
                flexWrap: 'wrap',
                fontSize: '10.5px',
                color: 'var(--text-muted)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                  <Calendar size={10} />
                  Reg: {formatearFecha(m.fecha_registro)}
                </span>
                <span>•</span>
                <span>Acceso: {formatearFecha(m.ultimo_acceso)}</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                {onVerConsultasMecanico && (
                  <button
                    type="button"
                    onClick={() => onVerConsultasMecanico(m.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '3px',
                      padding: '3px 7px',
                      borderRadius: '4px',
                      border: '1px solid var(--border-color)',
                      backgroundColor: '#ffffff',
                      color: 'var(--text-secondary)',
                      fontSize: '10.5px',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    <FileSearch size={11} />
                    <span>Consultas</span>
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => onConfirmBloquear(m, !estaBloqueado)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '3px',
                    padding: '3px 7px',
                    borderRadius: '4px',
                    border: '1px solid var(--border-color)',
                    backgroundColor: '#ffffff',
                    color: estaBloqueado ? '#059669' : '#d97706',
                    fontSize: '10.5px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  {estaBloqueado ? <Unlock size={11} /> : <Lock size={11} />}
                  <span>{estaBloqueado ? 'Desbloquear' : 'Bloquear'}</span>
                </button>

                <button
                  type="button"
                  onClick={() => onConfirmRevocar(m)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '3px',
                    padding: '3px 7px',
                    borderRadius: '4px',
                    border: '1px solid #fecaca',
                    backgroundColor: '#fff5f5',
                    color: '#dc2626',
                    fontSize: '10.5px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  <UserX size={11} />
                  <span>Revocar</span>
                </button>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
};
