import React, { useState } from 'react';
import { AlertCircle } from 'lucide-react';
import {
  apiService,
  type MensajeLabResponse,
} from '../../services/api';
import { LaboratorioHeader } from './components/LaboratorioHeader';
import { LaboratorioChat, type ChatEntry } from './components/LaboratorioChat';
import { LaboratorioPanel } from './components/LaboratorioPanel';

export const LaboratorioView: React.FC = () => {
  const [sessionId, setSessionId] = useState<string>(() => `lab_${Date.now().toString(36)}`);
  const [inputMensaje, setInputMensaje] = useState<string>('');
  const [historial, setHistorial] = useState<ChatEntry[]>([]);
  const [estadoActual, setEstadoActual] = useState<MensajeLabResponse | null>(null);
  const [cargando, setCargando] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [casoEnEjecucion, setCasoEnEjecucion] = useState<string | null>(null);

  const enviarMensaje = async (texto: string) => {
    if (!texto.trim() || cargando) return;
    setError(null);
    setCargando(true);

    const hora = new Date().toLocaleTimeString();
    const entryUsuario: ChatEntry = {
      emisor: 'usuario',
      texto,
      timestamp: hora,
    };
    setHistorial((prev) => [...prev, entryUsuario]);
    setInputMensaje('');

    try {
      const res = await apiService.enviarMensajeLaboratorio(texto, sessionId);
      setEstadoActual(res);
      setHistorial((prev) => [
        ...prev,
        {
          emisor: 'carbot',
          texto: res.respuesta_texto,
          tiempoMs: res.tiempo_total_ms,
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error desconocido al procesar el mensaje';
      setError(msg);
    } finally {
      setCargando(false);
    }
  };

  const reproducirCaso = async (caso: 'toyota' | 'nissan') => {
    if (cargando) return;
    setError(null);
    setCargando(true);
    setCasoEnEjecucion(caso);

    try {
      const res = await apiService.ejecutarCasoPredefinido(caso);
      setSessionId(res.session_id);

      const nuevosEntries: ChatEntry[] = [];
      res.resultados.forEach((r) => {
        nuevosEntries.push({
          emisor: 'usuario',
          texto: r.mensaje_enviado,
          timestamp: new Date().toLocaleTimeString(),
        });
        nuevosEntries.push({
          emisor: 'carbot',
          texto: r.respuesta.respuesta_texto,
          tiempoMs: r.respuesta.tiempo_total_ms,
          timestamp: new Date().toLocaleTimeString(),
        });
      });

      setHistorial(nuevosEntries);
      if (res.resultados.length > 0) {
        setEstadoActual(res.resultados[res.resultados.length - 1].respuesta);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : `Error al reproducir caso ${caso}`;
      setError(msg);
    } finally {
      setCargando(false);
      setCasoEnEjecucion(null);
    }
  };

  const reiniciarSesion = async () => {
    if (cargando) return;
    setCargando(true);
    setError(null);
    try {
      await apiService.reiniciarLaboratorio(sessionId);
      const nuevaSesion = `lab_${Date.now().toString(36)}`;
      setSessionId(nuevaSesion);
      setHistorial([]);
      setEstadoActual(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'No se pudo reiniciar la sesión';
      setError(msg);
    } finally {
      setCargando(false);
    }
  };

  const exportarResultadosJson = () => {
    const payload = {
      exportado_en: new Date().toISOString(),
      session_id: sessionId,
      caso_id: estadoActual?.case_id || null,
      placa: estadoActual?.placa || null,
      vehiculo: estadoActual?.vehiculo || null,
      historial,
      estado_final: estadoActual,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `carbot_lab_${sessionId}_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', height: '100%' }}>
      <LaboratorioHeader
        cargando={cargando}
        casoEnEjecucion={casoEnEjecucion}
        tieneHistorial={historial.length > 0}
        onReproducirCaso={reproducirCaso}
        onReiniciar={reiniciarSesion}
        onExportarJson={exportarResultadosJson}
      />

      {error && (
        <div
          style={{
            background: '#fef2f2',
            color: '#b91c1c',
            border: '1px solid #fecaca',
            padding: '12px 16px',
            borderRadius: '8px',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(420px, 1fr) minmax(380px, 1fr)',
          gap: '20px',
          flex: 1,
          minHeight: 0,
        }}
      >
        <LaboratorioChat
          sessionId={sessionId}
          historial={historial}
          inputMensaje={inputMensaje}
          cargando={cargando}
          onInputChange={setInputMensaje}
          onEnviar={enviarMensaje}
        />

        <LaboratorioPanel estado={estadoActual} />
      </div>
    </div>
  );
};
