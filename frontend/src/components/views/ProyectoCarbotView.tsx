import React, { useState, useEffect } from 'react';
import {
  Brain,
  GraduationCap,
  HelpCircle,
  Cpu,
} from 'lucide-react';
import { ComoFuncionaTab } from './proyecto/ComoFuncionaTab';
import { ModeloIATab } from './proyecto/ModeloIATab';
import { TesisValidacionTab } from './proyecto/TesisValidacionTab';

export type ProyectoSubTab = 'como_funciona' | 'modelo_ia' | 'tesis';

export interface ProyectoCarbotViewProps {
  initialSubTab?: ProyectoSubTab;
}

export const ProyectoCarbotView: React.FC<ProyectoCarbotViewProps> = ({
  initialSubTab = 'como_funciona',
}) => {
  const [subTab, setSubTab] = useState<ProyectoSubTab>(initialSubTab);

  useEffect(() => {
    if (initialSubTab) {
      setSubTab(initialSubTab);
    }
  }, [initialSubTab]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Brain size={22} style={{ color: '#7c3aed' }} />
          <h1 style={{ fontSize: '19px', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
            Proyecto CarBot AI — Arquitectura, Modelo & Tesis
          </h1>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '3px 0 0 0' }}>
          Documentación técnica del pipeline híbrido, benchmark experimental de algoritmos y sustento de investigación UCV 2026.
        </p>
      </div>

      {/* 3-Tab Segmented Control */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
          backgroundColor: '#f1f5f9',
          padding: '4px',
          borderRadius: '10px',
          gap: '4px',
        }}
      >
        <button
          type="button"
          onClick={() => setSubTab('como_funciona')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '8px 12px',
            borderRadius: '7px',
            fontSize: '12px',
            fontWeight: 700,
            border: 'none',
            backgroundColor: subTab === 'como_funciona' ? '#ffffff' : 'transparent',
            color: subTab === 'como_funciona' ? 'var(--primary)' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: subTab === 'como_funciona' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
          }}
        >
          <HelpCircle size={15} />
          <span>Cómo Funciona</span>
        </button>

        <button
          type="button"
          onClick={() => setSubTab('modelo_ia')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '8px 12px',
            borderRadius: '7px',
            fontSize: '12px',
            fontWeight: 700,
            border: 'none',
            backgroundColor: subTab === 'modelo_ia' ? '#7c3aed' : 'transparent',
            color: subTab === 'modelo_ia' ? '#ffffff' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: subTab === 'modelo_ia' ? '0 1px 3px rgba(124,58,237,0.2)' : 'none',
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
            gap: '8px',
            padding: '8px 12px',
            borderRadius: '7px',
            fontSize: '12px',
            fontWeight: 700,
            border: 'none',
            backgroundColor: subTab === 'tesis' ? '#059669' : 'transparent',
            color: subTab === 'tesis' ? '#ffffff' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            boxShadow: subTab === 'tesis' ? '0 1px 3px rgba(5,150,105,0.2)' : 'none',
          }}
        >
          <GraduationCap size={15} />
          <span>Tesis y Validación</span>
        </button>
      </div>

      {/* Active Sub-tab View */}
      {subTab === 'como_funciona' && <ComoFuncionaTab />}
      {subTab === 'modelo_ia' && <ModeloIATab />}
      {subTab === 'tesis' && <TesisValidacionTab />}
    </div>
  );
};
