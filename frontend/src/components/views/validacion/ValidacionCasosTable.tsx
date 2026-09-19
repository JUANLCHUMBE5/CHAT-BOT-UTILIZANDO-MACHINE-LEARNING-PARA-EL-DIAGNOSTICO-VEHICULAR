import React, { useState } from 'react';
import {
  AlertTriangle,
  Car,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Clock,
  RefreshCw,
  RotateCcw,
  Search,
} from 'lucide-react';
import { Card } from '../../common/Card';
import { Input } from '../../common/Input';
import { Select } from '../../common/Select';
import { Modal } from '../../common/Modal';
import type { CasoValidacionDTO } from '../../../types/api';

interface ValidacionCasosTableProps {
  casos: CasoValidacionDTO[];
  totalCasos: number;
  cargando: boolean;
  busqueda: string;
  onBusquedaChange: (v: string) => void;
  faseFiltro: string;
  onFaseFiltroChange: (v: string) => void;
  aciertoFiltro: string;
  onAciertoFiltroChange: (v: string) => void;
  pagina: number;
  totalPaginas: number;
  onCambiarPagina: (p: number) => void;
}

export const ValidacionCasosTable: React.FC<ValidacionCasosTableProps> = ({
  casos,
  totalCasos,
  cargando,
  busqueda,
  onBusquedaChange,
  faseFiltro,
  onFaseFiltroChange,
  aciertoFiltro,
  onAciertoFiltroChange,
  pagina,
  totalPaginas,
  onCambiarPagina,
}) => {
  const [seleccionado, setSeleccionado] = useState<CasoValidacionDTO | null>(null);
  const contarCampos = (caso: CasoValidacionDTO) => caso.cantidad_campos_completos ?? (caso.campos_completos ? 8 : 0);
  return (
    <Card style={{ padding: 0, overflow: 'hidden' }}>
      {/* Barra de Filtros */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          gap: '12px',
          alignItems: 'center',
          flexWrap: 'wrap',
          backgroundColor: 'var(--bg-main)',
        }}
      >
        <div style={{ flex: 1, minWidth: '220px' }}>
          <Input
            placeholder="Buscar por placa, síntoma o falla real..."
            value={busqueda}
            onChange={(e) => onBusquedaChange(e.target.value)}
            icon={<Search size={16} />}
          />
        </div>
        <div style={{ width: '160px' }}>
          <Select
            value={faseFiltro}
            onChange={(e) => onFaseFiltroChange(e.target.value)}
            options={[
              { value: '', label: 'Fase: Todas' },
              { value: 'Pre-test', label: 'Pre-test (Manual)' },
              { value: 'Post-test', label: 'Post-test (CarBot)' },
              { value: 'Piloto', label: 'Piloto' },
            ]}
          />
        </div>
        <div style={{ width: '160px' }}>
          <Select
            value={aciertoFiltro}
            onChange={(e) => onAciertoFiltroChange(e.target.value)}
            options={[
              { value: '', label: 'Resultado: Todos' },
              { value: '1', label: 'Acierto (1)' },
              { value: '0', label: 'Desacierto (0)' },
            ]}
          />
        </div>
        {Boolean(busqueda.trim() || faseFiltro || aciertoFiltro) && (
          <button
            type="button"
            onClick={() => {
              onBusquedaChange('');
              onFaseFiltroChange('');
              onAciertoFiltroChange('');
            }}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 12px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              backgroundColor: 'transparent',
              color: 'var(--text-secondary)',
              fontSize: '12px',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              height: '38px',
            }}
            title="Restablecer filtros"
          >
            <RotateCcw size={13} />
            <span>Limpiar</span>
          </button>
        )}
      </div>

      {/* Tabla de Registros */}
      <div className="validacion-table-scroll" style={{ overflowX: 'auto' }}>
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
              <th style={{ padding: '12px 16px' }}>Registro / Fase</th>
              <th style={{ padding: '12px 16px' }}>Placa / Vehículo</th>
              <th style={{ padding: '12px 16px' }}>Síntoma Reportado</th>
              <th style={{ padding: '12px 16px' }}>Hipótesis inicial</th>
              <th style={{ padding: '12px 16px' }}>Falla Real Confirmada</th>
              <th style={{ padding: '12px 16px', textAlign: 'center' }}>Acierto</th>
              <th style={{ padding: '12px 16px', textAlign: 'right' }}>Tiempo</th>
            </tr>
          </thead>
          <tbody>
            {cargando ? (
              <tr>
                <td colSpan={7} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                    <RefreshCw size={22} className="animate-spin" style={{ color: 'var(--primary)' }} />
                    <span>Cargando registros…</span>
                  </div>
                </td>
              </tr>
            ) : casos.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No se encontraron casos registrados con los filtros aplicados.
                </td>
              </tr>
            ) : (
              casos.map((caso, idx) => (
                <tr
                  key={`${caso.item || idx}-${caso.placa_hash || idx}`}
                  className="table-row-hover"
                  style={{
                    borderBottom: '1px solid var(--border-color)',
                    backgroundColor: caso.fase === 'Post-test' ? 'rgba(59, 130, 246, 0.02)' : 'transparent',
                  }}
                >
                  <td style={{ padding: '12px 16px' }}>
                    <button type="button" onClick={() => setSeleccionado(caso)}
                      style={{ display: 'block', marginBottom: 8, cursor: 'pointer', border: 0, background: 'none', color: 'var(--primary)', padding: 0, fontWeight: 600 }}>
                      Ver registro #{caso.item}
                    </button>
                    <div style={{ fontSize: 12, marginBottom: 8 }}>{caso.fecha}</div>
                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: '10px',
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: caso.fase === 'Post-test' ? '#eff6ff' : '#f1f5f9',
                        color: caso.fase === 'Post-test' ? '#1d4ed8' : '#475569',
                        border: `1px solid ${caso.fase === 'Post-test' ? '#bfdbfe' : '#e2e8f0'}`,
                      }}
                    >
                      {caso.fase}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Car size={14} style={{ color: 'var(--text-muted)' }} />
                      <strong style={{ color: 'var(--text-main)' }}>{caso.placa_enmascarada || '—'}</strong>
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {caso.marca_modelo}
                    </div>
                  </td>
                  <td style={{ padding: '12px 16px', maxWidth: '200px' }}>
                    <p style={{ margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={caso.sintoma}>
                      {caso.sintoma}
                    </p>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                      {caso.chatbot_prediccion || '— (Manual)'}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ color: '#047857', fontWeight: 600 }}>{caso.falla_real}</span>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{caso.metodo_confirmacion}</div>
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                    {caso.prediccion_correcta === 1 ? (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#16a34a', fontWeight: 700, fontSize: '12px' }}>
                        <CheckCircle size={14} /> Correcto
                      </span>
                    ) : (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#dc2626', fontWeight: 700, fontSize: '12px' }}>
                        <AlertTriangle size={14} /> Desacierto
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--text-secondary)', fontWeight: 600 }}>
                      <Clock size={12} /> {caso.tiempo_diagnostico_minutos} min
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="validacion-cards">
        {cargando ? <p role="status">Cargando registros…</p> : casos.length === 0 ? <p>Sin registros para estos filtros.</p> : casos.map(caso =>
          <article key={caso.item}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
              <strong>#{caso.item} · {caso.fase}</strong><span>{caso.fecha}</span>
            </div>
            <p>{caso.sintoma}</p>
            <p>{caso.prediccion_correcta ? 'Correcto' : 'Incorrecto'} · {caso.tiempo_diagnostico_minutos} min · {caso.campos_completos ? 'Completo' : 'Incompleto'}</p>
            <button type="button" onClick={() => setSeleccionado(caso)}>Ver detalle #{caso.item}</button>
          </article>)}
      </div>

      {/* Paginación */}
      {!cargando && totalCasos > 0 && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '12px 20px',
            borderTop: '1px solid var(--border-color)',
            backgroundColor: 'var(--bg-main)',
            flexWrap: 'wrap',
            gap: 8,
          }}
        >
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            {pagina * 10 + 1}–{pagina * 10 + casos.length} de {totalCasos} · 10 por página
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={() => onCambiarPagina(0)}
              disabled={pagina === 0}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '3px',
                height: '32px',
                padding: '0 10px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#ffffff',
                fontSize: '12px',
                fontWeight: 600,
                color: pagina === 0 ? 'var(--text-muted)' : 'var(--text-main)',
                cursor: pagina === 0 ? 'not-allowed' : 'pointer',
                opacity: pagina === 0 ? 0.45 : 1,
                transition: 'all 0.15s ease',
              }}
              title="Primera página"
            >
              <ChevronsLeft size={14} />
              <span>Primera</span>
            </button>

            <button
              type="button"
              onClick={() => onCambiarPagina(Math.max(0, pagina - 1))}
              aria-label="Página anterior"
              disabled={pagina === 0}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '32px',
                height: '32px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#ffffff',
                color: pagina === 0 ? 'var(--text-muted)' : 'var(--text-main)',
                cursor: pagina === 0 ? 'not-allowed' : 'pointer',
                opacity: pagina === 0 ? 0.45 : 1,
                transition: 'all 0.15s ease',
              }}
              title="Página anterior"
            >
              <ChevronLeft size={16} />
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
              Página {pagina + 1} de {Math.max(1, totalPaginas)}
            </span>

            <button
              type="button"
              onClick={() => onCambiarPagina(pagina + 1)}
              aria-label="Página siguiente"
              disabled={pagina + 1 >= totalPaginas}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '32px',
                height: '32px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#ffffff',
                color: pagina + 1 >= totalPaginas ? 'var(--text-muted)' : 'var(--text-main)',
                cursor: pagina + 1 >= totalPaginas ? 'not-allowed' : 'pointer',
                opacity: pagina + 1 >= totalPaginas ? 0.45 : 1,
                transition: 'all 0.15s ease',
              }}
              title="Página siguiente"
            >
              <ChevronRight size={16} />
            </button>

            <button
              type="button"
              onClick={() => onCambiarPagina(totalPaginas - 1)}
              disabled={pagina + 1 >= totalPaginas}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '3px',
                height: '32px',
                padding: '0 10px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#ffffff',
                fontSize: '12px',
                fontWeight: 600,
                color: pagina + 1 >= totalPaginas ? 'var(--text-muted)' : 'var(--text-main)',
                cursor: pagina + 1 >= totalPaginas ? 'not-allowed' : 'pointer',
                opacity: pagina + 1 >= totalPaginas ? 0.45 : 1,
                transition: 'all 0.15s ease',
              }}
              title="Última página"
            >
              <span>Última</span>
              <ChevronsRight size={14} />
            </button>
          </div>
        </div>
      )}
      <Modal isOpen={Boolean(seleccionado)} onClose={() => setSeleccionado(null)}
        title={`Evaluación #${seleccionado?.item || ''}`}>
        {seleccionado && <dl style={{ overflowWrap: 'anywhere' }}>
          {[
            ['Fecha y fase', `${seleccionado.fecha} · ${seleccionado.fase}`],
            ['Tipo de registro', seleccionado.tipo_registro || 'THESIS_POSTTEST'],
            ['Vehículo', `${seleccionado.placa_enmascarada} · ${seleccionado.marca_modelo}`],
            ['Año / km / combustible / transmisión', `${seleccionado.vehiculo_anio || 's/r'} · ${seleccionado.vehiculo_kilometraje ?? 's/r'} km · ${seleccionado.vehiculo_combustible || 's/r'} · ${seleccionado.vehiculo_transmision || 's/r'}`],
            ['Síntoma', seleccionado.sintoma],
            ['Descripción del síntoma', seleccionado.descripcion_sintoma || 'Sin registrar'],
            [seleccionado.fase === 'Pre-test' ? 'Hipótesis del mecánico' : 'Predicción del chatbot', seleccionado.chatbot_prediccion],
            ['Falla comprobada', seleccionado.falla_real],
            ['Resultado', seleccionado.prediccion_correcta ? 'Correcto' : 'Incorrecto'],
            ['Campos Ficha 2', `${contarCampos(seleccionado)}/8`],
            ['Registro', seleccionado.campos_completos ? 'Completo (declarado por evaluador)' : 'Incompleto'],
            ['Tiempo diagnóstico', `${seleccionado.tiempo_diagnostico_minutos} min`],
            ['Método de confirmación', seleccionado.metodo_confirmacion || 'Sin registrar'],
            ['Evidencia', seleccionado.evidencia_ref || 'Sin registrar'],
            ...(seleccionado.conversacion_id ? [['ID Conversación WhatsApp', seleccionado.conversacion_id]] : []),
            ...(seleccionado.diagnostico_id ? [['ID Diagnóstico CarBot', seleccionado.diagnostico_id]] : []),
          ].map(([label, valor]) => <div key={label} style={{ marginBottom: 12 }}>
            <dt style={{ fontWeight: 600 }}>{label}</dt><dd style={{ margin: '4px 0' }}>{valor}</dd>
          </div>)}
          {seleccionado.detalles_campos && (
            <div style={{ marginTop: 12 }}>
              <dt style={{ fontWeight: 700, marginBottom: 8 }}>Detalle auditable Ficha 2</dt>
              {Object.entries(seleccionado.detalles_campos).map(([clave, campo]) => (
                <dd key={clave} style={{ margin: '4px 0', display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <span>{campo.nombre}</span>
                  <strong style={{ color: campo.completo ? '#047857' : '#dc2626' }}>
                    {campo.completo ? 'Completo' : 'Incompleto'}
                  </strong>
                </dd>
              ))}
            </div>
          )}
        </dl>}
      </Modal>
    </Card>
  );
};
