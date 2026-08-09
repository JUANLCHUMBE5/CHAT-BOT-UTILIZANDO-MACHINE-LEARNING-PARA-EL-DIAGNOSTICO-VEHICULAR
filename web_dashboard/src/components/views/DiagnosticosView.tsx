import React, { useState } from 'react';
import { Search, FileText, Clock, Cpu } from 'lucide-react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { Modal } from '../common/Modal';
import type { Diagnostico, EstadoDiagnostico, Mecanico } from '../../types';

interface DiagnosticosViewProps {
  diagnosticos: Diagnostico[];
  mecanicos: Mecanico[];
  onActualizarEstado: (id: string, nuevoEstado: EstadoDiagnostico, notas?: string) => Promise<void>;
  onFiltrar?: (filtros: { busqueda?: string; estado?: string; modo?: string; mecanico_id?: string }) => Promise<void>;
  diagnosticoSeleccionadoModal?: Diagnostico | null;
  onCerrarModalDetalle: () => void;
  onAbrirModalDetalle: (diag: Diagnostico) => void;
}

export const DiagnosticosView: React.FC<DiagnosticosViewProps> = ({
  diagnosticos,
  mecanicos,
  onActualizarEstado,
  onFiltrar,
  diagnosticoSeleccionadoModal,
  onCerrarModalDetalle,
  onAbrirModalDetalle,
}) => {
  // Filter States
  const [busqueda, setBusqueda] = useState('');
  const [filtroEstado, setFiltroEstado] = useState('todos');
  const [filtroModo, setFiltroModo] = useState('todos');
  const [filtroMecanico, setFiltroMecanico] = useState('todos');

  // Trigger backend filtering with 300ms debounce on search
  React.useEffect(() => {
    const timer = setTimeout(() => {
      if (onFiltrar) {
        onFiltrar({
          busqueda: busqueda.trim() || undefined,
          estado: filtroEstado !== 'todos' ? filtroEstado : undefined,
          modo: filtroModo !== 'todos' ? filtroModo : undefined,
          mecanico_id: filtroMecanico !== 'todos' ? filtroMecanico : undefined,
        });
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [busqueda, filtroEstado, filtroModo, filtroMecanico, onFiltrar]);

  // Confirmation Form State inside Detail Modal
  const [nuevoEstado, setNuevoEstado] = useState<EstadoDiagnostico>('confirmado');
  const [notasMecanico, setNotasMecanico] = useState('');
  const [guardando, setGuardando] = useState(false);
  const [errorGuardado, setErrorGuardado] = useState('');

  // Render backend-filtered list directly
  const diagnosticosFiltrados = diagnosticos;

  const handleGuardarConfirmacion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!diagnosticoSeleccionadoModal) return;

    setGuardando(true);
    setErrorGuardado('');
    try {
      await onActualizarEstado(diagnosticoSeleccionadoModal.id, nuevoEstado, notasMecanico);
      onCerrarModalDetalle();
    } catch (err: unknown) {
      setErrorGuardado(err instanceof Error ? err.message : 'No se pudo guardar la confirmación.');
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div>
        <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-main)' }}>
          Historial y Confirmación de Diagnósticos
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Filtra, revisa las 3 secciones generadas por ML+RAG y confirma los diagnósticos mecánicos.
        </p>
      </div>

      {/* Filter Panel */}
      <Card style={{ padding: '16px' }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '12px',
          }}
        >
          <Input
            placeholder="Buscar por placa, síntoma o falla..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            icon={<Search size={18} />}
          />

          <Select
            value={filtroEstado}
            onChange={(e) => setFiltroEstado(e.target.value)}
            options={[
              { value: 'todos', label: 'Todos los estados' },
              { value: 'generado', label: 'Estado: Generado' },
              { value: 'en_revision', label: 'Estado: En Revisión' },
              { value: 'confirmado', label: 'Estado: Confirmado' },
              { value: 'descartado', label: 'Estado: Descartado' },
            ]}
          />

          <Select
            value={filtroModo}
            onChange={(e) => setFiltroModo(e.target.value)}
            options={[
              { value: 'todos', label: 'Todos los modos' },
              { value: 'completo_ml_rag_llm', label: 'Modo: ML + RAG + LLM' },
              { value: 'diagnostico_degradado_ml_rag', label: 'Modo: Degradado (ML+RAG)' },
              { value: 'saludo', label: 'Modo: Saludo / Regla' },
            ]}
          />

          <Select
            value={filtroMecanico}
            onChange={(e) => setFiltroMecanico(e.target.value)}
            options={[
              { value: 'todos', label: 'Todos los mecánicos' },
              ...mecanicos.map((m) => ({ value: m.id, label: m.nombres })),
            ]}
          />
        </div>
      </Card>

      {/* Diagnostics Table */}
      <Card style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr
                style={{
                  backgroundColor: 'var(--bg-subtle)',
                  borderBottom: '1px solid var(--border-color)',
                  fontSize: '12px',
                  fontWeight: 600,
                  color: 'var(--text-secondary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                <th style={{ padding: '12px 16px' }}>Placa / Vehículo</th>
                <th style={{ padding: '12px 16px' }}>Síntoma del Cliente</th>
                <th style={{ padding: '12px 16px' }}>Falla Predicha (ML)</th>
                <th style={{ padding: '12px 16px' }}>Confianza</th>
                <th style={{ padding: '12px 16px' }}>Modo</th>
                <th style={{ padding: '12px 16px' }}>Estado</th>
                <th style={{ padding: '12px 16px', textAlign: 'right' }}>Detalle</th>
              </tr>
            </thead>
            <tbody>
              {diagnosticosFiltrados.map((d) => (
                <tr
                  key={d.id}
                  style={{
                    borderBottom: '1px solid var(--border-color)',
                    fontSize: '14px',
                    backgroundColor: '#ffffff',
                  }}
                >
                  <td style={{ padding: '14px 16px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontWeight: 700, color: 'var(--primary)' }}>
                        {d.placa_vehiculo}
                      </span>
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                        {d.marca_modelo}
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '14px 16px', maxWidth: '240px', color: 'var(--text-main)' }}>
                    <p style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      "{d.sintoma_original}"
                    </p>
                  </td>
                  <td style={{ padding: '14px 16px', fontWeight: 600, color: 'var(--text-main)' }}>
                    {d.falla_predicha}
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{ fontWeight: 700, color: d.confianza >= 85 ? 'var(--status-success-text)' : 'var(--status-warning-text)' }}>
                      {d.confianza}%
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <Badge type={d.modo_diagnostico} size="sm" />
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <Badge type={d.estado} />
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setNuevoEstado(d.estado);
                        setNotasMecanico(d.notas_mecanico || '');
                        onAbrirModalDetalle(d);
                      }}
                    >
                      Ver / Confirmar
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Modal Detail & Mechanic Confirmation */}
      {diagnosticoSeleccionadoModal && (
        <Modal
          isOpen={!!diagnosticoSeleccionadoModal}
          onClose={onCerrarModalDetalle}
          title={`Diagnóstico Técnico — Placa ${diagnosticoSeleccionadoModal.placa_vehiculo}`}
          maxWidth="680px"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Meta header */}
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                backgroundColor: 'var(--primary-light)',
                borderRadius: '8px',
                border: '1px solid var(--primary-border)',
                gap: '10px',
              }}
            >
              <div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Mecánico Atendiendo:</span>
                <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)' }}>
                  {diagnosticoSeleccionadoModal.mecanico_nombre}
                </p>
              </div>
              <div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Fecha y Hora:</span>
                <p style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-main)' }}>
                  {diagnosticoSeleccionadoModal.fecha_hora}
                </p>
              </div>
              <div>
                <Badge type={diagnosticoSeleccionadoModal.estado} />
              </div>
            </div>

            {/* Sintoma original */}
            <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '12px 16px', borderRadius: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Síntoma reportado por el cliente en WhatsApp:
              </span>
              <p style={{ fontSize: '14px', fontStyle: 'italic', color: 'var(--text-main)', marginTop: '4px' }}>
                "{diagnosticoSeleccionadoModal.sintoma_original}"
              </p>
            </div>

            {/* Section 1: Posible Falla ML */}
            <div style={{ border: '1px solid var(--border-color)', borderRadius: '10px', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <Cpu size={18} color="var(--primary)" />
                <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)' }}>
                  🛠️ 1. Posible Falla Vehicular (Machine Learning)
                </h4>
              </div>
              <p style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-main)' }}>
                {diagnosticoSeleccionadoModal.falla_predicha}
              </p>
              <div style={{ display: 'flex', gap: '16px', marginTop: '6px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                <span>Certeza del modelo: <strong>{diagnosticoSeleccionadoModal.confianza}%</strong></span>
                <span>Fuente de inferencia: <strong>{diagnosticoSeleccionadoModal.fuente.toUpperCase()}</strong></span>
              </div>
            </div>

            {/* Section 2: Procedimiento RAG */}
            <div style={{ border: '1px solid var(--border-color)', borderRadius: '10px', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <FileText size={18} color="var(--primary)" />
                  <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)' }}>
                    📖 2. Procedimiento Técnico de Reparación (RAG Manuales)
                  </h4>
                </div>
                {diagnosticoSeleccionadoModal.similitud_rag !== undefined && (
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    Similitud RAG: <strong>{diagnosticoSeleccionadoModal.similitud_rag}%</strong>
                  </span>
                )}
              </div>
              {diagnosticoSeleccionadoModal.fuente_manual && (
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px', fontStyle: 'italic' }}>
                  Referencia: {diagnosticoSeleccionadoModal.fuente_manual}
                </div>
              )}
              <pre
                style={{
                  fontSize: '13px',
                  fontFamily: 'inherit',
                  whiteSpace: 'pre-wrap',
                  backgroundColor: 'var(--bg-subtle)',
                  padding: '12px',
                  borderRadius: '6px',
                  color: 'var(--text-main)',
                  lineHeight: 1.5,
                }}
              >
                {diagnosticoSeleccionadoModal.procedimiento_rag}
              </pre>
            </div>

            {/* Section 3: Tiempo & Gravedad */}
            <div style={{ border: '1px solid var(--border-color)', borderRadius: '10px', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <Clock size={18} color="var(--primary)" />
                <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)' }}>
                  ⏱️ 3. Tiempo Estimado y Gravedad
                </h4>
              </div>
              <pre
                style={{
                  fontSize: '13px',
                  fontFamily: 'inherit',
                  whiteSpace: 'pre-wrap',
                  color: 'var(--text-secondary)',
                }}
              >
                {diagnosticoSeleccionadoModal.tiempo_gravedad}
              </pre>
            </div>

            {/* Análisis completo generado por Gemini; WhatsApp recibe solo el resumen. */}
            {diagnosticoSeleccionadoModal.sintesis_llm && (
              <div style={{ border: '1px solid var(--border-color)', borderRadius: '10px', padding: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <FileText size={18} color="var(--primary)" />
                  <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)' }}>
                    Análisis completo ML + RAG + Gemini
                  </h4>
                </div>
                <pre style={{ fontSize: '13px', fontFamily: 'inherit', whiteSpace: 'pre-wrap', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  {diagnosticoSeleccionadoModal.sintesis_llm}
                </pre>
              </div>
            )}

            {/* Formulario de Confirmación del Mecánico */}
            <form
              onSubmit={handleGuardarConfirmacion}
              style={{
                backgroundColor: '#fff7ed',
                border: '1px solid #ffedd5',
                borderRadius: '10px',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px',
              }}
            >
              {errorGuardado && (
                <div style={{ padding: '10px', borderRadius: '6px', backgroundColor: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', fontSize: '13px' }}>
                  {errorGuardado}
                </div>
              )}
              <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--primary)' }}>
                ✍️ Validar / Confirmar Diagnóstico Mecánico
              </h4>

              <Select
                label="Estado de Validación por el Mecánico"
                value={nuevoEstado}
                onChange={(e) => setNuevoEstado(e.target.value as EstadoDiagnostico)}
                options={[
                  { value: 'confirmado', label: '✅ Confirmado (Falla verificada físicamente)' },
                  { value: 'en_revision', label: '⏳ En Revisión (Desmontando componentes)' },
                  { value: 'descartado', label: '❌ Descartado (Falla fue diferente a la predicha)' },
                ]}
              />

              <Input
                label="Notas del Mecánico en Taller"
                placeholder="Ej. Se verificó con escáner OBD-II y pastillas cambiadas."
                value={notasMecanico}
                onChange={(e) => setNotasMecanico(e.target.value)}
              />

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <Button type="button" variant="secondary" onClick={onCerrarModalDetalle}>
                  Cancelar
                </Button>
                <Button type="submit" variant="primary" disabled={guardando}>
                  {guardando ? 'Guardando...' : 'Guardar Confirmación'}
                </Button>
              </div>
            </form>
          </div>
        </Modal>
      )}
    </div>
  );
};
