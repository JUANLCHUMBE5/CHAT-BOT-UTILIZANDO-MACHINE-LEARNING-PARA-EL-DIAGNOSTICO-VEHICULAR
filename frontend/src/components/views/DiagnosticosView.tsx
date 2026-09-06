import { useState, useEffect } from 'react';
import type { Diagnostico, Mecanico } from '../../types';
import { DiagnosticosHeader, DiagnosticosTabla, DiagnosticoDetalleModal } from './diagnosticos';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { PeriodoFilter } from '../common/PeriodoFilter';
import { limitesDiagnosticos, type Periodo } from '../../utils/periodo';

export interface DiagnosticosViewProps {
  diagnosticos: Diagnostico[];
  totalDiagnosticos: number;
  cargando?: boolean;
  mecanicos: Mecanico[];
  initialFiltroMecanico?: string;
  onFiltroMecanicoSeleccionado?: (id: string) => void;
  onFiltrar?: (filtros: { busqueda?: string; estado?: string; modo?: string; mecanico_id?: string;
    limite?: number; offset?: number; fecha_desde?: string; fecha_hasta?: string }) => Promise<void>;
  error?: string | null;
  refreshKey?: number;
  diagnosticoSeleccionadoModal?: Diagnostico | null;
  onCerrarModalDetalle: () => void;
  onAbrirModalDetalle: (diag: Diagnostico) => void;
  periodoExterno?: Periodo;
}

export const DiagnosticosView = ({ diagnosticos, totalDiagnosticos, cargando = false, mecanicos,
  initialFiltroMecanico, onFiltroMecanicoSeleccionado, onFiltrar, error, refreshKey = 0,
  diagnosticoSeleccionadoModal, onCerrarModalDetalle, onAbrirModalDetalle, periodoExterno }: DiagnosticosViewProps) => {
  const [filtros, setFiltros] = useState({ busqueda: '', estado: '', mecanico: initialFiltroMecanico || 'todos', pagina: 1 });
  const [periodoInterno, setPeriodo] = useState<Periodo>({});
  const periodo = periodoExterno || periodoInterno;
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    if (initialFiltroMecanico !== undefined) setFiltros(f => ({ ...f, mecanico: initialFiltroMecanico, pagina: 1 }));
  }, [initialFiltroMecanico]);
  useEffect(() => { setFiltros(f => ({ ...f, pagina: 1 })); }, [periodo]);
  useEffect(() => {
    const timer = setInterval(() => { if (!document.hidden) setRevision(r => r + 1); }, 30000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    const timer = setTimeout(() => {
      void onFiltrar?.({ busqueda: filtros.busqueda.trim() || undefined, estado: filtros.estado || undefined,
        mecanico_id: filtros.mecanico !== 'todos' ? filtros.mecanico : undefined,
        limite: 10, offset: (filtros.pagina - 1) * 10, ...limitesDiagnosticos(periodo) });
    }, 300);
    return () => clearTimeout(timer);
  }, [filtros, periodo, refreshKey, revision, onFiltrar]);
  const totalPaginas = Math.max(1, Math.ceil(totalDiagnosticos / 10));
  // El backend mantiene el orden cronológico global, también entre páginas.
  return <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr)', gap: 14 }}>
    <DiagnosticosHeader totalProcesados={diagnosticos.length} totalTotal={totalDiagnosticos} />
    {error && <div className="inline-error" role="alert">{error}</div>}
    {!periodoExterno && <PeriodoFilter value={periodo} onChange={setPeriodo} />}
    <div className="periodo-filter">
      <Input placeholder="Buscar síntoma, falla o mecánico" value={filtros.busqueda}
        onChange={e => setFiltros(f => ({ ...f, busqueda: e.target.value, pagina: 1 }))} />
      <Select value={filtros.estado} onChange={e => setFiltros(f => ({ ...f, estado: e.target.value, pagina: 1 }))}
        options={[{ value: '', label: 'Todos los estados' }, ...['generado', 'en_revision', 'confirmado', 'descartado'].map(value => ({ value, label: value.replace('_', ' ') }))]} />
      {mecanicos.length > 0 && <Select value={filtros.mecanico} onChange={e => {
        setFiltros(f => ({ ...f, mecanico: e.target.value, pagina: 1 })); onFiltroMecanicoSeleccionado?.(e.target.value);
      }} options={[{ value: 'todos', label: 'Todos los mecánicos' }, ...mecanicos.map(m => ({ value: m.id, label: m.nombres }))]} />}
      <button type="button" onClick={() => setRevision(r => r + 1)} disabled={cargando}>Actualizar</button>
    </div>
    <p style={{ margin: 0, fontSize: 12 }}>Del más antiguo al más reciente · 10 por página</p>
    <DiagnosticosTabla diagnosticosPaginados={diagnosticos} cargando={cargando} totalProcesados={totalDiagnosticos}
      paginaActual={filtros.pagina} totalPaginas={totalPaginas} elementosPorPagina={10}
      onCambiarPagina={pagina => setFiltros(f => ({ ...f, pagina: Math.max(1, Math.min(pagina, totalPaginas)) }))}
      onElementosPorPaginaChange={() => {}} onVerDetalle={onAbrirModalDetalle} />
    <DiagnosticoDetalleModal diagnostico={diagnosticoSeleccionadoModal || null}
      isOpen={Boolean(diagnosticoSeleccionadoModal)} onClose={onCerrarModalDetalle} />
  </div>;
};
