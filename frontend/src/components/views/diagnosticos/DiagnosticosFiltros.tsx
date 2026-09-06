import React from 'react';
import { Search } from 'lucide-react';
import { Card } from '../../common/Card';
import { Input } from '../../common/Input';
import { Select } from '../../common/Select';
import type { Mecanico } from '../../../types';

export type FiltroFecha = 'todos' | 'hoy' | '7dias' | 'esteMes';

interface DiagnosticosFiltrosProps {
  busqueda: string;
  onBusquedaChange: (val: string) => void;
  filtroEstado: string;
  onFiltroEstadoChange: (val: string) => void;
  filtroMecanico?: string;
  onFiltroMecanicoChange?: (val: string) => void;
  mecanicos?: Mecanico[];
  filtroFecha: FiltroFecha;
  onFiltroFechaChange: (val: FiltroFecha) => void;
}

export const DiagnosticosFiltros: React.FC<DiagnosticosFiltrosProps> = ({
  busqueda,
  onBusquedaChange,
  filtroEstado,
  onFiltroEstadoChange,
  filtroMecanico = 'todos',
  onFiltroMecanicoChange,
  mecanicos = [],
  filtroFecha,
  onFiltroFechaChange,
}) => {
  const opcionesMecanicos = [
    { value: 'todos', label: 'Todos los mecánicos' },
    ...mecanicos.map((m) => ({
      value: m.id,
      label: `Mecánico: ${m.nombres}`,
    })),
  ];

  return (
    <Card style={{ padding: '8px 10px' }}>
      <div className="diagnosticos-filtros-grid">
        <div className="diagnosticos-filtros-search">
          <Input
            placeholder="Buscar por síntoma, falla, placa o mecánico..."
            value={busqueda}
            onChange={(e) => onBusquedaChange(e.target.value)}
            icon={<Search size={14} />}
          />
        </div>

        <Select
          value={filtroEstado}
          onChange={(e) => onFiltroEstadoChange(e.target.value)}
          options={[
            { value: 'todos', label: 'Todos estados' },
            { value: 'generado', label: 'Generado' },
            { value: 'en_revision', label: 'En Revisión' },
            { value: 'confirmado', label: 'Confirmado' },
            { value: 'descartado', label: 'Descartado' },
          ]}
        />

        {onFiltroMecanicoChange && (
          <Select
            value={filtroMecanico}
            onChange={(e) => onFiltroMecanicoChange(e.target.value)}
            options={opcionesMecanicos}
          />
        )}

        <Select
          value={filtroFecha}
          onChange={(e) => onFiltroFechaChange(e.target.value as FiltroFecha)}
          options={[
            { value: 'todos', label: 'Periodo: Todo' },
            { value: 'hoy', label: 'Hoy' },
            { value: '7dias', label: 'Últimos 7 días' },
            { value: 'esteMes', label: 'Este mes' },
          ]}
        />
      </div>
    </Card>
  );
};
