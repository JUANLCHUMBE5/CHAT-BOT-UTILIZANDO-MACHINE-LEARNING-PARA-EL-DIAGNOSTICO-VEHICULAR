/**
 * Data Transfer Objects (DTOs) para la comunicación Frontend <-> Backend API.
 * Garantiza contratos estrictos de tipo en las capas de transporte HTTP.
 */

// --- Authentication DTOs ---
export interface LoginRequestDTO {
  username: string;
  password: string;
}

export interface TokenResponseDTO {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
  mensaje: string;
  user?: {
    username: string;
    nombre: string;
    rol: string;
    taller_id: string;
    taller_nombre: string;
    requiere_cambio_password: boolean;
  };
}

export interface CambiarPasswordDTO {
  password_actual: string;
  password_nuevo: string;
}

// --- Diagnostic DTOs ---
export interface DiagnosticoResponseDTO {
  id: string;
  sintoma_original: string;
  sintoma_normalizado: string;
  falla_predicha: string;
  confianza: number;
  modo_diagnostico: 'completo_ml_rag_llm' | 'diagnostico_degradado_ml_rag' | 'en_cola_gemini' | 'saludo' | 'baja_confianza' | 'esperando_clarificacion' | 'audio_espectral';
  estado: 'generado' | 'en_revision' | 'confirmado' | 'descartado';
  fuente: 'ml' | 'rag' | 'gemini' | 'hibrido' | 'manual' | 'regla';
  mecanico_id: string;
  mecanico_nombre: string;
  placa_vehiculo_hash: string; // Placa anonimizada vía HMAC-SHA256
  placa_vehiculo_enmascarada: string; // Ej: ABC-***
  marca_modelo: string;
  fecha_hora: string;
  duracion_ms: number;
  procedimiento_rag: string;
  tiempo_gravedad: string;
  sintesis_llm?: string;
  notas_mecanico?: string;
  fecha_confirmacion?: string;
}

export interface ActualizarEstadoDiagnosticoDTO {
  diagnostico_id: string;
  nuevo_estado: 'generado' | 'en_revision' | 'confirmado' | 'descartado';
  notas_mecanico?: string;
}

// --- Mechanic Management DTOs ---
export interface MecanicoCreateDTO {
  nombres: string;
  telefono_whatsapp: string;
  password: string;
  rol: 'mecanico' | 'jefe_taller' | 'administrador';
}

export interface MecanicoResponseDTO {
  id: string;
  nombres: string;
  whatsapp_hash: string;
  whatsapp_ultimos4: string;
  rol: 'mecanico' | 'jefe_taller' | 'administrador';
  activo: boolean;
  bloqueado: boolean;
  fecha_registro: string;
  total_diagnosticos: number;
  ultimo_acceso: string;
}
