import { useState, useEffect, useMemo } from 'react';
import type { Mecanico } from '../../../../types';
import { limitesDiagnosticos, periodoDias, type Periodo } from '../../../../utils/periodo';

export interface UseDiagnosticosFilterProps {
  totalDiagnosticos: number;
  mecanicos: Mecanico[];
  initialFiltroMecanico?: string;
  onFiltrar?: (filtros: {
    busqueda?: string;
    estado?: string;
    modo?: string;
    mecanico_id?: string;
    limite?: number;
    offset?: number;
    fecha_desde?: string;
    fecha_hasta?: string;
  }) => Promise<void>;
  refreshKey?: number;
  periodoExterno?: Periodo;
}

export function useDiagnosticosFilter({
  totalDiagnosticos,
  mecanicos,
  initialFiltroMecanico,
  onFiltrar,
  refreshKey = 0,
  periodoExterno,
}: UseDiagnosticosFilterProps) {
  const [filtros, setFiltros] = useState({
    busqueda: '',
    estado: '',
    mecanico: initialFiltroMecanico || 'todos',
    pagina: 1,
  });
  const [periodoInterno, setPeriodo] = useState<Periodo>({});
  const periodo = periodoExterno || periodoInterno;
  const [rangoFechas, setRangoFechas] = useState<Periodo>(periodo);
  const [mostrarRangoFechas, setMostrarRangoFechas] = useState(false);

  useEffect(() => {
    if (initialFiltroMecanico !== undefined) {
      setFiltros((f) => ({ ...f, mecanico: initialFiltroMecanico, pagina: 1 }));
    }
  }, [initialFiltroMecanico]);

  useEffect(() => {
    setFiltros((f) => ({ ...f, pagina: 1 }));
  }, [periodo]);

  useEffect(() => {
    const timer = setTimeout(() => {
      void onFiltrar?.({
        busqueda: filtros.busqueda.trim() || undefined,
        estado: filtros.estado || undefined,
        mecanico_id: filtros.mecanico !== 'todos' ? filtros.mecanico : undefined,
        limite: 10,
        offset: (filtros.pagina - 1) * 10,
        ...limitesDiagnosticos(periodo),
      });
    }, 300);
    return () => clearTimeout(timer);
  }, [filtros, periodo, refreshKey, onFiltrar]);

  const totalPaginas = Math.max(1, Math.ceil(totalDiagnosticos / 10));

  const mecanicoSeleccionado = useMemo(() => {
    if (!filtros.mecanico || filtros.mecanico === 'todos') return null;
    return mecanicos.find((m) => m.id === filtros.mecanico) || null;
  }, [filtros.mecanico, mecanicos]);

  const seleccionarPresetPeriodo = (dias?: number) => {
    if (!dias) {
      setPeriodo({});
      setRangoFechas({});
      setMostrarRangoFechas(false);
    } else {
      const p = periodoDias(dias);
      setPeriodo(p);
      setRangoFechas(p);
      setMostrarRangoFechas(false);
    }
  };

  const fechaInvalida = Boolean(
    rangoFechas.fecha_desde &&
    rangoFechas.fecha_hasta &&
    rangoFechas.fecha_desde > rangoFechas.fecha_hasta
  );

  const aplicarRangoPersonalizado = () => {
    if (!fechaInvalida) {
      setPeriodo(rangoFechas);
    }
  };

  return {
    filtros,
    setFiltros,
    periodo,
    rangoFechas,
    setRangoFechas,
    mostrarRangoFechas,
    setMostrarRangoFechas,
    totalPaginas,
    mecanicoSeleccionado,
    seleccionarPresetPeriodo,
    fechaInvalida,
    aplicarRangoPersonalizado,
  };
}
