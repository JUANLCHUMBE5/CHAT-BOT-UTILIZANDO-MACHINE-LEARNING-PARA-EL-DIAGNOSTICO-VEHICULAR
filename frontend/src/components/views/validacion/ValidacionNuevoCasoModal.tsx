import React from 'react';
import { Modal } from '../../common/Modal';
import { Button } from '../../common/Button';
import { Input } from '../../common/Input';
import { Select } from '../../common/Select';
import type { CrearCasoValidacionDTO } from '../../../types/api';

interface ValidacionNuevoCasoModalProps {
  isOpen: boolean;
  onClose: () => void;
  nuevoCaso: CrearCasoValidacionDTO;
  onNuevoCasoChange: (updater: (prev: CrearCasoValidacionDTO) => CrearCasoValidacionDTO) => void;
  guardando: boolean;
  onSubmit: (e: React.FormEvent) => Promise<void>;
}

export const ValidacionNuevoCasoModal: React.FC<ValidacionNuevoCasoModalProps> = ({
  isOpen,
  onClose,
  nuevoCaso,
  onNuevoCasoChange,
  guardando,
  onSubmit,
}) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Registrar evaluación"
      maxWidth="680px"
    >
      <form onSubmit={onSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <label>Fecha de atención
          <Input type="date" value={nuevoCaso.fecha || ''} required
            onChange={e => onNuevoCasoChange(prev => ({ ...prev, fecha: e.target.value }))} />
        </label>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
              Fase del Estudio *
            </label>
            <Select
              value={nuevoCaso.fase}
              onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, fase: e.target.value as 'Pre-test' | 'Post-test' }))}
              options={[
                { value: 'Post-test', label: 'Post-test (Asistido por CarBot)' },
                { value: 'Pre-test', label: 'Pre-test (Diagnóstico Convencional)' },
              ]}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
              Placa del Vehículo *
            </label>
            <Input
              placeholder="Ej. ABC-123"
              value={nuevoCaso.placa}
              onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, placa: e.target.value }))}
              required
            />
          </div>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
            Marca y modelo del registro *
          </label>
          <Input
            placeholder="Ej. Toyota Yaris 2020"
            value={nuevoCaso.marca_modelo}
            required
            minLength={2}
            onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, marca_modelo: e.target.value }))}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
              Año del vehículo *
            </label>
            <Input
              type="number"
              min={1950}
              max={2100}
              placeholder="Ej. 2020"
              value={nuevoCaso.vehiculo_anio ? String(nuevoCaso.vehiculo_anio) : ''}
              required
              onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, vehiculo_anio: e.target.value ? Number(e.target.value) : undefined }))}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
              Kilometraje aproximado *
            </label>
            <Input
              type="number"
              min={0}
              placeholder="Ej. 85000"
              value={nuevoCaso.vehiculo_kilometraje !== undefined ? String(nuevoCaso.vehiculo_kilometraje) : ''}
              required
              onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, vehiculo_kilometraje: e.target.value ? Number(e.target.value) : undefined }))}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
              Tipo de combustible *
            </label>
            <Input
              placeholder="Ej. Gasolina / GLP / GNV"
              value={nuevoCaso.vehiculo_combustible || ''}
              required
              onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, vehiculo_combustible: e.target.value }))}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
              Tipo de transmisión *
            </label>
            <Input
              placeholder="Ej. Mecánica / Automática"
              value={nuevoCaso.vehiculo_transmision || ''}
              required
              onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, vehiculo_transmision: e.target.value }))}
            />
          </div>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
            Síntoma *
          </label>
          <Input
            placeholder="Ej. Chillido metálico al frenar a baja velocidad"
            value={nuevoCaso.sintoma}
            onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, sintoma: e.target.value }))}
            required
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
            Descripción del síntoma *
          </label>
          <Input
            placeholder="Ej. El volante vibra solo al frenar a velocidad media"
            value={nuevoCaso.descripcion_sintoma || ''}
            onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, descripcion_sintoma: e.target.value }))}
            required
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
              {nuevoCaso.fase === 'Pre-test' ? 'Hipótesis inicial del mecánico *' : 'Predicción original del chatbot *'}
            </label>
            <Input
              placeholder="Ej. Desgaste de Pastillas de Freno"
              value={nuevoCaso.chatbot_prediccion}
              onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, chatbot_prediccion: e.target.value }))}
              required
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
              Sistema afectado probable *
            </label>
            <Input
              placeholder="Ej. Frenos / Motor / Transmisión"
              value={nuevoCaso.sistema_afectado_probable || ''}
              onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, sistema_afectado_probable: e.target.value }))}
              required
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
              Falla Real Confirmada *
            </label>
            <Input
              placeholder="Ej. Desgaste de Pastillas de Freno Delanteras"
              value={nuevoCaso.falla_real}
              onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, falla_real: e.target.value }))}
              required
            />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
              ¿Fue Acierto?
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
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
              Tiempo Empleado (min)
            </label>
            <Input
              type="number"
              min={1}
              max={600}
              required
              value={String(nuevoCaso.tiempo_diagnostico_minutos)}
              onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, tiempo_diagnostico_minutos: Number(e.target.value) }))}
            />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
              Estado del Registro (Metodología) *
            </label>
            <Select
              value={nuevoCaso.estado_registro || 'verificado'}
              onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, estado_registro: e.target.value as 'verificado' | 'borrador' }))}
              options={[
                { value: 'verificado', label: 'Verificado (Oficial - Incluido en Tesis)' },
                { value: 'borrador', label: 'Borrador (Pendiente de Verificación)' },
              ]}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
              Método de Confirmación Física *
            </label>
            <Input
              placeholder="Ej. Inspección Visual en Elevador / Scanner OBD-II"
              value={nuevoCaso.metodo_confirmacion || ''}
              required={nuevoCaso.estado_registro === 'verificado'}
              onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, metodo_confirmacion: e.target.value }))}
            />
          </div>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
            Evidencia o Referencia de Taller *
          </label>
          <Input
            placeholder="Ej. Orden de Trabajo OT-2026-042 / Foto de pieza desmontada"
            value={nuevoCaso.evidencia_ref || ''}
            required={nuevoCaso.estado_registro === 'verificado'}
            onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, evidencia_ref: e.target.value }))}
          />
        </div>

        {/* Sección de Indicadores de la Variable Independiente (CarBot con ML) */}
        <div style={{
          backgroundColor: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '8px',
          padding: '12px 14px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
        }}>
          <div style={{ fontSize: '12.5px', fontWeight: 700, color: 'var(--text-main)' }}>
            Evaluación Operacional de la Variable Independiente (CarBot con ML)
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                Indicador 1: ¿Síntoma registrado correctamente?
              </label>
              <Select
                value={String(nuevoCaso.sintoma_registrado_correctamente ?? 1)}
                onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, sintoma_registrado_correctamente: Number(e.target.value) }))}
                options={[
                  { value: '1', label: 'Sí (Coincide con relato técnico validado)' },
                  { value: '0', label: 'No (Incompleto o distorsionado)' },
                ]}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                Indicador 2: Etapas del Pipeline Procesadas
              </label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px', marginTop: '4px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={nuevoCaso.normalizacion_correcta !== 0}
                    onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, normalizacion_correcta: e.target.checked ? 1 : 0 }))}
                  />
                  <span>Normalización de texto correcta</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={nuevoCaso.extraccion_correcta !== 0}
                    onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, extraccion_correcta: e.target.checked ? 1 : 0 }))}
                  />
                  <span>Extracción técnica correcta</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={nuevoCaso.clasificacion_procesada !== 0}
                    onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, clasificacion_procesada: e.target.checked ? 1 : 0 }))}
                  />
                  <span>Clasificación procesada</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
          <Button type="button" variant="secondary" onClick={onClose} disabled={guardando}>
            Cancelar
          </Button>
          <Button type="submit" variant="primary" disabled={guardando}>
            {guardando ? 'Guardando...' : 'Registrar Caso'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
