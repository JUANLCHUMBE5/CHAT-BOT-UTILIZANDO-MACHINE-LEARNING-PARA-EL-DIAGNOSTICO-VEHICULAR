import React, { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { DiagnosticoDetalleModal } from '../../diagnosticos/DiagnosticoDetalleModal';
import { ValidacionNuevoCasoModal } from '../../validacion/ValidacionNuevoCasoModal';
import { apiService } from '../../../../services/api';
import { dashboardApi } from '../../../../features/dashboard/api';
import type { Periodo } from '../../../../utils/periodo';
import type { Diagnostico, ResumenMetricas } from '../../../../types';
import type { MetricasValidacionDTO, CrearCasoValidacionDTO } from '../../../../types/api';
import {
  calcularIndicadoresVI,
  calcularTelemetriaTecnica,
} from './rendimiento/calculosIndicadores';
import { IndicadoresVariableIndependiente } from './rendimiento/IndicadoresVariableIndependiente';
import { MetricasTecnicas } from './rendimiento/MetricasTecnicas';
import { AuditoriaConsultas } from './rendimiento/AuditoriaConsultas';

export const ConsultasTesisView: React.FC = () => {
  const [periodo] = useState<Periodo>({});
  const [metricas, setMetricas] = useState<ResumenMetricas | null>(null);
  const [metricasValidacion, setMetricasValidacion] = useState<MetricasValidacionDTO | null>(null);
  const [cargandoMetricas, setCargandoMetricas] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busqueda, setBusqueda] = useState('');
  const [diagnosticoModal, setDiagnosticoModal] = useState<Diagnostico | null>(null);
  const [modalNuevoCasoAbierto, setModalNuevoCasoAbierto] = useState(false);
  const [guardandoCaso, setGuardandoCaso] = useState(false);
  const [casoParaCrear, setCasoParaCrear] = useState<CrearCasoValidacionDTO>({
    fase: 'Post-test',
    placa: '',
    marca_modelo: '',
    sintoma: '',
    descripcion_sintoma: '',
    falla_real: '',
    chatbot_prediccion: '',
    campos_completos: 1,
    tiempo_diagnostico_minutos: 0,
    prediccion_correcta: -1,
    estado_registro: 'borrador',
    tipo_registro: 'DEVELOPMENT',
  });

  const [historial, setHistorial] = useState<{
    diagnosticos: Diagnostico[];
    total: number;
    cargando: boolean;
  }>({
    diagnosticos: [],
    total: 0,
    cargando: true,
  });

  const cargarDatos = async () => {
    setCargandoMetricas(true);
    setError(null);
    try {
      const [datosDashboard, datosVal] = await Promise.all([
        dashboardApi.getResumenMetricas(periodo.fecha_desde, periodo.fecha_hasta, true),
        apiService.getMetricasValidacion(periodo).catch(() => null),
      ]);
      setMetricas(datosDashboard);
      setMetricasValidacion(datosVal);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar telemetría de CarBot');
    } finally {
      setCargandoMetricas(false);
    }
  };

  useEffect(() => {
    void cargarDatos();
  }, [periodo]);

  useEffect(() => {
    let activo = true;
    const cargarHistorial = async () => {
      setHistorial((prev) => ({ ...prev, cargando: true }));
      try {
        const resp = await apiService.getDiagnosticos({
          fecha_desde: periodo.fecha_desde,
          fecha_hasta: periodo.fecha_hasta,
          limite: 100,
        });
        if (activo) {
          setHistorial({
            diagnosticos: resp.items,
            total: resp.total,
            cargando: false,
          });
        }
      } catch {
        if (activo) {
          setHistorial((prev) => ({ ...prev, cargando: false }));
        }
      }
    };
    void cargarHistorial();
    return () => {
      activo = false;
    };
  }, [periodo]);

  const diagnósticosFiltrados = historial.diagnosticos.filter((d) => {
    if (!busqueda.trim()) return true;
    const term = busqueda.toLowerCase();
    return (
      (d.sintoma_original || '').toLowerCase().includes(term) ||
      (d.sintoma_normalizado || '').toLowerCase().includes(term) ||
      (d.falla_predicha || '').toLowerCase().includes(term) ||
      (d.cliente_nombre || '').toLowerCase().includes(term) ||
      (d.mecanico_nombre || '').toLowerCase().includes(term) ||
      (d.cliente_telefono || '').includes(term) ||
      (d.placa_vehiculo || '').toLowerCase().includes(term)
    );
  });

  const indicadoresVI = calcularIndicadoresVI(metricasValidacion);
  const telemetriaTecnica = calcularTelemetriaTecnica(metricas, historial.total);

  const confirmadosCount = historial.diagnosticos.filter((d) => d.estado === 'confirmado').length;
  const pendientesCount =
    metricas?.diagnosticos_pendientes ??
    historial.diagnosticos.filter((d) => d.estado === 'generado' || d.estado === 'en_revision').length;

  const handleCrearPostTestDesdeDiagnostico = (d: Diagnostico) => {
    setCasoParaCrear({
      fase: 'Post-test',
      fecha: d.fecha_hora ? d.fecha_hora.slice(0, 10) : new Date().toISOString().slice(0, 10),
      placa: d.placa_vehiculo && !d.placa_vehiculo.toLowerCase().includes('sin placa') ? d.placa_vehiculo : '',
      marca_modelo: '',
      sintoma: d.sintoma_original || '',
      descripcion_sintoma: '',
      falla_real: '',
      chatbot_prediccion: d.falla_predicha || '',
      sistema_afectado_probable: d.falla_predicha || '',
      campos_completos: 1,
      tiempo_diagnostico_minutos: 0,
      prediccion_correcta: -1,
      metodo_confirmacion: 'Inspección Visual en Elevador',
      evidencia_ref: '',
      estado_registro: 'borrador',
      tipo_registro: 'DEVELOPMENT',
      diagnostico_id: d.id,
      conversacion_id: d.conversacion_id || null,
      tiempo_inferencia_ml_ms: d.duracion_ms || undefined,
    });
    setDiagnosticoModal(null);
    setModalNuevoCasoAbierto(true);
  };

  const handleGuardarNuevoCaso = async (e: React.FormEvent) => {
    e.preventDefault();
    if (casoParaCrear.prediccion_correcta < 0) {
      alert('Indica el resultado de la predicción.');
      return;
    }
    try {
      setGuardandoCaso(true);
      await apiService.crearCasoValidacion(casoParaCrear);
      setModalNuevoCasoAbierto(false);
      const datosVal = await apiService.getMetricasValidacion(periodo);
      setMetricasValidacion(datosVal);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al guardar el caso');
    } finally {
      setGuardandoCaso(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', paddingBottom: '32px' }}>
      {/* Encabezado Limpio */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-main)', margin: '0 0 2px 0' }}>
            Desempeño de CarBot (Variable Independiente)
          </h2>
          <p style={{ margin: 0, fontSize: '12.5px', color: 'var(--text-secondary)' }}>
            CARTER MOTOR'S E.I.R.L. · Evaluación del modelo Linear SVM con TF-IDF y canal WhatsApp (Anexo 1)
          </p>
        </div>

        <button
          type="button"
          onClick={() => void cargarDatos()}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            fontSize: '11.5px',
            fontWeight: 600,
            borderRadius: '6px',
            border: '1px solid var(--border-color)',
            backgroundColor: '#ffffff',
            color: 'var(--text-main)',
            cursor: 'pointer',
          }}
        >
          <RefreshCw size={13} className={cargandoMetricas ? 'animate-spin' : ''} />
          <span>{cargandoMetricas ? 'Actualizando...' : 'Actualizar telemetría'}</span>
        </button>
      </div>

      {error && (
        <div className="inline-error" role="alert">
          {error}
        </div>
      )}

      {/* 1. Indicadores Metodológicos Oficiales de la Variable Independiente (Anexo 1) */}
      <IndicadoresVariableIndependiente indicadores={indicadoresVI} />

      {/* 2. Métricas Técnicas y Tiempos de Respuesta Reales (Regla 4 de AGENTS.md) */}
      <MetricasTecnicas
        telemetria={telemetriaTecnica}
        confirmadosCount={confirmadosCount}
        pendientesCount={pendientesCount}
      />

      {/* 3. Tabla de Auditoría de Consultas WhatsApp (Inferencia y Vinculación) */}
      <AuditoriaConsultas
        diagnosticos={diagnósticosFiltrados}
        cargando={historial.cargando}
        busqueda={busqueda}
        onBusquedaChange={setBusqueda}
        onVerDetalle={setDiagnosticoModal}
      />

      {/* Modal de Detalle de Inferencia */}
      <DiagnosticoDetalleModal
        diagnostico={diagnosticoModal}
        isOpen={Boolean(diagnosticoModal)}
        onClose={() => setDiagnosticoModal(null)}
        onCrearPostTest={handleCrearPostTestDesdeDiagnostico}
      />

      {/* Modal para Crear Registro Experimental desde Diagnóstico */}
      <ValidacionNuevoCasoModal
        isOpen={modalNuevoCasoAbierto}
        onClose={() => setModalNuevoCasoAbierto(false)}
        nuevoCaso={casoParaCrear}
        onNuevoCasoChange={setCasoParaCrear}
        guardando={guardandoCaso}
        onSubmit={handleGuardarNuevoCaso}
      />
    </div>
  );
};
