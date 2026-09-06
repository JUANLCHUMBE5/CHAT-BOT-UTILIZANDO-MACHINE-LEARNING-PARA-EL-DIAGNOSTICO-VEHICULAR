import React from 'react';
import { Calendar, Car, MessageSquare, Phone, User } from 'lucide-react';
import { Badge } from '../../../common/Badge';
import type { Diagnostico } from '../../../../types';

interface DiagnosticoMetaHeaderProps {
  diagnostico: Diagnostico;
}

export const DiagnosticoMetaHeader: React.FC<DiagnosticoMetaHeaderProps> = ({
  diagnostico,
}) => {
  const tienePlaca =
    diagnostico.placa_vehiculo &&
    diagnostico.placa_vehiculo.trim() !== '' &&
    !diagnostico.placa_vehiculo.toLowerCase().includes('sin placa');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {/* 1. Header Meta Card: Resumen Limpio */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          padding: '12px 14px',
          backgroundColor: '#f8fafc',
          borderRadius: '10px',
          border: '1px solid var(--border-color)',
          gap: '12px',
          alignItems: 'center',
        }}
      >
        {/* Solicitante */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)', fontSize: '11px', fontWeight: 600, marginBottom: '2px' }}>
            <User size={13} style={{ color: '#2563eb' }} />
            <span>Solicitante</span>
          </div>
          <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)' }}>
            {diagnostico.mecanico_nombre || diagnostico.cliente_nombre || 'Contacto'}
          </div>
          {diagnostico.cliente_telefono && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
              <Phone size={10} />
              <span>{diagnostico.cliente_telefono}</span>
            </div>
          )}
        </div>

        {/* Vehículo */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)', fontSize: '11px', fontWeight: 600, marginBottom: '2px' }}>
            <Car size={13} style={{ color: tienePlaca ? 'var(--primary)' : 'var(--text-muted)' }} />
            <span>Vehículo</span>
          </div>
          <div style={{ fontSize: '13px', fontWeight: 700, color: tienePlaca ? 'var(--primary)' : 'var(--text-muted)' }}>
            {tienePlaca ? diagnostico.placa_vehiculo : 'Sin Placa'}
          </div>
          {diagnostico.marca_modelo && !diagnostico.marca_modelo.toLowerCase().includes('no registrado') && (
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
              {diagnostico.marca_modelo}
            </div>
          )}
        </div>

        {/* Fecha y Estado */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)', fontSize: '11px', fontWeight: 600, marginBottom: '2px' }}>
            <Calendar size={13} />
            <span>Fecha y Estado</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
            <Badge type={diagnostico.estado} />
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '3px' }}>
            {diagnostico.fecha_hora}
          </div>
        </div>
      </div>

      {/* 2. Mensaje Recibido por WhatsApp */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: '10px',
          backgroundColor: '#f0fdf4',
          border: '1px solid #bbf7d0',
          borderRadius: '10px',
          padding: '12px 14px',
        }}
      >
        <div
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            backgroundColor: '#22c55e',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            marginTop: '2px',
          }}
        >
          <MessageSquare size={14} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#166534', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Mensaje Recibido (WhatsApp)
            </span>
          </div>
          <p style={{ margin: 0, fontSize: '13px', fontWeight: 500, color: '#14532d', lineHeight: 1.45 }}>
            "{diagnostico.sintoma_original}"
          </p>
        </div>
      </div>
    </div>
  );
};
