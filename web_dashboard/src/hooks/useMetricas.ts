import { useState, useCallback } from 'react';
import { apiService } from '../services/api';
import type { ResumenMetricas } from '../types';

export function useMetricas() {
  const [metricas, setMetricas] = useState<ResumenMetricas | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cargarMetricas = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const data = await apiService.getResumenMetricas();
      setMetricas(data);
    } catch (err: any) {
      setError(err?.message || 'Error al cargar las métricas ejecutivas');
    } finally {
      setCargando(false);
    }
  }, []);

  return {
    metricas,
    cargando,
    error,
    cargarMetricas,
  };
}
