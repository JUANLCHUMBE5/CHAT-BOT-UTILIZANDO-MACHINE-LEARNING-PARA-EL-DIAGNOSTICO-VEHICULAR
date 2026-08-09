import { useState, useCallback } from 'react';
import { apiService } from '../services/api';
import type { Diagnostico, EstadoDiagnostico } from '../types';

export function useDiagnosticos() {
  const [diagnosticos, setDiagnosticos] = useState<Diagnostico[]>([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cargarDiagnosticos = useCallback(async (filtros?: {
    busqueda?: string;
    estado?: string;
    modo?: string;
    mecanico_id?: string;
  }) => {
    setCargando(true);
    setError(null);
    try {
      const data = await apiService.getDiagnosticos(filtros);
      setDiagnosticos(data);
    } catch (err: any) {
      setError(err?.message || 'Error al cargar el historial de diagnósticos');
    } finally {
      setCargando(false);
    }
  }, []);

  const actualizarEstado = useCallback(async (
    id: string,
    nuevoEstado: EstadoDiagnostico,
    notas?: string
  ) => {
    await apiService.actualizarEstadoDiagnostico({
      diagnostico_id: id,
      nuevo_estado: nuevoEstado,
      notas_mecanico: notas,
    });
    await cargarDiagnosticos();
  }, [cargarDiagnosticos]);

  return {
    diagnosticos,
    cargando,
    error,
    cargarDiagnosticos,
    actualizarEstado,
  };
}
