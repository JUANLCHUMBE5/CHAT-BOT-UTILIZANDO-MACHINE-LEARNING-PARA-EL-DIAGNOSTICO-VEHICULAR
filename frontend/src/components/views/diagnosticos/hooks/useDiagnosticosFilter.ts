import { useState, useEffect, useMemo } from 'react';
import type { Mecanico } from '../../../../types';
import { limitesDiagnosticos, periodoDias, type Periodo } from '../../../../utils/periodo';

export interface UseDiagnosticosFilterProps {
  totalDiagnosticos: number;
  mecanicos: Mecanico[];
  initialFiltroMecanico?: string;
  initialLimite?: number;
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

export interface FiltrosDiagnosticosState {
  busqueda: string;
  estado: string;
  mecanico: string;
  pagina: number;
  limite: number;
}

export function useDiagnosticosFilter({
  totalDiagnosticos,
  mecanicos,
  initialFiltroMecanico,
  initialLimite = 10,
  onFiltrar,
  refreshKey = 0,
  periodoExterno,
}: UseDiagnosticosFilterProps) {
  const limiteInicial = [10, 20, 50].includes(initialLimite) ? initialLimite : 10;

  const [filtros, setFiltros] = useState<FiltrosDiagnosticosState>({
    busqueda: '',
    estado: '',
    mecanico: initialFiltroMecanico || 'todos',
    pagina: 1,
    limite: limiteInicial,
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
      const lim = filtros.limite || 10;
      void onFiltrar?.({
        busqueda: filtros.busqueda.trim() || undefined,
        estado: filtros.estado || undefined,
        mecanico_id: filtros.mecanico !== 'todos' ? filtros.mecanico : undefined,
        limite: lim,
        offset: (filtros.pagina - 1) * lim,
        ...limitesDiagnosticos(periodo),
      });
    }, 300);
    return () => clearTimeout(timer);
  }, [filtros, periodo, refreshKey, onFiltrar]);

  const totalPaginas = Math.max(1, Math.ceil(totalDiagnosticos / (filtros.limite || 10)));

  const cambiarLimite = (nuevoLimite: number) => {
    const lim = [10, 20, 50].includes(nuevoLimite) ? nuevoLimite : 10;
    setFiltros((f) => ({
      ...f,
      limite: lim,
      pagina: 1,
    }));
  };

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
    cambiarLimite,
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
