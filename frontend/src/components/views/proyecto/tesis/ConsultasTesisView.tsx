import React, { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { PeriodoFilter } from '../../../common/PeriodoFilter';
import { DiagnosticoDetalleModal } from '../../diagnosticos/DiagnosticoDetalleModal';
import { apiService } from '../../../../services/api';
import { dashboardApi } from '../../../../features/dashboard/api';
import type { Periodo } from '../../../../utils/periodo';
import type { Diagnostico, ResumenMetricas } from '../../../../types';
import type { MetricasValidacionDTO } from '../../../../types/api';
import {
  calcularIndicadoresVI,
  calcularTelemetriaTecnica,
} from './rendimiento/calculosIndicadores';
import { IndicadoresVariableIndependiente } from './rendimiento/IndicadoresVariableIndependiente';
import { MetricasTecnicas } from './rendimiento/MetricasTecnicas';
import { DistribucionPipeline } from './rendimiento/DistribucionPipeline';
import { AuditoriaConsultas } from './rendimiento/AuditoriaConsultas';

export const ConsultasTesisView: React.FC = () => {
  const [periodo, setPeriodo] = useState<Periodo>({});
  const [metricas, setMetricas] = useState<ResumenMetricas | null>(null);
  const [metricasValidacion, setMetricasValidacion] = useState<MetricasValidacionDTO | null>(null);
  const [cargandoMetricas, setCargandoMetricas] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busqueda, setBusqueda] = useState('');
  const [diagnosticoModal, setDiagnosticoModal] = useState<Diagnostico | null>(null);

  const [historial, setHistorial] = useState<{
    diagnosticos: Diagnostico[];
    total: number;
    cargando: boolean;
  }>({
    diagnosticos: [],
    total: 0,
    cargando: true,
  });

  useEffect(() => {
    let activo = true;
    const cargar = async () => {
      setCargandoMetricas(true);
      setError(null);
      try {
        const [datosDashboard, datosVal] = await Promise.all([
          dashboardApi.getResumenMetricas(periodo.fecha_desde, periodo.fecha_hasta, true),
          apiService.getMetricasValidacion(periodo).catch(() => null),
        ]);
        if (activo) {
          setMetricas(datosDashboard);
          setMetricasValidacion(datosVal);
        }
      } catch (err) {
        if (activo) {
          setError(err instanceof Error ? err.message : 'Error al cargar telemetría de CarBot');
        }
      } finally {
        if (activo) setCargandoMetricas(false);
      }
    };
    void cargar();
    return () => {
      activo = false;
    };
  }, [periodo]);

  useEffect(() => {
    let activo = true;
    const cargarHistorial = async () => {
      setHistorial((prev) => ({ ...prev, cargando: true }));
      try {
        const resp = await apiService.getDiagnosticos({
          fecha_desde: periodo.fecha_desde,
          fecha_hasta: periodo.fecha_hasta,
          limite: 50,
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingBottom: '32px' }}>
      {/* 1. Encabezado de la Sección */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-main)', margin: '0 0 4px 0' }}>
            Desempeño de CarBot (Variable Independiente)
          </h2>
          <p style={{ margin: 0, fontSize: '12.5px', color: 'var(--text-secondary)' }}>
            Evaluación técnica del modelo <strong>Linear SVM con TF-IDF</strong> y pipeline de atención vía WhatsApp en el taller CARTER MOTOR'S E.I.R.L.
          </p>
        </div>
      </div>

      {/* Control de Período */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <PeriodoFilter value={periodo} onChange={setPeriodo} />
        {cargandoMetricas && (
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <RefreshCw size={13} className="animate-spin" /> Actualizando telemetría...
          </span>
        )}
      </div>

      {error && (
        <div className="inline-error" role="alert">
          {error}
        </div>
      )}

      {/* 2. NIVEL 1: Indicadores Metodológicos de la Variable Independiente */}
      <IndicadoresVariableIndependiente indicadores={indicadoresVI} />

      {/* 3. NIVEL 2: Métricas Técnicas Complementarias */}
      <MetricasTecnicas
        telemetria={telemetriaTecnica}
        confirmadosCount={confirmadosCount}
        pendientesCount={pendientesCount}
      />

      {/* 4. Desglose Técnico: Hipótesis de Falla y Modos de Inferencia */}
      <DistribucionPipeline
        metricas={metricas}
        totalConsultas={telemetriaTecnica.totalConsultas}
      />

      {/* 5. Tabla de Auditoría y Trazabilidad Individual */}
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
      />
    </div>
  );
};
