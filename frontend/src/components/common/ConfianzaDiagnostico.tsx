import type { Diagnostico } from '../../types/domain';
import { presentarConfianzaDiagnostico } from '../../utils/prediccionPresentation';

export function ConfianzaDiagnostico({ diagnostico }: { diagnostico: Diagnostico }) {
  const dato = presentarConfianzaDiagnostico(diagnostico);
  return (
    <span title={dato.titulo} style={{ fontSize: '11px', fontWeight: 700, padding: '2px 7px',
      borderRadius: '6px', display: 'inline-block', color: '#334155', background: '#f1f5f9' }}>
      {dato.etiqueta}
    </span>
  );
}
