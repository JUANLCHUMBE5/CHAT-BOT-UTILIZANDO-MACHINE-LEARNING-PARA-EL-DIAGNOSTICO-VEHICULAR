import { useState } from 'react';
import { ValidacionTallerView } from '../ValidacionTallerView';
import { ConsultasTesisView } from './tesis/ConsultasTesisView';

export const TesisValidacionTab = () => {
  const [vista, setVista] = useState<'fichas' | 'consultas'>('fichas');
  return <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr)', gap: 16 }}>
    <div className="periodo-filter">
      <button type="button" aria-pressed={vista === 'fichas'} onClick={() => setVista('fichas')}>
        Fichas de Taller (Variable Dependiente)
      </button>
      <button type="button" aria-pressed={vista === 'consultas'} onClick={() => setVista('consultas')}>
        Desempeño de CarBot (Variable Independiente)
      </button>
    </div>
    {vista === 'fichas' ? <ValidacionTallerView /> : <ConsultasTesisView />}
  </div>;
};
