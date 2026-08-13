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

export type MecanicoRol = 'mecanico' | 'jefe_taller' | 'administrador';

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
  rol: MecanicoRol;
  activo: boolean;
  bloqueado: boolean;
  fecha_registro: string;
  total_diagnosticos: number;
  ultimo_acceso: string;
}

export interface Cliente {
  id: string;
  nombres: string;
  telefono: string;
  tipo_identificador: string;
  activo: boolean;
  bloqueado: boolean;
  fecha_registro: string;
  ultima_interaccion: string;
  tiene_solicitud_pendiente: boolean;
  solicitud_id?: string;
}

export interface SolicitudAcceso {
  id: string;
  usuario_id: string;
  usuario_nombre: string;
  telefono: string;
  rol_solicitado: string;
  estado: 'pendiente' | 'aprobada' | 'rechazada';
  solicitado_en: string;
  revisado_por?: string;
  revisado_en?: string;
  observaciones?: string;
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
