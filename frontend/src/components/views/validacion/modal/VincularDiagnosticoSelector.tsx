import React, { useState, useEffect } from 'react';
import { Search, Bot, Check, X, RefreshCw } from 'lucide-react';
import { apiService } from '../../../../services/api';
import type { Diagnostico } from '../../../../types';

interface VincularDiagnosticoSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectDiagnostico: (diag: Diagnostico) => void;
}

export const VincularDiagnosticoSelector: React.FC<VincularDiagnosticoSelectorProps> = ({
  isOpen,
  onClose,
  onSelectDiagnostico,
}) => {
  const [diagnosticos, setDiagnosticos] = useState<Diagnostico[]>([]);
  const [cargando, setCargando] = useState(false);
  const [busqueda, setBusqueda] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    let activo = true;
    setCargando(true);
    setError(null);
    apiService
      .getDiagnosticos({ limite: 25 })
      .then((res: { items: Diagnostico[]; total: number }) => {
        if (activo) {
          setDiagnosticos(res.items || []);
        }
      })
      .catch((err: unknown) => {
        if (activo) setError(err instanceof Error ? err.message : 'Error al cargar diagnósticos');
      })
      .finally(() => {
        if (activo) setCargando(false);
      });
    return () => {
      activo = false;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const filtrados = diagnosticos.filter((d) => {
    if (!busqueda.trim()) return true;
    const term = busqueda.toLowerCase();
    return (
      (d.sintoma_original || '').toLowerCase().includes(term) ||
      (d.falla_predicha || '').toLowerCase().includes(term) ||
      (d.placa_vehiculo || '').toLowerCase().includes(term) ||
      (d.id || '').toLowerCase().includes(term)
    );
  });

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '16px',
      }}
    >
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          width: '100%',
          maxWidth: '620px',
          maxHeight: '85vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '14px 18px',
            borderBottom: '1px solid #e2e8f0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: '#f8fafc',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Bot size={18} style={{ color: '#2563eb' }} />
            <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>
              Vincular Diagnóstico Real de CarBot
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#64748b' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Buscador */}
        <div style={{ padding: '12px 18px', borderBottom: '1px solid #f1f5f9' }}>
          <div style={{ position: 'relative' }}>
            <Search
              size={15}
              style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }}
            />
            <input
              type="text"
              placeholder="Buscar por placa, síntoma o falla predicha..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              style={{
                width: '100%',
                padding: '7px 10px 7px 32px',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                fontSize: '12.5px',
                boxSizing: 'border-box',
              }}
            />
          </div>
        </div>

        {/* Lista de Diagnósticos */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px 18px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {cargando ? (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '40px', gap: '8px', color: '#64748b' }}>
              <RefreshCw size={18} className="animate-spin" />
              <span>Cargando consultas de CarBot...</span>
            </div>
          ) : error ? (
            <div style={{ padding: '16px', color: '#dc2626', fontSize: '12.5px', textAlign: 'center' }}>
              {error}
            </div>
          ) : filtrados.length === 0 ? (
            <div style={{ padding: '30px', textAlign: 'center', color: '#64748b', fontSize: '12.5px' }}>
              No se encontraron diagnósticos disponibles en el taller.
            </div>
          ) : (
            filtrados.map((d) => (
              <div
                key={d.id}
                style={{
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: '12px',
                  backgroundColor: '#ffffff',
                  transition: 'background-color 0.15s',
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ fontSize: '11px', fontWeight: 800, color: '#1d4ed8', backgroundColor: '#eff6ff', padding: '2px 6px', borderRadius: '4px' }}>
                      {d.placa_vehiculo || 'Sin placa'}
                    </span>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>
                      {d.fecha_hora ? new Date(d.fecha_hora).toLocaleDateString() : 'Reciente'}
                    </span>
                    <span style={{ fontSize: '11px', fontWeight: 700, color: '#059669', backgroundColor: '#ecfdf5', padding: '1px 5px', borderRadius: '4px' }}>
                      {d.confianza}% confianza
                    </span>
                  </div>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#1e293b', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {d.falla_predicha || 'Sin predicción'}
                  </div>
                  <div style={{ fontSize: '11.5px', color: '#64748b', marginTop: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    Síntoma: {d.sintoma_original}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    onSelectDiagnostico(d);
                    onClose();
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '6px 12px',
                    backgroundColor: '#2563eb',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    flexShrink: 0,
                  }}
                >
                  <Check size={14} />
                  <span>Vincular</span>
                </button>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: '10px 18px', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'flex-end', backgroundColor: '#f8fafc' }}>
          <button
            type="button"
            onClick={onClose}
            style={{
              padding: '6px 14px',
              backgroundColor: '#e2e8f0',
              color: '#334155',
              border: 'none',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};
