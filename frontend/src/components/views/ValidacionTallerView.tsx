import React, { useState, useEffect, useCallback, useTransition } from 'react';
import {
  Clock,
  Car,
  Plus,
  Download,
  RefreshCw,
  Search,
  CheckCircle,
  AlertTriangle,
  Award,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  ShieldCheck,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { Modal } from '../common/Modal';
import { apiService } from '../../services/api';
import type { CasoValidacionDTO, MetricasValidacionDTO, CrearCasoValidacionDTO } from '../../types/api';

export const ValidacionTallerView: React.FC = () => {
  const [, startTransition] = useTransition();
  const [metricas, setMetricas] = useState<MetricasValidacionDTO | null>(null);
  const [casos, setCasos] = useState<CasoValidacionDTO[]>([]);
  const [totalCasos, setTotalCasos] = useState(0);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filtros
  const [faseFiltro, setFaseFiltro] = useState<string>('');
  const [aciertoFiltro, setAciertoFiltro] = useState<string>('');
  const [busqueda, setBusqueda] = useState<string>('');
  const [pagina, setPagina] = useState(0);
  const limite = 25;

  // Modal Nuevo Caso
  const [modalAbierto, setModalAbierto] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [exitoMensaje, setExitoMensaje] = useState<string | null>(null);

  const [nuevoCaso, setNuevoCaso] = useState<CrearCasoValidacionDTO>({
    fase: 'Post-test',
    placa: '',
    marca_modelo: 'Toyota Yaris 2020',
    sintoma: '',
    falla_real: '',
    chatbot_prediccion: '',
    campos_completos: 1,
    tiempo_diagnostico_minutos: 15,
    prediccion_correcta: 1,
    metodo_confirmacion: 'Inspección Visual + Escáner OBD-II',
    evidencia_ref: '',
  });

  const cargarDatos = useCallback(async () => {
    try {
      setCargando(true);
      setError(null);
      const [metricasRes, casosRes] = await Promise.all([
        apiService.getMetricasValidacion(),
        apiService.getCasosValidacion({
          fase: faseFiltro || undefined,
          acierto: aciertoFiltro !== '' ? Number(aciertoFiltro) : undefined,
          busqueda: busqueda || undefined,
          skip: pagina * limite,
          limit: limite,
        }),
      ]);
      startTransition(() => {
        setMetricas(metricasRes);
        setCasos(casosRes.casos);
        setTotalCasos(casosRes.total);
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al cargar datos del tracker experimental');
    } finally {
      setCargando(false);
    }
  }, [faseFiltro, aciertoFiltro, busqueda, pagina]);

  useEffect(() => {
    cargarDatos();
  }, [cargarDatos]);

  const handleCrearCaso = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nuevoCaso.placa || !nuevoCaso.sintoma || !nuevoCaso.falla_real || !nuevoCaso.chatbot_prediccion) {
      alert('Por favor complete los campos obligatorios.');
      return;
    }
    try {
      setGuardando(true);
      await apiService.crearCasoValidacion(nuevoCaso);
      setExitoMensaje('¡Registro experimental guardado exitosamente con placa pseudonimizada!');
      setModalAbierto(false);
      setNuevoCaso({
        fase: 'Post-test',
        placa: '',
        marca_modelo: 'Toyota Yaris 2020',
        sintoma: '',
        falla_real: '',
        chatbot_prediccion: '',
        campos_completos: 1,
        tiempo_diagnostico_minutos: 15,
        prediccion_correcta: 1,
        metodo_confirmacion: 'Inspección Visual + Escáner OBD-II',
        evidencia_ref: '',
      });
      cargarDatos();
      setTimeout(() => setExitoMensaje(null), 4000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo guardar el registro');
    } finally {
      setGuardando(false);
    }
  };

  const handleDescargarCsv = () => {
    window.open(apiService.getExportarTrackerCsvUrl(), '_blank');
  };

  const totalPaginas = Math.ceil(totalCasos / limite);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', paddingBottom: '32px' }}>
      {/* Encabezado Principal */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-main)', margin: '0 0 4px 0' }}>
            🔬 Seguimiento Experimental y Simulación de Taller
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: 0 }}>
            Plataforma de evaluación empírica de tesis: Comparación entre fase Pre-test (manual) y Post-test (asistida por CarBot).
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <Button variant="outline" size="sm" onClick={handleDescargarCsv}>
            <Download size={15} style={{ marginRight: '6px' }} />
            Exportar CSV Sanitizado
          </Button>
          <Button variant="primary" size="sm" onClick={() => setModalAbierto(true)}>
            <Plus size={15} style={{ marginRight: '6px' }} />
            Registrar Caso de Taller
          </Button>
        </div>
      </div>

      {/* Nota Metodológica de Tesis */}
      <div
        style={{
          padding: '12px 16px',
          backgroundColor: '#f8fafc',
          border: '1px solid #cbd5e1',
          borderRadius: '8px',
          fontSize: '12px',
          color: '#475569',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}
      >
        <ShieldCheck size={18} color="#2563eb" style={{ flexShrink: 0 }} />
        <span>
          <strong>Nota Metodológica de Tesis:</strong> Las métricas agregadas reflejan el seguimiento del piloto experimental
          (Pre-test vs Post-test) y los 33 casos reales de taller auditados. Las placas se encuentran pseudonimizadas
          mediante encriptación SHA-256 para estricto cumplimiento de privacidad de datos.
        </span>
      </div>

      {exitoMensaje && (
        <div style={{ padding: '12px 16px', backgroundColor: '#ecfdf5', border: '1px solid #10b981', color: '#065f46', borderRadius: '8px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={16} />
          <span>{exitoMensaje}</span>
        </div>
      )}

      {error && (
        <div style={{ padding: '12px 16px', backgroundColor: '#fef2f2', border: '1px solid #ef4444', color: '#991b1b', borderRadius: '8px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Tarjetas de Métricas Ejecutivas del Estudio de Campo */}
      {metricas && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
          <Card style={{ padding: '16px', borderLeft: '4px solid #2563eb' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Registros Tracker</span>
                <h3 style={{ fontSize: '24px', fontWeight: 800, margin: '4px 0 0 0', color: 'var(--text-main)' }}>
                  {metricas.total_casos.toLocaleString()}
                </h3>
              </div>
              <div style={{ padding: '10px', backgroundColor: '#eff6ff', borderRadius: '10px', color: '#2563eb' }}>
                <Car size={22} />
              </div>
            </div>
            <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-secondary)' }}>
              Pre-test: <strong>{metricas.casos_pretest}</strong> | Post-test: <strong>{metricas.casos_posttest}</strong>
            </div>
          </Card>

          <Card style={{ padding: '16px', borderLeft: '4px solid #10b981' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Precisión Post-Test (Con Bot)</span>
                <h3 style={{ fontSize: '24px', fontWeight: 800, margin: '4px 0 0 0', color: '#059669' }}>
                  {metricas.tasa_acierto_posttest_porcentaje}%
                </h3>
              </div>
              <div style={{ padding: '10px', backgroundColor: '#ecfdf5', borderRadius: '10px', color: '#059669' }}>
                <Award size={22} />
              </div>
            </div>
            <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-secondary)' }}>
              Pre-test manual: <strong>{metricas.tasa_acierto_pretest_porcentaje}%</strong>
            </div>
          </Card>

          <Card style={{ padding: '16px', borderLeft: '4px solid #f59e0b' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Tiempo Post-Test</span>
                <h3 style={{ fontSize: '24px', fontWeight: 800, margin: '4px 0 0 0', color: '#d97706' }}>
                  {metricas.tiempo_promedio_posttest_min} min
                </h3>
              </div>
              <div style={{ padding: '10px', backgroundColor: '#fffbeb', borderRadius: '10px', color: '#d97706' }}>
                <Clock size={22} />
              </div>
            </div>
            <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-secondary)' }}>
              Pre-test tradicional: <strong>{metricas.tiempo_promedio_pretest_min} min</strong>
            </div>
          </Card>

          <Card style={{ padding: '16px', borderLeft: '4px solid #8b5cf6' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Reducción de Tiempo</span>
                <h3 style={{ fontSize: '24px', fontWeight: 800, margin: '4px 0 0 0', color: '#7c3aed' }}>
                  -{metricas.reduccion_tiempo_porcentaje}%
                </h3>
              </div>
              <div style={{ padding: '10px', backgroundColor: '#f5f3ff', borderRadius: '10px', color: '#7c3aed' }}>
                <TrendingUp size={22} />
              </div>
            </div>
            <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-secondary)' }}>
              Ahorro de ~<strong>{Math.round(metricas.tiempo_promedio_pretest_min - metricas.tiempo_promedio_posttest_min)} min</strong> por diagnóstico
            </div>
          </Card>
        </div>
      )}

      {/* Barra de Filtros y Búsqueda */}
      <Card style={{ padding: '14px 18px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center', flex: 1, minWidth: '280px' }}>
            <div style={{ position: 'relative', flex: 1, minWidth: '220px' }}>
              <Input
                placeholder="Buscar por placa pseudonimizada, síntoma, falla o predicción..."
                value={busqueda}
                onChange={(e) => {
                  setBusqueda(e.target.value);
                  setPagina(0);
                }}
                style={{ width: '100%', paddingLeft: '32px' }}
              />
              <Search size={15} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            </div>

            <div style={{ width: '170px' }}>
              <Select
                value={faseFiltro}
                onChange={(e) => {
                  setFaseFiltro(e.target.value);
                  setPagina(0);
                }}
                options={[
                  { value: '', label: 'Todas las Fases' },
                  { value: 'Pre-test', label: 'Pre-test (Manual)' },
                  { value: 'Post-test', label: 'Post-test (Con Bot)' },
                  { value: 'Piloto', label: 'Fase Piloto' },
                ]}
              />
            </div>

            <div style={{ width: '180px' }}>
              <Select
                value={aciertoFiltro}
                onChange={(e) => {
                  setAciertoFiltro(e.target.value);
                  setPagina(0);
                }}
                options={[
                  { value: '', label: 'Todos los Resultados' },
                  { value: '1', label: '✔ Aciertos (Bot Correcto)' },
                  { value: '0', label: '❌ Desaciertos (Corregido)' },
                ]}
              />
            </div>
          </div>

          <Button variant="ghost" size="sm" onClick={() => cargarDatos()} disabled={cargando}>
            <RefreshCw size={14} className={cargando ? 'animate-spin' : ''} style={{ marginRight: '6px' }} />
            Actualizar
          </Button>
        </div>
      </Card>

      {/* Tabla de Casos del Tracker */}
      <Card style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--bg-subtle)', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>Item</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>Fase / Fecha</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>Vehículo (Pseudónimo)</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>Síntoma Declarado</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>Predicción CarBot</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>Diagnóstico Mecánico</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>Método Confirmación</th>
                <th style={{ padding: '10px 14px', fontWeight: 600, textAlign: 'center' }}>Tiempo</th>
                <th style={{ padding: '10px 14px', fontWeight: 600, textAlign: 'center' }}>Resultado</th>
              </tr>
            </thead>
            <tbody>
              {cargando && casos.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    Cargando registros del tracker experimental...
                  </td>
                </tr>
              ) : casos.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No se encontraron registros con los filtros seleccionados.
                  </td>
                </tr>
              ) : (
                casos.map((c) => (
                  <tr
                    key={c.item}
                    style={{
                      borderBottom: '1px solid var(--border-color)',
                      transition: 'background-color 0.15s ease',
                    }}
                  >
                    <td style={{ padding: '10px 14px', fontWeight: 700, color: 'var(--text-muted)' }}>
                      #{c.item}
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <span style={{ fontWeight: 600, color: c.fase === 'Post-test' ? '#2563eb' : '#64748b' }}>
                          {c.fase}
                        </span>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{c.fecha}</span>
                      </div>
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <span style={{ fontWeight: 700, color: 'var(--text-main)', letterSpacing: '0.04em' }}>
                          {c.placa_enmascarada}
                        </span>
                        <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{c.marca_modelo}</span>
                      </div>
                    </td>
                    <td style={{ padding: '10px 14px', maxWidth: '220px' }}>
                      <span style={{ color: 'var(--text-main)' }}>{c.sintoma}</span>
                    </td>
                    <td style={{ padding: '10px 14px', maxWidth: '180px' }}>
                      <span style={{ color: '#1e40af', fontWeight: 600 }}>{c.chatbot_prediccion}</span>
                    </td>
                    <td style={{ padding: '10px 14px', maxWidth: '180px' }}>
                      <span style={{ color: '#065f46', fontWeight: 600 }}>{c.falla_real}</span>
                    </td>
                    <td style={{ padding: '10px 14px', maxWidth: '160px' }}>
                      <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
                        {c.metodo_confirmacion || 'Inspección Visual'}
                      </span>
                    </td>
                    <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                      <span style={{ padding: '3px 8px', borderRadius: '6px', backgroundColor: 'var(--bg-subtle)', fontWeight: 600, fontSize: '11px' }}>
                        {c.tiempo_diagnostico_minutos} min
                      </span>
                    </td>
                    <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                      {c.prediccion_correcta === 1 ? (
                        <Badge type="confirmado" label="✔ Acertado" size="sm" />
                      ) : (
                        <Badge type="descartado" label="❌ Corregido" size="sm" />
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Paginador */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 18px', borderTop: '1px solid var(--border-color)', fontSize: '12px', color: 'var(--text-muted)' }}>
          <span>
            Mostrando <strong>{casos.length}</strong> de <strong>{totalCasos.toLocaleString()}</strong> casos
          </span>
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPagina((p) => Math.max(0, p - 1))}
              disabled={pagina === 0}
            >
              <ChevronLeft size={14} />
              Anterior
            </Button>
            <span>
              Página {pagina + 1} de {totalPaginas || 1}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPagina((p) => Math.min(totalPaginas - 1, p + 1))}
              disabled={pagina >= totalPaginas - 1}
            >
              Siguiente
              <ChevronRight size={14} />
            </Button>
          </div>
        </div>
      </Card>

      {/* Modal Registrar Nuevo Caso */}
      {modalAbierto && (
        <Modal
          isOpen={modalAbierto}
          onClose={() => setModalAbierto(false)}
          title="Registrar Caso de Taller (Tracker Experimental Tesis)"
          maxWidth="640px"
        >
          <form onSubmit={handleCrearCaso} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
              <div>
                <Select
                  label="Fase de Evaluación"
                  value={nuevoCaso.fase}
                  onChange={(e) => setNuevoCaso({ ...nuevoCaso, fase: e.target.value as 'Pre-test' | 'Post-test' | 'Piloto' })}
                  options={[
                    { value: 'Post-test', label: 'Post-test (Asistencia CarBot)' },
                    { value: 'Pre-test', label: 'Pre-test (Diagnóstico Tradicional)' },
                    { value: 'Piloto', label: 'Fase Piloto' },
                  ]}
                />
              </div>

              <div>
                <Input
                  label="Placa Vehicular (Será Pseudonimizada)"
                  placeholder="Ej. ABC-123"
                  value={nuevoCaso.placa}
                  onChange={(e) => setNuevoCaso({ ...nuevoCaso, placa: e.target.value.toUpperCase() })}
                  required
                />
              </div>
            </div>

            <div>
              <Input
                label="Marca y Modelo del Vehículo"
                placeholder="Ej. Toyota Yaris 2020 / Nissan Sentra"
                value={nuevoCaso.marca_modelo}
                onChange={(e) => setNuevoCaso({ ...nuevoCaso, marca_modelo: e.target.value })}
                required
              />
            </div>

            <div>
              <Input
                label="Síntoma Inicial Declarado"
                placeholder="Ej. Pedal de freno esponjoso y se hunde en bajada"
                value={nuevoCaso.sintoma}
                onChange={(e) => setNuevoCaso({ ...nuevoCaso, sintoma: e.target.value })}
                required
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
              <div>
                <Input
                  label="Predicción de CarBot"
                  placeholder="Ej. Fuga de liquido de frenos"
                  value={nuevoCaso.chatbot_prediccion}
                  onChange={(e) => setNuevoCaso({ ...nuevoCaso, chatbot_prediccion: e.target.value })}
                  required
                />
              </div>

              <div>
                <Input
                  label="Diagnóstico Final Mecánico"
                  placeholder="Ej. Fuga en bombin maestro de frenos"
                  value={nuevoCaso.falla_real}
                  onChange={(e) => setNuevoCaso({ ...nuevoCaso, falla_real: e.target.value })}
                  required
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
              <div>
                <Input
                  label="Método de Confirmación"
                  placeholder="Ej. Manómetro hidráulico + Inspección visual"
                  value={nuevoCaso.metodo_confirmacion || ''}
                  onChange={(e) => setNuevoCaso({ ...nuevoCaso, metodo_confirmacion: e.target.value })}
                />
              </div>

              <div>
                <Input
                  label="Referencia de Evidencia (Opcional)"
                  placeholder="Ej. FOTO_BOMBIN_01.JPG / INFORME_PDF"
                  value={nuevoCaso.evidencia_ref || ''}
                  onChange={(e) => setNuevoCaso({ ...nuevoCaso, evidencia_ref: e.target.value })}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
              <div>
                <Input
                  label="Tiempo de Diagnóstico (Minutos)"
                  type="number"
                  min="1"
                  max="300"
                  value={String(nuevoCaso.tiempo_diagnostico_minutos)}
                  onChange={(e) => setNuevoCaso({ ...nuevoCaso, tiempo_diagnostico_minutos: Number(e.target.value) })}
                  required
                />
              </div>

              <div>
                <Select
                  label="¿El Bot Acertó?"
                  value={String(nuevoCaso.prediccion_correcta)}
                  onChange={(e) => setNuevoCaso({ ...nuevoCaso, prediccion_correcta: Number(e.target.value) })}
                  options={[
                    { value: '1', label: '✔ Sí, Predicción Correcta (Acertado)' },
                    { value: '0', label: '❌ No, Mecánico Corrigió (Desacertado)' },
                  ]}
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px', borderTop: '1px solid var(--border-color)', paddingTop: '14px' }}>
              <Button variant="outline" type="button" onClick={() => setModalAbierto(false)}>
                Cancelar
              </Button>
              <Button variant="primary" type="submit" disabled={guardando}>
                {guardando ? 'Guardando...' : 'Guardar en Tracker'}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
