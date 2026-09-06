import { useState } from 'react';
import { periodoDias, type Periodo } from '../../utils/periodo';

export function PeriodoFilter({ value, onChange }: { value: Periodo; onChange: (p: Periodo) => void }) {
  const [rango, setRango] = useState(value);
  const invalido = Boolean(rango.fecha_desde && rango.fecha_hasta && rango.fecha_desde > rango.fecha_hasta);
  const seleccionar = (p: Periodo) => { setRango(p); onChange(p); };
  return <div className="periodo-filter" aria-label="Período de consulta">
    {[7, 14].map(dias => {
      const p = periodoDias(dias);
      return <button type="button" key={dias}
        aria-pressed={value.fecha_desde === p.fecha_desde && value.fecha_hasta === p.fecha_hasta}
        onClick={() => seleccionar(p)}>Últimos {dias} días</button>;
    })}
    <button type="button" aria-pressed={!value.fecha_desde && !value.fecha_hasta}
      onClick={() => seleccionar({})}>Todo</button>
    <label>Desde <input type="date" value={rango.fecha_desde || ''}
      onChange={e => setRango({ ...rango, fecha_desde: e.target.value || undefined })} /></label>
    <label>Hasta <input type="date" value={rango.fecha_hasta || ''}
      onChange={e => setRango({ ...rango, fecha_hasta: e.target.value || undefined })} /></label>
    <button type="button" disabled={invalido} onClick={() => onChange(rango)}>Aplicar</button>
    {invalido && <span role="alert">Revisa el orden de las fechas.</span>}
  </div>;
}
