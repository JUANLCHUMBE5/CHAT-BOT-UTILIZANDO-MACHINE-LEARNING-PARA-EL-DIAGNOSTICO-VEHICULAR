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
  telefono_whatsapp: string;
  password?: string;
  rol: MecanicoRol;
}

export interface MecanicoUpdateDTO {
  nombres?: string;
  telefono_whatsapp?: string;
  password?: string;
}

export type MecanicoResponseDTO = Mecanico;

export interface AprobarSolicitudResponseDTO {
  mensaje: string;
  solicitud_id: string;
  usuario_id: string;
  nuevo_rol: MecanicoRol;
}
