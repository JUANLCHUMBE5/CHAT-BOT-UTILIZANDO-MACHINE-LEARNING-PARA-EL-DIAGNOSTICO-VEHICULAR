import React, { useState } from 'react';
import {
  Download,
  Plus,
  AlertTriangle,
  CheckCircle,
  ClipboardList,
  Search,
} from 'lucide-react';
import { Button } from '../common/Button';
import { useValidacionTaller } from '../../hooks/useValidacionTaller';
import {
  ValidacionCasosTable,
  ValidacionNuevoCasoModal,
} from './validacion';
import { TesisFichaOficialView } from './proyecto/tesis/TesisFichaOficialView';
import type { RegistroTesis } from '../../data/fichasTesisData';

type TabEvaluacion = 'casos' | 'ficha1' | 'ficha2' | 'ficha3';

export const ValidacionTallerView: React.FC = () => {
  const [tabActiva, setTabActiva] = useState<TabEvaluacion>('casos');

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
    handleDescargarFichasAnexo2Csv,
  } = useValidacionTaller();

  // Mapeo de casos reales desde la API a la interfaz de registros de tesis
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
  const totalVerificados = metricas?.total_casos_verificados || metricas?.casos_verificados || metricas?.total_casos || casosRealesTesis.length || 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', paddingBottom: '32px' }}>
      {/* Encabezado Principal Limpio */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-main)', margin: '0 0 2px 0' }}>
            Fichas e Instrumentos de Taller (Anexo 2)
          </h1>
          <p style={{ margin: 0, fontSize: '12.5px', color: 'var(--text-secondary)' }}>
            CARTER MOTOR'S E.I.R.L. · Recolección oficial del estudio preexperimental
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
          <Button variant="primary" size="sm" onClick={() => setModalAbierto(true)}>
            <Plus size={15} style={{ marginRight: '6px' }} />
            Registrar caso
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDescargarFichasAnexo2Csv}
            disabled={totalVerificados === 0}
            title={
              totalVerificados === 0
                ? 'No existen registros verificados en taller para exportar'
                : `Exportar Anexo 2 oficial con ${totalVerificados} casos verificados`
            }
          >
            <Download size={15} style={{ marginRight: '6px' }} />
            Exportar Anexo 2 (CSV)
          </Button>
        </div>
      </div>

      {/* Banner de Estado Oficial (Regla 2 obligatoria de AGENTS.md) */}
      <div
        style={{
          padding: '10px 14px',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: '#f8fafc',
          border: '1px solid #e2e8f0',
          flexWrap: 'wrap',
          gap: '10px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={16} style={{ color: '#059669', flexShrink: 0 }} />
          <span style={{ fontSize: '12px', color: '#334155' }}>
            <strong>Trabajo de campo pendiente.</strong> Los resultados pretest y postest se calcularán exclusivamente con registros reales recopilados y verificados durante la aplicación de los instrumentos. <strong>Avance actual: {casosPretest + casosPosttest} de 60 registros.</strong>
          </span>
        </div>
        <div style={{ display: 'flex', gap: '6px', fontSize: '11px', fontWeight: 700 }}>
          <span style={{ backgroundColor: '#f0fdf4', color: '#166534', border: '1px solid #bbf7d0', padding: '2px 8px', borderRadius: '4px' }}>
            Pre-test: {casosPretest}/30
          </span>
          <span style={{ backgroundColor: '#eff6ff', color: '#1e40af', border: '1px solid #bfdbfe', padding: '2px 8px', borderRadius: '4px' }}>
            Post-test: {casosPosttest}/30
          </span>
        </div>
      </div>

      {/* Pestañas de los 4 Instrumentos Oficiales */}
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
          <span>Lista de Casos (Tracker)</span>
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
          <span>Ficha 3: Eficiencia y Tiempo (TPRD)</span>
        </button>
      </div>

      {/* Alertas de Éxito / Error */}
      {exitoMensaje && (
        <div
          style={{
            backgroundColor: '#ecfdf5',
            color: '#065f46',
            border: '1px solid #a7f3d0',
            padding: '10px 14px',
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
            padding: '10px 14px',
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

      {/* Vista 1: Tabla de Casos Experimentales con Filtros Dinámicos */}
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

      {/* Vista 2: Ficha 1 Oficial (PPCF) */}
      {tabActiva === 'ficha1' && <TesisFichaOficialView fichaId="ficha1" casosReales={casosRealesTesis} />}

      {/* Vista 3: Ficha 2 Oficial (PRDC) */}
      {tabActiva === 'ficha2' && <TesisFichaOficialView fichaId="ficha2" casosReales={casosRealesTesis} />}

      {/* Vista 4: Ficha 3 Oficial (TPRD) */}
      {tabActiva === 'ficha3' && <TesisFichaOficialView fichaId="ficha3" casosReales={casosRealesTesis} />}

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
