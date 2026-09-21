import { useState, useCallback, useEffect, useRef } from 'react';
import { dashboardApi } from '../features/dashboard/api';
import type { ResumenMetricas } from '../types';
import {
  obtenerPeriodosComparativa,
  type DashboardPreset,
  type PeriodosComparativa,
} from '../utils/dashboardComparador';
import { getErrorMessage } from '../utils/errors';

export interface DashboardOperativoState {
  preset: DashboardPreset;
  periodos: PeriodosComparativa;
  metricasActuales: ResumenMetricas | null;
  metricasAnteriores: ResumenMetricas | null;
  cargando: boolean;
  error: string | null;
  customInicio: string;
  customFin: string;
  cambiarPreset: (nuevoPreset: 'hoy' | '7dias' | 'esteMes') => void;
  aplicarRangoCustom: (inicio: string, fin: string) => void;
  recargar: () => void;
}

export function useDashboardOperativo(): DashboardOperativoState {
  const [preset, setPreset] = useState<DashboardPreset>('esteMes');
  const [customInicio, setCustomInicio] = useState('');
  const [customFin, setCustomFin] = useState('');

  const [metricasActuales, setMetricasActuales] = useState<ResumenMetricas | null>(null);
  const [metricasAnteriores, setMetricasAnteriores] = useState<ResumenMetricas | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [periodos, setPeriodos] = useState<PeriodosComparativa>(() =>
    obtenerPeriodosComparativa('esteMes')
  );

  // Evita condiciones de carrera con peticiones asíncronas
  const abortControllerRef = useRef<number>(0);

  const cargar = useCallback(
    async (
      nuevoPreset: DashboardPreset,
      cInicio?: string,
      cFin?: string
    ) => {
      const callId = ++abortControllerRef.current;
      const pers = obtenerPeriodosComparativa(nuevoPreset, cInicio, cFin);
      setPeriodos(pers);
      setCargando(true);
      setError(null);

      try {
        const [dataActual, dataAnterior, colas] = await Promise.all([
          dashboardApi.getResumenMetricas(pers.actual.inicio, pers.actual.fin),
          pers.anterior
            ? dashboardApi.getResumenMetricas(pers.anterior.inicio, pers.anterior.fin).catch(() => null)
            : Promise.resolve(null),
          dashboardApi.getMetricasColas().catch(() => undefined),
        ]);

        if (callId === abortControllerRef.current) {
          setMetricasActuales(dataActual ? { ...dataActual, colas } : null);
          setMetricasAnteriores(dataAnterior);
        }
      } catch (err: unknown) {
        if (callId === abortControllerRef.current) {
          setError(getErrorMessage(err, 'Error al cargar los datos del dashboard operativo'));
        }
      } finally {
        if (callId === abortControllerRef.current) {
          setCargando(false);
        }
      }
    },
    []
  );

  const cambiarPreset = useCallback(
    (nuevoPreset: 'hoy' | '7dias' | 'esteMes') => {
      setPreset(nuevoPreset);
      setCustomInicio('');
      setCustomFin('');
      void cargar(nuevoPreset);
    },
    [cargar]
  );

  const aplicarRangoCustom = useCallback(
    (inicio: string, fin: string) => {
      setPreset('custom');
      setCustomInicio(inicio);
      setCustomFin(fin);
      void cargar('custom', inicio, fin);
    },
    [cargar]
  );

  const recargar = useCallback(() => {
    void cargar(preset, customInicio, customFin);
  }, [cargar, preset, customInicio, customFin]);

  // Carga inicial
  useEffect(() => {
    void cargar('esteMes');
  }, [cargar]);

  return {
    preset,
    periodos,
    metricasActuales,
    metricasAnteriores,
    cargando,
    error,
    customInicio,
    customFin,
    cambiarPreset,
    aplicarRangoCustom,
    recargar,
  };
}
