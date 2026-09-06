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

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
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
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
              Completitud
            </label>
            <Select
              value={String(nuevoCaso.campos_completos)}
              onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, campos_completos: Number(e.target.value) }))}
              options={[
                { value: '-1', label: 'Revisar registro' },
                { value: '1', label: 'Completo (1)' },
                { value: '0', label: 'Incompleto (0)' },
              ]}
            />
          </div>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
            Método de Confirmación
          </label>
          <Input
            value={nuevoCaso.metodo_confirmacion}
            onChange={(e) => onNuevoCasoChange((prev) => ({ ...prev, metodo_confirmacion: e.target.value }))}
          />
        </div>

        <p style={{ fontSize: 12 }}>Evalúa la completitud según la ficha acordada. El tiempo corresponde al diagnóstico del taller.</p>
        <label>Evidencia de la revisión
          <Input value={nuevoCaso.evidencia_ref || ''}
            onChange={e => onNuevoCasoChange(prev => ({ ...prev, evidencia_ref: e.target.value }))} />
        </label>
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
