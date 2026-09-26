import React, { useState } from 'react';
import { Modal } from '../../../common/Modal';
import { Button } from '../../../common/Button';
import { Input } from '../../../common/Input';
import type { CasoValidacionDTO } from '../../../../types/api';

export const PostTestConfirmacionModal: React.FC<{ caso: CasoValidacionDTO | null; onClose: () => void; onConfirmar: (datos: { falla_real: string; tiempo_diagnostico_minutos: number; prediccion_correcta: 0 | 1; metodo_confirmacion: string }) => Promise<void> }> = ({ caso, onClose, onConfirmar }) => {
  const [falla, setFalla] = useState(''); const [minutos, setMinutos] = useState('');
  const [metodo, setMetodo] = useState(''); const [correcta, setCorrecta] = useState<0 | 1 | null>(null);
  const [guardando, setGuardando] = useState(false); const [error, setError] = useState<string | null>(null);
  if (!caso) return null;
  const enviar = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!falla.trim() || !metodo.trim() || !minutos || correcta === null) { setError('Complete todos los campos y seleccione Sí o No.'); return; }
    setGuardando(true); setError(null);
    try { await onConfirmar({ falla_real: falla, tiempo_diagnostico_minutos: Number(minutos), prediccion_correcta: correcta, metodo_confirmacion: metodo }); }
    catch (err) { setError(err instanceof Error ? err.message : 'No se pudo confirmar.'); }
    finally { setGuardando(false); }
  };
  return <Modal isOpen onClose={onClose} title="Confirmar diagnóstico POST-TEST" maxWidth="560px"><form onSubmit={enviar} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
    <p style={{ margin: 0, fontSize: 12, color: 'var(--text-secondary)' }}>BORRADOR · {caso.placa_enmascarada}. La predicción no se marca automáticamente.</p>
    {error && <div className="inline-error">{error}</div>}
    <Input required value={falla} onChange={(e) => setFalla(e.target.value)} placeholder="Falla real o diagnóstico confirmado" />
    <Input required type="number" min="1" max="600" value={minutos} onChange={(e) => setMinutos(e.target.value)} placeholder="Tiempo de diagnóstico (minutos)" />
    <Input required value={metodo} onChange={(e) => setMetodo(e.target.value)} placeholder="Método o evidencia de confirmación" />
    <div><strong style={{ fontSize: 12 }}>¿La predicción de CarBot fue correcta?</strong><div style={{ display: 'flex', gap: 8, marginTop: 6 }}>{([['SÍ', 1], ['NO', 0]] as const).map(([etiqueta, valor]) => <button key={etiqueta} type="button" onClick={() => setCorrecta(valor)} style={{ padding: '8px 16px', borderRadius: 6, cursor: 'pointer', border: correcta === valor ? '2px solid var(--primary)' : '1px solid var(--border-color)', background: correcta === valor ? '#fff7ed' : '#fff' }}>{etiqueta}</button>)}</div></div>
    <Button type="submit" disabled={guardando}>{guardando ? 'Guardando...' : 'Confirmar diagnóstico'}</Button>
  </form></Modal>;
};
