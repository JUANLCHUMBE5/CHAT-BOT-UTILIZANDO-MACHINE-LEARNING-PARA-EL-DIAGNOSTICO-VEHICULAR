export const MODO_LABELS: Record<string, string> = {
  completo_ml_rag_llm: 'Completo (IA + RAG)',
  diagnostico_degradado_ml_rag: 'Base (ML + RAG)',
  base_arboles_decision: 'Árboles de Decisión',
  base_arboles_decisión: 'Árboles de Decisión',
  evaluacion_reglas_expertas: 'Reglas Expertas',
  rapido_patrones_frecuentes: 'Patrones Frecuentes',
  en_cola_gemini: 'En Cola IA',
  saludo: 'Interacción Inicial',
  baja_confianza: 'Baja Confianza',
  esperando_clarificacion: 'Esperando Clarificación',
  audio_espectral: 'Análisis de Audio',
};

export const getModoLabel = (modo?: string | null): string => {
  if (!modo) return 'Sin Modo';
  return MODO_LABELS[modo] || modo.replace(/_/g, ' ');
};
