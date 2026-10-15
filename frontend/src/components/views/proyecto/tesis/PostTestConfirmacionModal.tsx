import React, { useEffect, useState } from 'react';
import { Modal } from '../../../common/Modal';
import { Button } from '../../../common/Button';
import { Input } from '../../../common/Input';
import type { CasoValidacionDTO, ConfirmacionPostTestInput } from '../../../../types/api';

export const PostTestConfirmacionModal: React.FC<{
  caso: CasoValidacionDTO | null;
  onClose: () => void;
  onConfirmar: (datos: ConfirmacionPostTestInput) => Promise<void>;
}> = ({ caso, onClose, onConfirmar }) => {
  const casoId = caso?.id;
  const sistemaInicial = caso?.sistema_afectado_probable;
  const anioInicial = caso?.vehiculo_anio;
  const kilometrajeInicial = caso?.vehiculo_kilometraje;
  const combustibleInicial = caso?.vehiculo_combustible;
  const transmisionInicial = caso?.vehiculo_transmision;
  const [falla, setFalla] = useState(''); const [minutos, setMinutos] = useState('');
  const [metodo, setMetodo] = useState(''); const [correcta, setCorrecta] = useState<0 | 1 | null>(null);
  const [evidenciaRef, setEvidenciaRef] = useState('');
  const [sistema, setSistema] = useState('');
  const [anio, setAnio] = useState(''); const [kilometraje, setKilometraje] = useState('');
  const [combustible, setCombustible] = useState(''); const [transmision, setTransmision] = useState('');
  const [guardando, setGuardando] = useState(false); const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!casoId) return;
    setFalla(''); setMinutos(''); setMetodo(''); setCorrecta(null); setEvidenciaRef('');
    setSistema(sistemaInicial || '');
    setAnio(anioInicial?.toString() || '');
    setKilometraje(kilometrajeInicial?.toString() || '');
    setCombustible(combustibleInicial || '');
    setTransmision(transmisionInicial || '');
  }, [casoId, sistemaInicial, anioInicial, kilometrajeInicial, combustibleInicial, transmisionInicial]);
  if (!caso) return null;
  const enviar = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!falla.trim() || !metodo.trim() || !evidenciaRef.trim() || !minutos || correcta === null) {
      setError('Complete la falla, el tiempo, el método, la referencia revisada y el resultado de la comparación.');
      return;
    }
    setGuardando(true); setError(null);
    try {
      await onConfirmar({
        falla_real: falla.trim(), tiempo_diagnostico_minutos: Number(minutos),
        prediccion_correcta: correcta, metodo_confirmacion: metodo.trim(), evidencia_ref: evidenciaRef.trim(),
        ...(sistema.trim() ? { sistema_afectado_probable: sistema.trim() } : {}),
        ...(anio ? { vehiculo_anio: Number(anio) } : {}),
        ...(kilometraje ? { vehiculo_kilometraje: Number(kilometraje) } : {}),
        ...(combustible.trim() ? { vehiculo_combustible: combustible.trim() } : {}),
        ...(transmision.trim() ? { vehiculo_transmision: transmision.trim() } : {}),
      });
    }
    catch (err) { setError(err instanceof Error ? err.message : 'No se pudo confirmar.'); }
    finally { setGuardando(false); }
  };
  return (
    <Modal isOpen onClose={onClose} title="Confirmar diagnóstico POST-TEST" maxWidth="680px">
      <form onSubmit={enviar} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <p style={{ margin: 0, fontSize: 12, color: 'var(--text-secondary)' }}>
          BORRADOR · {caso.placa_enmascarada}. La predicción original se conserva sin cambios.
          Registra la falla solo después de la comprobación humana.
        </p>
        {error && <div className="inline-error">{error}</div>}
        <Input required value={falla} onChange={(e) => setFalla(e.target.value)} placeholder="Falla confirmada por el mecánico" />
        <Input required type="number" min="1" max="600" value={minutos} onChange={(e) => setMinutos(e.target.value)} placeholder="Tiempo de diagnóstico (minutos)" />
        <Input value={sistema} onChange={(e) => setSistema(e.target.value)} placeholder="Sistema afectado probable, si está identificado" />
        <Input required value={metodo} onChange={(e) => setMetodo(e.target.value)} placeholder="Método de comprobación realizado" />
        <Input required value={evidenciaRef} onChange={(e) => setEvidenciaRef(e.target.value)} placeholder="Referencia del soporte que revisaste (OT, foto, medición)" />
        <small style={{ color: 'var(--text-secondary)' }}>
          La referencia localiza el soporte; por sí sola no demuestra una comprobación física.
        </small>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 8 }}>
          <Input type="number" min="1950" max="2100" value={anio} onChange={(e) => setAnio(e.target.value)} placeholder="Año del vehículo (si se conoce)" />
          <Input type="number" min="0" value={kilometraje} onChange={(e) => setKilometraje(e.target.value)} placeholder="Kilometraje (si se conoce)" />
          <Input value={combustible} onChange={(e) => setCombustible(e.target.value)} placeholder="Combustible (si se conoce)" />
          <Input value={transmision} onChange={(e) => setTransmision(e.target.value)} placeholder="Transmisión (si se conoce)" />
        </div>
        <div>
          <strong style={{ fontSize: 12 }}>¿La predicción original de CarBot coincidió con la falla confirmada?</strong>
          <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
            {([['SÍ', 1], ['NO', 0]] as const).map(([etiqueta, valor]) => (
              <button key={etiqueta} type="button" onClick={() => setCorrecta(valor)} style={{
                padding: '8px 16px', borderRadius: 6, cursor: 'pointer',
                border: correcta === valor ? '2px solid var(--primary)' : '1px solid var(--border-color)',
                background: correcta === valor ? '#fff7ed' : '#fff',
              }}>{etiqueta}</button>
            ))}
          </div>
        </div>
        <Button type="submit" disabled={guardando}>{guardando ? 'Guardando...' : 'Guardar revisión humana'}</Button>
      </form>
    </Modal>
  );
};
