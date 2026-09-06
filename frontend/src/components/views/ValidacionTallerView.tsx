import React from 'react';
import { Download, Plus, AlertTriangle, CheckCircle } from 'lucide-react';
import { Button } from '../common/Button';
import { PeriodoFilter } from '../common/PeriodoFilter';
import { useValidacionTaller } from '../../hooks/useValidacionTaller';
import {
  ValidacionMetricasCards,
  ValidacionCasosTable,
  ValidacionNuevoCasoModal,
} from './validacion';

export const ValidacionTallerView: React.FC = () => {
  const {
    metricas,
    casos,
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
    periodo,
    setPeriodo,
    cargarDatos,
  } = useValidacionTaller();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', paddingBottom: '32px' }}>
      {/* Encabezado Principal */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-main)', margin: '0 0 4px 0' }}>
            Fichas de evaluación
          </h1>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <Button variant="outline" size="sm" onClick={handleDescargarCsv}>
            <Download size={15} style={{ marginRight: '6px' }} />
            Exportar período
          </Button>
          <Button variant="primary" size="sm" onClick={() => setModalAbierto(true)}>
            <Plus size={15} style={{ marginRight: '6px' }} />
            Registrar caso
          </Button>
        </div>
      </div>

      <PeriodoFilter value={periodo} onChange={setPeriodo} />
      <div><Button variant="outline" size="sm" onClick={cargarDatos} disabled={cargando}>Actualizar</Button></div>

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

      {/* 1. Tarjetas Resumen de Métricas (Pre vs Post) */}
      <ValidacionMetricasCards metricas={metricas} />

      {/* 2. Tabla de Casos Experimentales con Filtros */}
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

      {/* 3. Modal Registrar Nuevo Caso */}
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
