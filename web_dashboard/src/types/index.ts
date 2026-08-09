export type ModoDiagnostico =
  | 'completo_ml_rag_llm'
  | 'diagnostico_degradado_ml_rag'
  | 'en_cola_gemini'
  | 'saludo'
  | 'baja_confianza'
  | 'esperando_clarificacion'
  | 'audio_espectral';

export type EstadoDiagnostico = 'generado' | 'en_revision' | 'confirmado' | 'descartado';

export type FuenteDiagnostico = 'ml' | 'rag' | 'gemini' | 'hibrido' | 'manual' | 'regla';

export interface Diagnostico {
  id: string;
  sintoma_original: string;
  sintoma_normalizado: string;
  falla_predicha: string;
  confianza: number; // 0 a 100
  similitud_rag?: number; // 0 a 100
  modo_diagnostico: ModoDiagnostico;
  estado: EstadoDiagnostico;
  fuente: FuenteDiagnostico;
  mecanico_id: string;
  mecanico_nombre: string;
  placa_vehiculo: string;
  marca_modelo: string;
  fecha_hora: string;
  duracion_ms: number;
  procedimiento_rag: string;
  fuente_manual?: string;
  version_corpus_rag?: string;
  tiempo_gravedad: string;
  sintesis_llm?: string;
  notas_mecanico?: string;
  fecha_confirmacion?: string;
}

export interface Mecanico {
  id: string;
  nombres: string;
  telefono: string;
  rol: 'mecanico' | 'jefe_taller' | 'administrador';
  activo: boolean;
  bloqueado: boolean;
  fecha_registro: string;
  total_diagnosticos: number;
  ultimo_acceso: string;
}

export interface ResumenMetricas {
  diagnosticos_hoy: number;
  diagnosticos_semana: number;
  diagnosticos_mes: number;
  porcentaje_confirmados: number;
  tiempo_promedio_ms: number;
  distribucion_modos: { modo: string; cantidad: number }[];
  actividad_diaria: { fecha: string; cantidad: number }[];
  fallas_frecuentes: { falla: string; cantidad: number }[];
}

export interface FiltrosDiagnostico {
  busqueda: string;
  estado: string;
  modo: string;
  mecanicoId: string;
  rangoFecha: 'todos' | 'hoy' | 'semana' | 'mes';
}

export interface UsuarioSesion {
  username: string;
  nombre: string;
  rol: string;
  taller: string;
  token: string;
}
