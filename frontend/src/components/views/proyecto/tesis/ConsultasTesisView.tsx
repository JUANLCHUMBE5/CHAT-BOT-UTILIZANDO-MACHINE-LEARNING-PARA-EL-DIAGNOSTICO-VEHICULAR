import { useEffect, useState } from 'react';
import { useDiagnosticos } from '../../../../hooks/useDiagnosticos';
import { dashboardApi } from '../../../../features/dashboard/api';
import { DiagnosticosView } from '../../DiagnosticosView';
import { PeriodoFilter } from '../../../common/PeriodoFilter';
import { Card } from '../../../common/Card';
import { periodoDias, type Periodo } from '../../../../utils/periodo';
import type { Diagnostico, ResumenMetricas } from '../../../../types';

export function ConsultasTesisView() {
  const historial = useDiagnosticos();
  const [periodo, setPeriodo] = useState<Periodo>(() => periodoDias(7));
  const [seleccionado, setSeleccionado] = useState<Diagnostico | null>(null);
  const [metricas, setMetricas] = useState<ResumenMetricas | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let activo = true;
    let enCurso = false;
    setMetricas(null);
    const cargar = async () => {
      if (enCurso) return;
      enCurso = true;
      try {
        const datos = await dashboardApi.getResumenMetricas(periodo.fecha_desde, periodo.fecha_hasta, true);
        if (activo) { setMetricas(datos); setError(null); }
      } catch (e) { if (activo) { setMetricas(null); setError(e instanceof Error ? e.message : 'No se pudo cargar el resumen'); } }
      finally { enCurso = false; }
    };
    void cargar();
    const timer = setInterval(() => { if (!document.hidden) void cargar(); }, 30000);
    return () => { activo = false; clearInterval(timer); };
  }, [periodo]);
  const cantidad = metricas?.diagnosticos_realizados ?? metricas?.diagnosticos_mes ?? 0;
  return <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr)', gap: 14 }}>
    <PeriodoFilter value={periodo} onChange={setPeriodo} />
    {error && <div role="alert" className="inline-error">{error}</div>}
    {metricas && <Card>
      <h3 style={{ marginTop: 0 }}>Resumen de consultas del período</h3>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 24 }}>
        <span><strong>{cantidad}</strong> diagnósticos</span>
        <span><strong>{metricas.diagnosticos_pendientes ?? 0}</strong> pendientes de confirmación</span>
        <span><strong>{cantidad ? `${metricas.porcentaje_confirmados}%` : 'Sin datos'}</strong> confirmados</span>
        <span>Respuesta del bot: <strong>{cantidad ? `${metricas.tiempo_promedio_ms} ms` : 'Sin datos'}</strong></span>
      </div>
      <details style={{ marginTop: 12 }}><summary>Fallas frecuentes</summary>
        {metricas.fallas_frecuentes.length ? <ul>{metricas.fallas_frecuentes.map(f =>
          <li key={f.falla}>{f.falla}: {f.cantidad}</li>)}</ul> : <p>Sin fallas registradas.</p>}
      </details>
      <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Resumen de todo el período. Los filtros del historial solo afectan la lista.</p>
    </Card>}
    <DiagnosticosView diagnosticos={historial.diagnosticos} totalDiagnosticos={historial.total}
      cargando={historial.cargando} error={historial.error} mecanicos={[]}
      onFiltrar={historial.cargarDiagnosticos} periodoExterno={periodo}
      diagnosticoSeleccionadoModal={seleccionado} onAbrirModalDetalle={setSeleccionado}
      onCerrarModalDetalle={() => setSeleccionado(null)} />
  </div>;
}
