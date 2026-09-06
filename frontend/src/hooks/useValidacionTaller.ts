import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { apiService } from '../services/api';
import type { CasoValidacionDTO, MetricasValidacionDTO, CrearCasoValidacionDTO } from '../types/api';
import type { Periodo } from '../utils/periodo';

const vacio = (): CrearCasoValidacionDTO => ({
  fase: 'Post-test', placa: '', marca_modelo: '', sintoma: '', falla_real: '',
  chatbot_prediccion: '', campos_completos: -1, tiempo_diagnostico_minutos: 0,
  prediccion_correcta: -1, metodo_confirmacion: '', evidencia_ref: '',
});

export const useValidacionTaller = () => {
  const [metricas, setMetricas] = useState<MetricasValidacionDTO | null>(null);
  const [casos, setCasos] = useState<CasoValidacionDTO[]>([]);
  const [totalCasos, setTotalCasos] = useState(0);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorMetricas, setErrorMetricas] = useState<string | null>(null);
  const [filtros, setFiltros] = useState({ fase: '', acierto: '', busqueda: '', pagina: 0 });
  const [periodo, guardarPeriodo] = useState<Periodo>({});
  const [revision, setRevision] = useState(0);
  const [modalAbierto, setModalAbierto] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [exitoMensaje, setExitoMensaje] = useState<string | null>(null);
  const [nuevoCaso, setNuevoCaso] = useState(vacio);
  const limite = 10;
  const cargarDatos = () => setRevision(r => r + 1);
  const setPeriodo = (p: Periodo) => { guardarPeriodo(p); setFiltros(f => ({ ...f, pagina: 0 })); };

  useEffect(() => {
    let activo = true;
    setCargando(true); setError(null);
    const timer = setTimeout(async () => {
      try {
        const res = await apiService.getCasosValidacion({ ...periodo, fase: filtros.fase || undefined,
          acierto: filtros.acierto === '' ? undefined : Number(filtros.acierto),
          busqueda: filtros.busqueda || undefined, skip: filtros.pagina * limite, limit: limite });
        if (!activo) return;
        const ultima = Math.max(0, Math.ceil(res.total / limite) - 1);
        if (filtros.pagina > ultima) { setFiltros(f => ({ ...f, pagina: ultima })); return; }
        setCasos(res.casos); setTotalCasos(res.total);
      } catch (e) {
        if (activo) { setCasos([]); setError(e instanceof Error ? e.message : 'No se pudo cargar el historial'); }
      } finally { if (activo) setCargando(false); }
    }, 300);
    return () => { activo = false; clearTimeout(timer); };
  }, [filtros, periodo, revision]);

  // Agregados del período completo; cambiar de página no vuelve a calcularlos.
  useEffect(() => {
    let activo = true;
    setMetricas(null); setErrorMetricas(null);
    apiService.getMetricasValidacion(periodo).then(res => { if (activo) setMetricas(res); })
      .catch(e => { if (activo) setErrorMetricas(e instanceof Error ? e.message : 'No se pudieron cargar las métricas'); });
    return () => { activo = false; };
  }, [periodo, revision]);

  useEffect(() => {
    const timer = setInterval(() => { if (!document.hidden) setRevision(r => r + 1); }, 30000);
    return () => clearInterval(timer);
  }, []);

  const handleCrearCaso = async (e: FormEvent) => {
    e.preventDefault(); setError(null); setExitoMensaje(null);
    if (nuevoCaso.campos_completos < 0 || nuevoCaso.prediccion_correcta < 0) {
      setError('Indica el resultado y si el registro está completo.'); return;
    }
    try {
      setGuardando(true);
      await apiService.crearCasoValidacion(nuevoCaso);
      setExitoMensaje('Caso guardado.'); setModalAbierto(false); setNuevoCaso(vacio()); cargarDatos();
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo guardar el caso'); }
    finally { setGuardando(false); }
  };
  const handleDescargarCsv = async () => {
    try { await apiService.descargarValidacionCsv(periodo); }
    catch (e) { setError(e instanceof Error ? e.message : 'No se pudo exportar'); }
  };
  return { metricas, casos, totalCasos, cargando, error: error || errorMetricas,
    faseFiltro: filtros.fase, setFaseFiltro: (fase: string) => setFiltros(f => ({ ...f, fase, pagina: 0 })),
    aciertoFiltro: filtros.acierto, setAciertoFiltro: (acierto: string) => setFiltros(f => ({ ...f, acierto, pagina: 0 })),
    busqueda: filtros.busqueda, setBusqueda: (busqueda: string) => setFiltros(f => ({ ...f, busqueda, pagina: 0 })),
    pagina: filtros.pagina, setPagina: (pagina: number) => setFiltros(f => ({ ...f, pagina })),
    totalPaginas: Math.max(1, Math.ceil(totalCasos / limite)), periodo, setPeriodo,
    modalAbierto, setModalAbierto, guardando, exitoMensaje, nuevoCaso, setNuevoCaso,
    handleCrearCaso, handleDescargarCsv, cargarDatos };
};
