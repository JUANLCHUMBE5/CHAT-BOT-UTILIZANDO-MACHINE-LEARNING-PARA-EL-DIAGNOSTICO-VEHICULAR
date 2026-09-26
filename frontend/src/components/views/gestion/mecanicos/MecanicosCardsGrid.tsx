import React, { useState } from 'react';
import {
  FileSearch,
  Lock,
  Unlock,
  UserX,
  Wrench,
  MoreVertical,
} from 'lucide-react';
import { Card } from '../../../common/Card';
import { enmascararIdentificadorSensible } from '../../../../services/api';
import { calcularVigenciaMecanico } from '../../../../utils/vigenciaMecanico';
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
  const [menuAbiertoId, setMenuAbiertoId] = useState<string | null>(null);

  const formatearFecha = (fechaStr?: string) => {
    if (!fechaStr) return 'N/A';
    try {
      const d = new Date(fechaStr);
      return !isNaN(d.getTime())
        ? d.toLocaleDateString('es-PE', { day: '2-digit', month: '2-digit', year: 'numeric' })
        : fechaStr;
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
          No se encontraron mecánicos
        </h4>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: 0 }}>
          {busqueda
            ? 'No hay resultados que coincidan con la búsqueda o filtro seleccionado.'
            : 'Las solicitudes aprobadas desde WhatsApp aparecerán automáticamente aquí.'}
        </p>
      </Card>
    );
  }

  return (
    <div className="mecanicos-grid-container">
      {mecanicosFiltrados.map((m) => {
        const vigencia = calcularVigenciaMecanico(m);
        const estaBloqueado = m.bloqueado;
        const telefonoSeguro = enmascararIdentificadorSensible(m.telefono, 'telefono') || m.telefono;
        const esMenuAbierto = menuAbiertoId === m.id;

        return (
          <Card
            key={m.id}
            style={{
              padding: '12px 14px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '10px',
              borderRadius: '10px',
              border: '1px solid var(--border-color)',
              backgroundColor: estaBloqueado ? 'rgba(239, 68, 68, 0.02)' : '#ffffff',
              boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
              position: 'relative',
            }}
          >
            {/* Header de Card: Nombre y Badge de Vigencia */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', marginBottom: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', minWidth: 0 }}>
                  <Wrench size={14} style={{ color: estaBloqueado ? '#ef4444' : 'var(--primary)', flexShrink: 0 }} />
                  <h4
                    style={{
                      fontSize: '14px',
                      fontWeight: 700,
                      color: 'var(--text-main)',
                      margin: 0,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                    title={m.nombres}
                  >
                    {m.nombres}
                  </h4>
                </div>

                <span
                  style={{
                    padding: '2px 8px',
                    borderRadius: '10px',
                    fontSize: '10px',
                    fontWeight: 800,
                    backgroundColor: vigencia.badgeStyle.bg,
                    color: vigencia.badgeStyle.color,
                    border: `1px solid ${vigencia.badgeStyle.border}`,
                    textTransform: 'uppercase',
                    letterSpacing: '0.03em',
                    flexShrink: 0,
                  }}
                >
                  {vigencia.etiquetaEstado}
                </span>
              </div>

              {/* Teléfono y Total Diagnósticos */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                <span>📱 {telefonoSeguro}</span>
                <span style={{ fontWeight: 700, color: 'var(--text-main)', backgroundColor: '#f1f5f9', padding: '1px 6px', borderRadius: '4px', fontSize: '11px' }}>
                  {m.total_diagnosticos || 0} diagnósticos
                </span>
              </div>

              {/* Fechas: Vigencia y Registro */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', fontSize: '11px', color: 'var(--text-muted)', backgroundColor: '#f8fafc', padding: '6px 8px', borderRadius: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Acceso hasta:</span>
                  <strong style={{ color: vigencia.estadoVisual === 'vencido' ? '#b45309' : 'var(--text-main)' }}>
                    {vigencia.fechaExpiracionStr}
                  </strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10.5px' }}>
                  <span>Registro: {formatearFecha(m.fecha_registro)}</span>
                  <span>Actividad: {formatearFecha(m.ultimo_acceso)}</span>
                </div>
              </div>
            </div>

            {/* Barra de Acciones: [Ver actividad] + Menú Contextual [⋮] */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', paddingTop: '8px', borderTop: '1px solid #f1f5f9', position: 'relative' }}>
              {onVerConsultasMecanico && (
                <button
                  type="button"
                  onClick={() => onVerConsultasMecanico(m.id)}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '4px',
                    padding: '6px 10px',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color)',
                    backgroundColor: '#ffffff',
                    color: 'var(--primary)',
                    fontSize: '11.5px',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  <FileSearch size={13} />
                  <span>Ver actividad</span>
                </button>
              )}

              {/* Botón de Menú Contextual / Acciones Secundarias */}
              <button
                type="button"
                onClick={() => setMenuAbiertoId(esMenuAbierto ? null : m.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '30px',
                  height: '30px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-color)',
                  backgroundColor: esMenuAbierto ? '#f1f5f9' : '#ffffff',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                }}
                title="Más opciones"
              >
                <MoreVertical size={14} />
              </button>

              {/* Desplegable del Menú Contextual */}
              {esMenuAbierto && (
                <div
                  style={{
                    position: 'absolute',
                    right: 0,
                    bottom: '36px',
                    backgroundColor: '#ffffff',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
                    zIndex: 20,
                    minWidth: '150px',
                    padding: '4px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '2px',
                  }}
                >
                  <button
                    type="button"
                    onClick={() => {
                      setMenuAbiertoId(null);
                      onConfirmBloquear(m, !estaBloqueado);
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '7px 10px',
                      border: 'none',
                      backgroundColor: 'transparent',
                      color: estaBloqueado ? '#059669' : '#d97706',
                      fontSize: '11.5px',
                      fontWeight: 600,
                      borderRadius: '4px',
                      cursor: 'pointer',
                      textAlign: 'left',
                      width: '100%',
                    }}
                  >
                    {estaBloqueado ? <Unlock size={13} /> : <Lock size={13} />}
                    <span>{estaBloqueado ? 'Desbloquear' : 'Bloquear'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setMenuAbiertoId(null);
                      onConfirmRevocar(m);
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '7px 10px',
                      border: 'none',
                      backgroundColor: 'transparent',
                      color: '#dc2626',
                      fontSize: '11.5px',
                      fontWeight: 600,
                      borderRadius: '4px',
                      cursor: 'pointer',
                      textAlign: 'left',
                      width: '100%',
                    }}
                  >
                    <UserX size={13} />
                    <span>Revocar acceso</span>
                  </button>
                </div>
              )}
            </div>
          </Card>
        );
      })}
    </div>
  );
};
