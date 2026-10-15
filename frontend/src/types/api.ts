/** Contratos JSON intercambiados con la API FastAPI. */

import type { Diagnostico, Mecanico, MecanicoRol } from './domain';

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
  refresh_token?: string;
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

export type EstadoRegistro = 'borrador' | 'verificado' | 'excluido';
export type TipoRegistro = 'DEVELOPMENT' | 'REGRESSION' | 'THESIS_PRETEST' | 'THESIS_POSTTEST' | 'PILOT';

export interface CasoValidacionDTO {
  id?: string;
  item: number;
  fase: string;
  fecha: string;
  placa_enmascarada: string;
  placa_hash: string;
  marca_modelo: string;
  sintoma: string;
  descripcion_sintoma?: string | null;
  vehiculo_anio?: number | null;
  vehiculo_kilometraje?: number | null;
  vehiculo_combustible?: string | null;
  vehiculo_transmision?: string | null;
  falla_real: string | null;
  chatbot_prediccion: string | null;
  diagnostico_preliminar_sin_chatbot?: string | null;
  falla_sugerida_chatbot?: string | null;
  sistema_afectado_probable?: string | null;
  campos_completos: number;
  cantidad_campos_completos?: number;
  detalles_campos?: Record<string, { nombre: string; completo: boolean; valor_resumen?: string }> | null;
  tiempo_diagnostico_minutos: number | null;
  prediccion_correcta: number | null;
  taller_id?: string;
  mecanico_id?: string;
  metodo_confirmacion?: string | null;
  evidencia_ref?: string | null;
  estado_registro?: EstadoRegistro;
  tipo_registro?: TipoRegistro;
  conversacion_id?: string | null;
  diagnostico_id?: string | null;
  sintoma_registrado_correctamente?: number;
  validado_por_id?: string;
  fecha_validacion?: string;
  normalizacion_correcta?: number;
  extraccion_correcta?: number;
  clasificacion_procesada?: number;
  procesamiento_validado?: number;
  tiempo_inferencia_ml_ms?: number;
  inicio_sistema_at?: string | null;
  fin_sistema_at?: string | null;
  duracion_sistema_segundos?: number | null;
}

export interface CrearCasoValidacionDTO {
  fase: 'Pre-test' | 'Post-test' | 'Piloto';
  fecha?: string;
  placa: string;
  marca_modelo: string;
  sintoma: string;
  descripcion_sintoma?: string;
  vehiculo_anio?: number;
  vehiculo_kilometraje?: number;
  vehiculo_combustible?: string;
  vehiculo_transmision?: string;
  falla_real: string;
  chatbot_prediccion: string;
  sistema_afectado_probable?: string;
  campos_completos: number;
  tiempo_diagnostico_minutos: number;
  prediccion_correcta: number;
  metodo_confirmacion?: string;
  evidencia_ref?: string;
  estado_registro?: EstadoRegistro;
  tipo_registro?: TipoRegistro;
  conversacion_id?: string | null;
  diagnostico_id?: string | null;
  sintoma_registrado_correctamente?: number;
  normalizacion_correcta?: number;
  extraccion_correcta?: number;
  clasificacion_procesada?: number;
  tiempo_inferencia_ml_ms?: number;
  inicio_sistema_at?: string | null;
  fin_sistema_at?: string | null;
  duracion_sistema_segundos?: number | null;
}

export interface ConfirmacionPostTestInput {
  falla_real: string;
  tiempo_diagnostico_minutos: number;
  prediccion_correcta: 0 | 1;
  metodo_confirmacion: string;
  evidencia_ref: string;
  sistema_afectado_probable?: string;
  vehiculo_anio?: number;
  vehiculo_kilometraje?: number;
  vehiculo_combustible?: string;
  vehiculo_transmision?: string;
}

export interface MetricasVariableIndependienteDTO {
  indicador1_sintomas_correctos_pct: number | null;
  indicador2_procesamiento_correcto_pct: number | null;
  indicador3_exactitud_ml_pct: number | null;
  casos_verificados_evaluados: number;
  casos_sintomas_evaluados: number;
  casos_procesamiento_evaluados: number;
  casos_modelo_evaluados: number;
  nota_metodologica: string;
}

export interface MetricasValidacionDTO {
  registros_completos_pretest_porcentaje: number | null;
  registros_completos_posttest_porcentaje: number | null;
  total_casos: number;
  total_aciertos: number;
  total_desaciertos: number;
  tasa_acierto_global_porcentaje: number | null;
  casos_pretest: number;
  predicciones_evaluadas_pretest: number;
  tasa_acierto_pretest_porcentaje: number | null;
  tiempos_evaluados_pretest: number;
  tiempo_promedio_pretest_min: number | null;
  casos_posttest: number;
  predicciones_evaluadas_posttest: number;
  tasa_acierto_posttest_porcentaje: number | null;
  tiempos_evaluados_posttest: number;
  tiempo_promedio_posttest_min: number | null;
  reduccion_tiempo_porcentaje: number | null;
  distribucion_marcas: { marca: string; conteo: number }[];
  top_fallas_reales: { falla: string; conteo: number }[];
  nota_metodologica?: string;
  casos_piloto?: number;
  casos_verificados?: number;
  total_casos_verificados?: number;
  total_casos_borrador?: number;
  variable_independiente?: MetricasVariableIndependienteDTO;
}

export interface AprobarSolicitudResponseDTO {
  mensaje: string;
  solicitud_id: string;
  usuario_id: string;
  nuevo_rol: MecanicoRol;
}
