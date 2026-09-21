import React, { useState, useEffect } from 'react';
import {
  GraduationCap,
  Cpu,
} from 'lucide-react';
import { ModeloIATab } from './proyecto/ModeloIATab';
import { TesisValidacionTab } from './proyecto/TesisValidacionTab';

export type ProyectoSubTab = 'modelo_ia' | 'tesis';

export interface ProyectoCarbotViewProps {
  initialSubTab?: ProyectoSubTab;
}

export const ProyectoCarbotView: React.FC<ProyectoCarbotViewProps> = ({
  initialSubTab = 'tesis',
}) => {
  const [subTab, setSubTab] = useState<ProyectoSubTab>(initialSubTab);

  useEffect(() => {
    if (initialSubTab) {
      setSubTab(initialSubTab);
    }
  }, [initialSubTab]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* 2-Tab Segmented Control */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          backgroundColor: '#f1f5f9',
          padding: '3px',
          borderRadius: '9px',
          gap: '4px',
        }}
      >
        <button
          type="button"
          onClick={() => setSubTab('modelo_ia')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            padding: '8px 6px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: 700,
            border: 'none',
            backgroundColor: subTab === 'modelo_ia' ? '#7c3aed' : 'transparent',
            color: subTab === 'modelo_ia' ? '#ffffff' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: subTab === 'modelo_ia' ? '0 1px 3px rgba(124,58,237,0.2)' : 'none',
            whiteSpace: 'nowrap',
          }}
        >
          <Cpu size={15} />
          <span>Modelo de IA</span>
        </button>

        <button
          type="button"
          onClick={() => setSubTab('tesis')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            padding: '8px 6px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: 700,
            border: 'none',
            backgroundColor: subTab === 'tesis' ? '#059669' : 'transparent',
            color: subTab === 'tesis' ? '#ffffff' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: subTab === 'tesis' ? '0 1px 3px rgba(5,150,105,0.2)' : 'none',
            whiteSpace: 'nowrap',
          }}
        >
          <GraduationCap size={15} />
          <span>Tesis y Validación</span>
        </button>
      </div>

      {/* Active Sub-tab View */}
      {subTab === 'modelo_ia' && <ModeloIATab />}
      {subTab === 'tesis' && <TesisValidacionTab />}
    </div>
  );
};
