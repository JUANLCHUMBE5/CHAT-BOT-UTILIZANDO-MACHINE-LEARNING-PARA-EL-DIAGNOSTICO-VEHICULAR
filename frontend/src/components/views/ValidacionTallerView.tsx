import React, { useState } from 'react';
import {
  Download,
  Plus,
  AlertTriangle,
  CheckCircle,
  FileSpreadsheet,
  BarChart3,
  ClipboardList,
  Search,
} from 'lucide-react';
import { Button } from '../common/Button';
import { PeriodoFilter } from '../common/PeriodoFilter';
import { useValidacionTaller } from '../../hooks/useValidacionTaller';
import { useTesisStats } from '../../hooks/useTesisStats';
import {
  ValidacionMetricasCards,
  ValidacionCasosTable,
  ValidacionNuevoCasoModal,
} from './validacion';
import { TesisFichaOficialView } from './proyecto/tesis/TesisFichaOficialView';
import { TesisComparativaChart } from './proyecto/tesis/TesisComparativaChart';
import type { RegistroTesis } from '../../data/fichasTesisData';

type TabEvaluacion = 'resumen' | 'ficha1' | 'ficha2' | 'ficha3' | 'casos';

export const ValidacionTallerView: React.FC = () => {
  const [tabActiva, setTabActiva] = useState<TabEvaluacion>('resumen');
  const [modoDemoGrafica, setModoDemoGrafica] = useState(false);
  const { dataComparativaFichas } = useTesisStats();

  const {
    metricas,
    casos,
    casosVerificados,
    totalCasos,
    cargando,
    error,
    faseFiltro,
    setFaseFiltro,
    aciertoFiltro,
    setAciertoFiltro,
    busqueda,
    setBusqueda,
    pagina,
    setPagina,
    totalPaginas,
    modalAbierto,
    setModalAbierto,
    guardando,
    exitoMensaje,
    nuevoCaso,
    setNuevoCaso,
    handleCrearCaso,
    handleDescargarCsv,
    handleDescargarFichasAnexo2Csv,
    periodo,
    setPeriodo,
    cargarDatos,
  } = useValidacionTaller();

  // Mapeo de casos reales desde la API a la interfaz de registros de tesis
  // Utiliza la lista completa de casos verificados (no solo la página de 10 de la tabla)
  const fuenteCasosTesis = casosVerificados && casosVerificados.length > 0 ? casosVerificados : casos;
  const casosRealesTesis: RegistroTesis[] = fuenteCasosTesis.map((c) => ({
    item: c.item,
    fase: c.fase === 'Pre-test' ? 'Pre-test' : 'Post-test',
    fecha: c.fecha,
    placa: c.placa_enmascarada || 'VEH-***',
    marca_modelo: c.marca_modelo,
    sintoma: c.sintoma,
    falla_real: c.falla_real,
    chatbot_prediccion: c.chatbot_prediccion,
    campos_completos: c.campos_completos,
    tiempo_diagnostico_minutos: c.tiempo_diagnostico_minutos,
    prediccion_correcta: c.prediccion_correcta,
  }));

  const casosPretest = metricas?.casos_pretest ?? 0;
  const casosPosttest = metricas?.casos_posttest ?? 0;
  const tieneDatosAmbasFases = casosPretest > 0 && casosPosttest > 0;
  const totalVerificados = metricas?.total_casos_verificados || metricas?.casos_verificados || metricas?.total_casos || casosRealesTesis.length || 0;

  const dataGraficaReal = tieneDatosAmbasFases && metricas ? [
    {
      indicador: 'Ficha 1: Acierto PPCF (%)',
      'Pre-test (Manual)': metricas.tasa_acierto_pretest_porcentaje,
      'Post-test (CarBot AI)': metricas.tasa_acierto_posttest_porcentaje,
    },
    {
      indicador: 'Ficha 2: Registros PRDC (%)',
      'Pre-test (Manual)': metricas.registros_completos_pretest_porcentaje,
      'Post-test (CarBot AI)': metricas.registros_completos_posttest_porcentaje,
    },
    {
      indicador: 'Ficha 3: Tiempo TPRD (min)',
      'Pre-test (Manual)': metricas.tiempo_promedio_pretest_min,
      'Post-test (CarBot AI)': metricas.tiempo_promedio_posttest_min,
    },
  ] : [];

  const dataComparativaFinal = modoDemoGrafica ? dataComparativaFichas : dataGraficaReal;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingBottom: '32px' }}>
      {/* Encabezado Principal */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-main)', margin: '0 0 4px 0' }}>
            Evaluación del diagnóstico vehicular
          </h1>
          <p style={{ margin: 0, fontSize: '12.5px', color: 'var(--text-secondary)' }}>
            Variable Dependiente · Instrumentos de recolección de datos (Anexo 2: Fichas 1, 2 y 3) · CARTER MOTOR'S E.I.R.L.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
          <Button
            variant="primary"
            size="sm"
            onClick={handleDescargarFichasAnexo2Csv}
            disabled={totalVerificados === 0}
            title={
              totalVerificados === 0
                ? 'No existen registros verificados en taller para exportar'
                : `Descargar Anexo 2 oficial con ${totalVerificados} casos verificados del periodo`
            }
          >
            <FileSpreadsheet size={15} style={{ marginRight: '6px' }} />
            Descargar Anexo 2 ({totalVerificados > 0 ? `${totalVerificados} casos` : 'Sin datos'})
          </Button>
          <Button variant="outline" size="sm" onClick={handleDescargarCsv} title="Descargar datos en bruto">
            <Download size={15} style={{ marginRight: '6px' }} />
            Exportar período (CSV)
          </Button>
          <Button variant="outline" size="sm" onClick={() => setModalAbierto(true)}>
            <Plus size={15} style={{ marginRight: '6px' }} />
            Registrar caso
          </Button>
        </div>
      </div>

      {/* Pestañas de Instrumentos y Fichas Oficiales */}
      <div
        style={{
          display: 'flex',
          gap: '4px',
          backgroundColor: '#f1f5f9',
          padding: '4px',
          borderRadius: '10px',
          overflowX: 'auto',
        }}
      >
        <button
          type="button"
          onClick={() => setTabActiva('resumen')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 14px',
            fontSize: '12px',
            fontWeight: 700,
            borderRadius: '7px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: tabActiva === 'resumen' ? '#ffffff' : 'transparent',
            color: tabActiva === 'resumen' ? 'var(--primary)' : 'var(--text-secondary)',
            boxShadow: tabActiva === 'resumen' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
            whiteSpace: 'nowrap',
            transition: 'all 0.15s ease',
          }}
        >
          <BarChart3 size={14} />
          <span>Comparación Pre / Post</span>
        </button>

        <button
          type="button"
          onClick={() => setTabActiva('ficha1')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 14px',
            fontSize: '12px',
            fontWeight: 700,
            borderRadius: '7px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: tabActiva === 'ficha1' ? '#ffffff' : 'transparent',
            color: tabActiva === 'ficha1' ? 'var(--primary)' : 'var(--text-secondary)',
            boxShadow: tabActiva === 'ficha1' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
            whiteSpace: 'nowrap',
            transition: 'all 0.15s ease',
          }}
        >
          <ClipboardList size={14} />
          <span>Ficha 1: Predicción (PPCF)</span>
        </button>

        <button
          type="button"
          onClick={() => setTabActiva('ficha2')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 14px',
            fontSize: '12px',
            fontWeight: 700,
            borderRadius: '7px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: tabActiva === 'ficha2' ? '#ffffff' : 'transparent',
            color: tabActiva === 'ficha2' ? 'var(--primary)' : 'var(--text-secondary)',
            boxShadow: tabActiva === 'ficha2' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
            whiteSpace: 'nowrap',
            transition: 'all 0.15s ease',
          }}
        >
          <ClipboardList size={14} />
          <span>Ficha 2: Información (PRDC)</span>
        </button>

        <button
          type="button"
          onClick={() => setTabActiva('ficha3')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 14px',
            fontSize: '12px',
            fontWeight: 700,
            borderRadius: '7px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: tabActiva === 'ficha3' ? '#ffffff' : 'transparent',
            color: tabActiva === 'ficha3' ? 'var(--primary)' : 'var(--text-secondary)',
            boxShadow: tabActiva === 'ficha3' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
            whiteSpace: 'nowrap',
            transition: 'all 0.15s ease',
          }}
        >
          <ClipboardList size={14} />
          <span>Ficha 3: Tiempo (TPRD)</span>
        </button>

        <button
          type="button"
          onClick={() => setTabActiva('casos')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 14px',
            fontSize: '12px',
            fontWeight: 700,
            borderRadius: '7px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: tabActiva === 'casos' ? '#ffffff' : 'transparent',
            color: tabActiva === 'casos' ? 'var(--primary)' : 'var(--text-secondary)',
            boxShadow: tabActiva === 'casos' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
            whiteSpace: 'nowrap',
            transition: 'all 0.15s ease',
          }}
        >
          <Search size={14} />
          <span>Tracker de Casos</span>
        </button>
      </div>

      {/* Filtro de Período (visible en Resumen y Tracker de Casos) */}
      {(tabActiva === 'resumen' || tabActiva === 'casos') && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <PeriodoFilter value={periodo} onChange={setPeriodo} />
          <Button variant="outline" size="sm" onClick={cargarDatos} disabled={cargando}>
            Actualizar
          </Button>
        </div>
      )}

      {/* Alertas de Éxito / Error */}
      {exitoMensaje && (
        <div
          style={{
            backgroundColor: '#ecfdf5',
            color: '#065f46',
            border: '1px solid #a7f3d0',
            padding: '12px 16px',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            fontWeight: 500,
          }}
        >
          <CheckCircle size={16} />
          <span>{exitoMensaje}</span>
        </div>
      )}

      {error && (
        <div
          style={{
            backgroundColor: '#fef2f2',
            color: '#991b1b',
            border: '1px solid #fecaca',
            padding: '12px 16px',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
          }}
        >
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Vista 1: Resumen Comparativo de Indicadores */}
      {tabActiva === 'resumen' && (
        <>
          <ValidacionMetricasCards metricas={metricas} />
          <TesisComparativaChart
            data={dataComparativaFinal}
            esModoDemo={modoDemoGrafica}
            onAlternarDemo={() => setModoDemoGrafica((prev) => !prev)}
            tieneDatosAmbasFases={tieneDatosAmbasFases}
            casosPretest={casosPretest}
            casosPosttest={casosPosttest}
          />
        </>
      )}

      {/* Vista 2: Ficha 1 Oficial (PPCF) */}
      {tabActiva === 'ficha1' && <TesisFichaOficialView fichaId="ficha1" casosReales={casosRealesTesis} />}

      {/* Vista 3: Ficha 2 Oficial (PRDC) */}
      {tabActiva === 'ficha2' && <TesisFichaOficialView fichaId="ficha2" casosReales={casosRealesTesis} />}

      {/* Vista 4: Ficha 3 Oficial (TPRD) */}
      {tabActiva === 'ficha3' && <TesisFichaOficialView fichaId="ficha3" casosReales={casosRealesTesis} />}

      {/* Vista 5: Tabla de Casos Experimentales con Filtros Dinámicos */}
      {tabActiva === 'casos' && (
        <ValidacionCasosTable
          casos={casos}
          totalCasos={totalCasos}
          cargando={cargando}
          busqueda={busqueda}
          onBusquedaChange={setBusqueda}
          faseFiltro={faseFiltro}
          onFaseFiltroChange={setFaseFiltro}
          aciertoFiltro={aciertoFiltro}
          onAciertoFiltroChange={setAciertoFiltro}
          pagina={pagina}
          totalPaginas={totalPaginas}
          onCambiarPagina={setPagina}
        />
      )}

      {/* Modal Registrar Nuevo Caso */}
      <ValidacionNuevoCasoModal
        isOpen={modalAbierto}
        onClose={() => setModalAbierto(false)}
        nuevoCaso={nuevoCaso}
        onNuevoCasoChange={setNuevoCaso}
        guardando={guardando}
        onSubmit={handleCrearCaso}
      />
    </div>
  );
};

