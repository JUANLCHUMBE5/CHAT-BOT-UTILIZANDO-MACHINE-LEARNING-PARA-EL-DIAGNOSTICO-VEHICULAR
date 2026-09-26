import React, { useState } from 'react';
import { Bot, Link, Lock } from 'lucide-react';
import { Modal } from '../../common/Modal';
import { Button } from '../../common/Button';
import { Input } from '../../common/Input';
import { Select } from '../../common/Select';
import type { CrearCasoValidacionDTO, TipoRegistro } from '../../../types/api';
import type { Diagnostico } from '../../../types';
import { VincularDiagnosticoSelector } from './modal/VincularDiagnosticoSelector';
import { ConfirmacionOficialModal } from './modal/ConfirmacionOficialModal';

interface ValidacionNuevoCasoModalProps {
  isOpen: boolean;
  onClose: () => void;
  nuevoCaso: CrearCasoValidacionDTO;
  onNuevoCasoChange: (updater: (prev: CrearCasoValidacionDTO) => CrearCasoValidacionDTO) => void;
  guardando: boolean;
  onSubmit: (e: React.FormEvent) => Promise<void>;
}

type EntornoSeleccionado = 'DESARROLLO' | 'PILOTO' | 'OFICIAL';

export const ValidacionNuevoCasoModal: React.FC<ValidacionNuevoCasoModalProps> = ({
  isOpen,
  onClose,
  nuevoCaso,
  onNuevoCasoChange,
  guardando,
  onSubmit,
}) => {
  const [selectorDiagAbierto, setSelectorDiagAbierto] = useState(false);
  const [confirmacionOficialAbierta, setConfirmacionOficialAbierta] = useState(false);

  // Mapeo bidireccional del entorno
  const obtenerEntornoActual = (): EntornoSeleccionado => {
    if (nuevoCaso.tipo_registro === 'THESIS_PRETEST' || nuevoCaso.tipo_registro === 'THESIS_POSTTEST') {
      return 'OFICIAL';
    }
    if (nuevoCaso.tipo_registro === 'PILOT') {
      return 'PILOTO';
    }
    return 'DESARROLLO';
  };

  const entorno = obtenerEntornoActual();

  const handleCambioEntorno = (nuevoEntorno: EntornoSeleccionado) => {
    let tr: TipoRegistro = 'DEVELOPMENT';
    if (nuevoEntorno === 'PILOTO') {
      tr = 'PILOT';
    } else if (nuevoEntorno === 'OFICIAL') {
      tr = nuevoCaso.fase === 'Pre-test' ? 'THESIS_PRETEST' : 'THESIS_POSTTEST';
    }
    onNuevoCasoChange((prev) => ({
      ...prev,
      tipo_registro: tr,
      estado_registro: nuevoEntorno === 'OFICIAL' ? 'verificado' : 'borrador',
    }));
  };

  const handleCambioFase = (nuevaFase: 'Pre-test' | 'Post-test') => {
    let tr: TipoRegistro = nuevoCaso.tipo_registro || 'DEVELOPMENT';
    if (entorno === 'OFICIAL') {
      tr = nuevaFase === 'Pre-test' ? 'THESIS_PRETEST' : 'THESIS_POSTTEST';
    }
    onNuevoCasoChange((prev) => ({
      ...prev,
      fase: nuevaFase,
      tipo_registro: tr,
      diagnostico_id: nuevaFase === 'Pre-test' ? null : prev.diagnostico_id,
      conversacion_id: nuevaFase === 'Pre-test' ? null : prev.conversacion_id,
    }));
  };

  const handleVincularDiagnostico = (d: Diagnostico) => {
    onNuevoCasoChange((prev) => ({
      ...prev,
      diagnostico_id: d.id,
      conversacion_id: d.conversacion_id || null,
      fase: 'Post-test',
      tipo_registro: entorno === 'OFICIAL' ? 'THESIS_POSTTEST' : prev.tipo_registro,
      sintoma: d.sintoma_original || prev.sintoma,
      chatbot_prediccion: d.falla_predicha || prev.chatbot_prediccion,
      sistema_afectado_probable: d.falla_predicha || prev.sistema_afectado_probable,
      tiempo_inferencia_ml_ms: d.duracion_ms || undefined,
      placa: d.placa_vehiculo && !d.placa_vehiculo.toLowerCase().includes('sin placa') ? d.placa_vehiculo : prev.placa,
    }));
  };

  const handleDesvincularDiagnostico = () => {
    onNuevoCasoChange((prev) => ({
      ...prev,
      diagnostico_id: null,
      conversacion_id: null,
    }));
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (entorno === 'OFICIAL') {
      setConfirmacionOficialAbierta(true);
    } else {
      void onSubmit(e);
    }
  };

  const handleConfirmarOficial = () => {
    setConfirmacionOficialAbierta(false);
    const tr: TipoRegistro = nuevoCaso.fase === 'Pre-test' ? 'THESIS_PRETEST' : 'THESIS_POSTTEST';
    onNuevoCasoChange((prev) => ({ ...prev, tipo_registro: tr, estado_registro: 'verificado' }));
    const fakeEvent = { preventDefault: () => {} } as React.FormEvent;
    void onSubmit(fakeEvent);
  };

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose} title="Registrar Caso de Estudio Experimental" maxWidth="720px">
        <form onSubmit={handleFormSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* 1. SELECCIÓN EXPLÍCITA DE ENTORNO (BLINDAJE DE MUESTRA) */}
          <div style={{ backgroundColor: '#f8fafc', padding: '12px 14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--text-main)', marginBottom: '6px' }}>
              Entorno del Registro *
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
              <button
                type="button"
                onClick={() => handleCambioEntorno('DESARROLLO')}
                style={{
                  padding: '8px 10px',
                  borderRadius: '6px',
                  border: entorno === 'DESARROLLO' ? '2px solid #64748b' : '1px solid #cbd5e1',
                  backgroundColor: entorno === 'DESARROLLO' ? '#f1f5f9' : '#ffffff',
                  color: entorno === 'DESARROLLO' ? '#0f172a' : '#64748b',
                  fontSize: '11.5px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  textAlign: 'center',
                }}
              >
                DESARROLLO / PRUEBA
              </button>
              <button
                type="button"
                onClick={() => handleCambioEntorno('PILOTO')}
                style={{
                  padding: '8px 10px',
                  borderRadius: '6px',
                  border: entorno === 'PILOTO' ? '2px solid #d97706' : '1px solid #cbd5e1',
                  backgroundColor: entorno === 'PILOTO' ? '#fffbeb' : '#ffffff',
                  color: entorno === 'PILOTO' ? '#92400e' : '#64748b',
                  fontSize: '11.5px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  textAlign: 'center',
                }}
              >
                PILOTO (Presencial)
              </button>
              <button
                type="button"
                onClick={() => handleCambioEntorno('OFICIAL')}
                style={{
                  padding: '8px 10px',
                  borderRadius: '6px',
                  border: entorno === 'OFICIAL' ? '2px solid #dc2626' : '1px solid #cbd5e1',
                  backgroundColor: entorno === 'OFICIAL' ? '#fef2f2' : '#ffffff',
                  color: entorno === 'OFICIAL' ? '#991b1b' : '#64748b',
                  fontSize: '11.5px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  textAlign: 'center',
                }}
              >
                OFICIAL DE TESIS (N=60)
              </button>
            </div>
            <div style={{ fontSize: '11px', color: '#64748b', marginTop: '6px' }}>
              {entorno === 'DESARROLLO' && '✓ Excluido de métricas y muestra oficial (pruebas internas de sistema).'}
              {entorno === 'PILOTO' && '✓ Prueba piloto independiente. No computa en los 60 casos oficiales de la tesis.'}
              {entorno === 'OFICIAL' && '⚠️ Formará parte de la muestra de tesis. Requiere confirmación y verificación física.'}
            </div>
          </div>

          {/* 2. FASE DEL ESTUDIO Y FECHA */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                Fase Experimental *
              </label>
              <Select
                value={nuevoCaso.fase}
                onChange={(e) => handleCambioFase(e.target.value as 'Pre-test' | 'Post-test')}
                options={[
                  { value: 'Post-test', label: 'Post-test (Asistido por CarBot ML)' },
                  { value: 'Pre-test', label: 'Pre-test (Diagnóstico Tradicional)' },
                ]}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                Fecha de atención *
              </label>
              <Input
                type="date"
                value={nuevoCaso.fecha || ''}
                required
                onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, fecha: e.target.value }))}
              />
            </div>
          </div>

          {/* 3. VINCULACIÓN CON DIAGNÓSTICO CARBOT (EXCLUSIVO POST-TEST) */}
          {nuevoCaso.fase === 'Post-test' && (
            <div style={{ backgroundColor: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '8px', padding: '10px 12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Bot size={16} style={{ color: '#2563eb' }} />
                  <span style={{ fontSize: '12px', fontWeight: 700, color: '#1e40af' }}>
                    {nuevoCaso.diagnostico_id ? 'Diagnóstico CarBot Vinculado' : 'Asociar Consulta de CarBot'}
                  </span>
                </div>
                {nuevoCaso.diagnostico_id ? (
                  <button
                    type="button"
                    onClick={handleDesvincularDiagnostico}
                    style={{ fontSize: '11px', color: '#dc2626', border: 'none', background: 'none', cursor: 'pointer', fontWeight: 600 }}
                  >
                    ✕ Desvincular
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => setSelectorDiagAbierto(true)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '4px 10px',
                      backgroundColor: '#2563eb',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '5px',
                      fontSize: '11.5px',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    <Link size={13} />
                    <span>Seleccionar Diagnóstico</span>
                  </button>
                )}
              </div>
              {nuevoCaso.diagnostico_id && (
                <div style={{ fontSize: '11.5px', color: '#1e3a8a', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Lock size={12} style={{ color: '#2563eb' }} />
                  <span>ID: {nuevoCaso.diagnostico_id.slice(0, 13)}... · Predicción y telemetría bloqueadas para trazabilidad técnica.</span>
                </div>
              )}
            </div>
          )}

          {/* 4. DATOS DEL VEHÍCULO */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                Placa del Vehículo *
              </label>
              <Input
                placeholder="Ej. ABC-123"
                value={nuevoCaso.placa}
                onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, placa: e.target.value }))}
                required
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                Marca y Modelo *
              </label>
              <Input
                placeholder="Ej. Toyota Yaris"
                value={nuevoCaso.marca_modelo}
                required
                minLength={2}
                onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, marca_modelo: e.target.value }))}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '3px' }}>
                Año *
              </label>
              <Input
                type="number"
                min={1950}
                max={2100}
                placeholder="2018"
                value={nuevoCaso.vehiculo_anio ? String(nuevoCaso.vehiculo_anio) : ''}
                required
                onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, vehiculo_anio: e.target.value ? Number(e.target.value) : undefined }))}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '3px' }}>
                Kilometraje *
              </label>
              <Input
                type="number"
                min={0}
                placeholder="85000"
                value={nuevoCaso.vehiculo_kilometraje !== undefined ? String(nuevoCaso.vehiculo_kilometraje) : ''}
                required
                onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, vehiculo_kilometraje: e.target.value ? Number(e.target.value) : undefined }))}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '3px' }}>
                Combustible *
              </label>
              <Input
                placeholder="Gasolina"
                value={nuevoCaso.vehiculo_combustible || ''}
                required
                onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, vehiculo_combustible: e.target.value }))}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '3px' }}>
                Transmisión *
              </label>
              <Input
                placeholder="Mecánica"
                value={nuevoCaso.vehiculo_transmision || ''}
                required
                onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, vehiculo_transmision: e.target.value }))}
              />
            </div>
          </div>

          {/* 5. SÍNTOMAS */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
              Síntoma Reportado *
            </label>
            <Input
              placeholder="Ej. Motor tiembla en mínimo y aguja de RPM oscila"
              value={nuevoCaso.sintoma}
              onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, sintoma: e.target.value }))}
              required
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
              Descripción detallada del síntoma *
            </label>
            <Input
              placeholder="Ej. Al detenerse en semáforos, el motor pierde estabilidad y vibra; en alta marcha se normaliza"
              value={nuevoCaso.descripcion_sintoma || ''}
              onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, descripcion_sintoma: e.target.value }))}
              required
            />
          </div>

          {/* 6. DIAGNÓSTICO: PREDICCIÓN / HIPÓTESIS Y FALLA REAL */}
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                {nuevoCaso.fase === 'Pre-test'
                  ? 'Hipótesis Inicial (Diagnóstico Tradicional) *'
                  : nuevoCaso.diagnostico_id
                  ? 'Predicción CarBot (Inmutable) 🔒'
                  : 'Predicción CarBot *'}
              </label>
              <Input
                placeholder="Ej. Falla de Encendido en Cilindro Individual"
                value={nuevoCaso.chatbot_prediccion}
                readOnly={Boolean(nuevoCaso.diagnostico_id)}
                required
                onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, chatbot_prediccion: e.target.value }))}
                style={{ backgroundColor: nuevoCaso.diagnostico_id ? '#f1f5f9' : '#ffffff' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                Sistema Afectado Probable *
              </label>
              <Input
                placeholder="Ej. Motor / Frenos / Eléctrico"
                value={nuevoCaso.sistema_afectado_probable || ''}
                required
                onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, sistema_afectado_probable: e.target.value }))}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
              Falla Real Confirmada Físicamente en Taller *
            </label>
            <Input
              placeholder="Ej. Falla de Encendido en Cilindro Individual (Bobina N°2 quemada)"
              value={nuevoCaso.falla_real}
              onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, falla_real: e.target.value }))}
              required
            />
          </div>

          {/* 7. EVALUACIÓN DE ACIERTO Y TIEMPO METODOLÓGICO */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                ¿Fue Acierto? (PPCF) *
              </label>
              <Select
                value={String(nuevoCaso.prediccion_correcta)}
                onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, prediccion_correcta: Number(e.target.value) }))}
                options={[
                  { value: '-1', label: 'Seleccionar resultado' },
                  { value: '1', label: 'Sí (Acierto = 1)' },
                  { value: '0', label: 'No (Desacierto = 0)' },
                ]}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                Tiempo de Diagnóstico Metodológico (min) *
              </label>
              <Input
                type="number"
                min={1}
                max={600}
                required
                value={String(nuevoCaso.tiempo_diagnostico_minutos || '')}
                placeholder="Ej. 15"
                onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, tiempo_diagnostico_minutos: Number(e.target.value) }))}
              />
            </div>
          </div>

          {/* 8. MÉTODO Y EVIDENCIA */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                Método de Confirmación Física *
              </label>
              <Input
                placeholder="Inspección Visual en Elevador"
                value={nuevoCaso.metodo_confirmacion || ''}
                required={entorno === 'OFICIAL'}
                onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, metodo_confirmacion: e.target.value }))}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                Evidencia de Taller *
              </label>
              <Input
                placeholder="OT-2026-081 / Foto componente"
                value={nuevoCaso.evidencia_ref || ''}
                required={entorno === 'OFICIAL'}
                onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, evidencia_ref: e.target.value }))}
              />
            </div>
          </div>

          {/* Botones de acción */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
            <Button type="button" variant="secondary" onClick={onClose} disabled={guardando}>
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={guardando}
              style={{
                backgroundColor: entorno === 'OFICIAL' ? '#dc2626' : undefined,
                borderColor: entorno === 'OFICIAL' ? '#b91c1c' : undefined,
              }}
            >
              {guardando ? 'Guardando...' : entorno === 'OFICIAL' ? 'Guardar en Muestra Oficial' : 'Registrar Caso'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Selector Modal para Vincular Diagnóstico */}
      <VincularDiagnosticoSelector
        isOpen={selectorDiagAbierto}
        onClose={() => setSelectorDiagAbierto(false)}
        onSelectDiagnostico={handleVincularDiagnostico}
      />

      {/* Confirmación de Seguridad para Registro Oficial */}
      <ConfirmacionOficialModal
        isOpen={confirmacionOficialAbierta}
        onClose={() => setConfirmacionOficialAbierta(false)}
        onConfirm={handleConfirmarOficial}
        fase={nuevoCaso.fase}
        guardando={guardando}
      />
    </>
  );
};
