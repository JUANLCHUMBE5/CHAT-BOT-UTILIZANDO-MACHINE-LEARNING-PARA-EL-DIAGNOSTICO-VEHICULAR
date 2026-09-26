import React from 'react';
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from 'lucide-react';
import { Card } from '../../common/Card';
import type { Diagnostico } from '../../../types';
import { DiagnosticosDesktopTable } from './DiagnosticosDesktopTable';
import { DiagnosticosMobileCards } from './DiagnosticosMobileCards';

interface DiagnosticosTablaProps {
  diagnosticosPaginados: Diagnostico[];
  cargando: boolean;
  totalProcesados: number;
  paginaActual: number;
  totalPaginas: number;
  elementosPorPagina: number;
  onCambiarPagina: (pagina: number) => void;
  onElementosPorPaginaChange: (cantidad: number) => void;
  onVerDetalle: (d: Diagnostico) => void;
}

export const DiagnosticosTabla: React.FC<DiagnosticosTablaProps> = ({
  diagnosticosPaginados,
  cargando,
  totalProcesados,
  paginaActual,
  totalPaginas,
  elementosPorPagina,
  onCambiarPagina,
  onElementosPorPaginaChange,
  onVerDetalle,
}) => {
  return (
    <Card style={{ padding: 0, overflow: 'hidden' }}>
      {/* 1. Desktop / Tablet Table View */}
      <DiagnosticosDesktopTable
        diagnosticos={diagnosticosPaginados}
        cargando={cargando}
        onVerDetalle={onVerDetalle}
      />

      {/* 2. Mobile Card Feed View */}
      <DiagnosticosMobileCards
        diagnosticos={diagnosticosPaginados}
        cargando={cargando}
        onVerDetalle={onVerDetalle}
      />

      {/* Pagination Bar */}
      {!cargando && totalProcesados > 0 && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '10px 14px',
            borderTop: '1px solid var(--border-color)',
            backgroundColor: 'var(--bg-main)',
            flexWrap: 'wrap',
            gap: '10px',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '12px',
              color: 'var(--text-secondary)',
            }}
          >
            <span>Mostrar</span>
            <select
              value={elementosPorPagina}
              onChange={(e) => onElementosPorPaginaChange(Number(e.target.value))}
              style={{
                padding: '4px 8px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
                fontSize: '12px',
                backgroundColor: '#ffffff',
              }}
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
            <span>por página</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={() => onCambiarPagina(1)}
              disabled={paginaActual <= 1}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '3px',
                height: '30px',
                padding: '0 8px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#ffffff',
                fontSize: '11.5px',
                fontWeight: 600,
                color: paginaActual <= 1 ? 'var(--text-muted)' : 'var(--text-main)',
                cursor: paginaActual <= 1 ? 'not-allowed' : 'pointer',
                opacity: paginaActual <= 1 ? 0.45 : 1,
              }}
              title="Primera página"
            >
              <ChevronsLeft size={13} />
              <span className="desktop-only">Primera</span>
            </button>

            <button
              type="button"
              onClick={() => onCambiarPagina(paginaActual - 1)}
              aria-label="Página anterior"
              disabled={paginaActual <= 1}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '30px',
                height: '30px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#ffffff',
                color: paginaActual <= 1 ? 'var(--text-muted)' : 'var(--text-main)',
                cursor: paginaActual <= 1 ? 'not-allowed' : 'pointer',
                opacity: paginaActual <= 1 ? 0.45 : 1,
              }}
              title="Página anterior"
            >
              <ChevronLeft size={15} />
            </button>

            <span
              style={{
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                padding: '0 6px',
                whiteSpace: 'nowrap',
              }}
            >
              Página {paginaActual} de {totalPaginas}
            </span>

            <button
              type="button"
              onClick={() => onCambiarPagina(paginaActual + 1)}
              aria-label="Página siguiente"
              disabled={paginaActual >= totalPaginas}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '30px',
                height: '30px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#ffffff',
                color: paginaActual >= totalPaginas ? 'var(--text-muted)' : 'var(--text-main)',
                cursor: paginaActual >= totalPaginas ? 'not-allowed' : 'pointer',
                opacity: paginaActual >= totalPaginas ? 0.45 : 1,
              }}
              title="Página siguiente"
            >
              <ChevronRight size={15} />
            </button>

            <button
              type="button"
              onClick={() => onCambiarPagina(totalPaginas)}
              disabled={paginaActual >= totalPaginas}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '3px',
                height: '30px',
                padding: '0 8px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#ffffff',
                fontSize: '11.5px',
                fontWeight: 600,
                color: paginaActual >= totalPaginas ? 'var(--text-muted)' : 'var(--text-main)',
                cursor: paginaActual >= totalPaginas ? 'not-allowed' : 'pointer',
                opacity: paginaActual >= totalPaginas ? 0.45 : 1,
              }}
              title="Última página"
            >
              <span className="desktop-only">Última</span>
              <ChevronsRight size={13} />
            </button>
          </div>
        </div>
      )}
    </Card>
  );
};
