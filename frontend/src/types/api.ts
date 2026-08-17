/** Contratos JSON intercambiados con la API FastAPI. */

import type { Diagnostico, EstadoDiagnostico, Mecanico, MecanicoRol } from './domain';

export interface LoginRequestDTO {
  username: string;
  password: string;
}

export interface TokenUserDTO {
  id?: string;
  usuario_id?: string;
  username: string;
  nombre: string;
  rol: string;
  taller_id: string;
  taller_nombre: string;
  requiere_cambio_password: boolean;
}

export interface TokenResponseDTO {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in_seconds: number;
  refresh_expires_in_seconds: number;
  mensaje: string;
  user?: TokenUserDTO;
}

export interface CambiarPasswordDTO {
  password_actual: string;
  password_nuevo: string;
}

export type DiagnosticoHistorialResponseDTO = Diagnostico;

export interface ActualizarEstadoDiagnosticoDTO {
  diagnostico_id: string;
  nuevo_estado: EstadoDiagnostico;
  notas_mecanico?: string;
}

export interface MecanicoCreateDTO {
  nombres: string;
  username?: string;
  telefono_whatsapp: string;
  password?: string;
  rol: MecanicoRol;
}

export interface MecanicoUpdateDTO {
  nombres?: string;
  username?: string;
  telefono_whatsapp?: string;
  password?: string;
}

export type MecanicoResponseDTO = Mecanico;

export interface CasoValidacionDTO {
  item: number;
  fase: string;
  fecha: string;
  placa: string;
  marca_modelo: string;
  sintoma: string;
  falla_real: string;
  chatbot_prediccion: string;
  campos_completos: number;
  tiempo_diagnostico_minutos: number;
  prediccion_correcta: number;
}

export interface CrearCasoValidacionDTO {
  fase: string;
  fecha?: string;
  placa: string;
  marca_modelo: string;
  sintoma: string;
  falla_real: string;
  chatbot_prediccion: string;
  campos_completos: number;
  tiempo_diagnostico_minutos: number;
  prediccion_correcta: number;
}

export interface MetricasValidacionDTO {
  total_casos: number;
  total_aciertos: number;
  total_desaciertos: number;
  tasa_acierto_global_porcentaje: number;
  casos_pretest: number;
  tasa_acierto_pretest_porcentaje: number;
  tiempo_promedio_pretest_min: number;
  casos_posttest: number;
  tasa_acierto_posttest_porcentaje: number;
  tiempo_promedio_posttest_min: number;
  reduccion_tiempo_porcentaje: number;
  distribucion_marcas: { marca: string; conteo: number }[];
  top_fallas_reales: { falla: string; conteo: number }[];
}

export interface AprobarSolicitudResponseDTO {
  mensaje: string;
  solicitud_id: string;
  usuario_id: string;
  nuevo_rol: MecanicoRol;
}
