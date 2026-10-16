import { API_BASE_URL, authFetch, extractErrorMessage } from './client';

export interface ComprobacionResult {
  criterio: string;
  resultado: 'APROBADO' | 'FALLIDO' | 'PENDIENTE';
  evidencia: string;
}

export interface MensajeLabResponse {
  session_id: string;
  case_id: string | null;
  placa: string | null;
  vehiculo: string | null;
  respuesta_texto: string;
  modo_diagnostico: string;
  diagnostico_ml: string | null;
  confianza_ml: number;
  contexto_manual: string | null;
  titulo_manual: string | null;
  similitud_rag: number;
  tiempo_total_ms: number;
  sintomas_confirmados: string[];
  sintomas_negados: string[];
  limitaciones: string[];
  fase: string;
  top3_actual: Array<{ falla: string; probabilidad: number; origen?: string }>;
  comprobaciones: ComprobacionResult[];
}

export interface TurnoReplay {
  turno: number;
  mensaje_enviado: string;
  respuesta: MensajeLabResponse;
}

export interface CasoReplayResponse {
  caso: string;
  session_id: string;
  total_turnos: number;
  resultados: TurnoReplay[];
}

export async function enviarMensajeLaboratorio(
  mensaje: string,
  sessionId?: string,
): Promise<MensajeLabResponse> {
  const response = await authFetch(`${API_BASE_URL}/laboratorio/mensaje`, {
    method: 'POST',
    body: JSON.stringify({ mensaje, session_id: sessionId || '' }),
  });
  if (!response.ok) {
    const errorMsg = await extractErrorMessage(response, `Error ${response.status}: Fallo al procesar mensaje en laboratorio.`);
    throw new Error(errorMsg);
  }
  return (await response.json()) as MensajeLabResponse;
}

export async function reiniciarLaboratorio(sessionId: string): Promise<{ status: string; mensaje: string }> {
  const response = await authFetch(`${API_BASE_URL}/laboratorio/reiniciar?session_id=${encodeURIComponent(sessionId)}`, {
    method: 'POST',
  });
  if (!response.ok) {
    const errorMsg = await extractErrorMessage(response, `Error ${response.status}: No se pudo reiniciar la sesión de prueba.`);
    throw new Error(errorMsg);
  }
  return (await response.json()) as { status: string; mensaje: string };
}

export async function ejecutarCasoPredefinido(casoNombre: 'toyota' | 'nissan'): Promise<CasoReplayResponse> {
  const response = await authFetch(`${API_BASE_URL}/laboratorio/ejecutar-caso/${casoNombre}`, {
    method: 'POST',
  });
  if (!response.ok) {
    const errorMsg = await extractErrorMessage(response, `Error ${response.status}: Fallo al reproducir caso ${casoNombre}.`);
    throw new Error(errorMsg);
  }
  return (await response.json()) as CasoReplayResponse;
}
