import { useState, useCallback, useRef, useEffect } from 'react';
import { diagnosticsApi } from '../features/management/api/diagnosticsApi';
import type { Diagnostico } from '../types';
import { getErrorMessage } from '../utils/errors';

export function useDiagnosticos() {
  const solicitud = useRef(0);
  useEffect(() => () => { solicitud.current++; }, []);
  const [diagnosticos, setDiagnosticos] = useState<Diagnostico[]>([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const cargarDiagnosticos = useCallback(async (filtros?: {
    busqueda?: string;
    estado?: string;
    modo?: string;
    mecanico_id?: string;
    limite?: number;
    offset?: number;
    fecha_desde?: string;
    fecha_hasta?: string;
  }) => {
    const version = ++solicitud.current;
    setCargando(true);
    setError(null);
    try {
      const data = await diagnosticsApi.listar({ limite: 10, ...filtros });
      if (version !== solicitud.current) return;
      setDiagnosticos(data.items);
      setTotal(data.total);
    } catch (error: unknown) {
      if (version !== solicitud.current) return;
      setDiagnosticos([]);
      setError(getErrorMessage(error, 'Error al cargar el historial de diagnósticos'));
    } finally {
      if (version === solicitud.current) setCargando(false);
    }
  }, []);

  return {
    diagnosticos,
    cargando,
    error,
    total,
    cargarDiagnosticos,
  };
}
