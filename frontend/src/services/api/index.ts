import type {
  AprobarSolicitudResponseDTO,
  CasoValidacionDTO,
  Cliente,
  CrearCasoValidacionDTO,
  Diagnostico,
  LoginRequestDTO,
  Mecanico,
  MecanicoCreateDTO,
  MecanicoResponseDTO,
  MecanicoUpdateDTO,
  MecanicoRol,
  MetricasValidacionDTO,
  MetricasCola,
  ResumenMetricas,
  SolicitudAcceso,
  TokenResponseDTO,
} from '../../types';

import {
  API_BASE_URL,
  SESSION_UPDATED_EVENT,
  SESSION_EXPIRED_EVENT,
  enmascararIdentificadorSensible,
  getAuthHeaders,
  setAccessTokenInMemory,
} from './client';

import { login, cambiarPassword, logout } from './authApi';
import { getDiagnosticos, getResumenMetricas, getMetricasColas, getConversacionDiagnostico } from './diagnosticosApi';
import {
  getMecanicos,
  registrarMecanico,
  actualizarMecanico,
  toggleActivarMecanico,
  toggleBloquearMecanico,
  revocarAccesoMecanico,
  cambiarRolMecanico,
  getClientes,
  toggleBloquearCliente,
  getSolicitudesAcceso,
  aprobarSolicitudAcceso,
  rechazarSolicitudAcceso,
} from './mecanicosApi';
import {
  getCasosValidacion,
  getMetricasValidacion,
  crearCasoValidacion,
  crearBorradorPosttest,
  confirmarPosttest,
  getExportarTrackerCsvUrl,
  descargarValidacionCsv,
  getExportarFichasAnexo2CsvUrl,
  descargarFichasAnexo2Csv,
} from './validacionApi';
import {
  getHealthReady,
  getTrabajosFallidos,
  reintentarTrabajoFallido,
} from './colaApi';

class ApiService {
  setAccessToken(token: string | null): void {
    setAccessTokenInMemory(token);
  }

  login(payload: LoginRequestDTO): Promise<TokenResponseDTO> {
    return login(payload);
  }

  cambiarPassword(
    token: string,
    passwordActual: string,
    passwordNuevo: string,
  ): Promise<{ mensaje: string; access_token: string; refresh_token?: string }> {
    return cambiarPassword(token, passwordActual, passwordNuevo);
  }

  logout(): Promise<void> {
    return logout();
  }

  getResumenMetricas(fechaInicio?: string, fechaFin?: string, todo = false): Promise<ResumenMetricas> {
    return getResumenMetricas(fechaInicio, fechaFin, todo);
  }

  getMetricasColas(): Promise<MetricasCola> {
    return getMetricasColas();
  }

  getMecanicos(): Promise<Mecanico[]> {
    return getMecanicos();
  }

  registrarMecanico(data: MecanicoCreateDTO): Promise<Mecanico> {
    return registrarMecanico(data);
  }

  actualizarMecanico(id: string, data: MecanicoUpdateDTO): Promise<MecanicoResponseDTO> {
    return actualizarMecanico(id, data);
  }

  toggleActivarMecanico(id: string): Promise<Mecanico> {
    return toggleActivarMecanico(id);
  }

  toggleBloquearMecanico(id: string): Promise<Mecanico> {
    return toggleBloquearMecanico(id);
  }

  revocarAccesoMecanico(id: string): Promise<{ mensaje: string }> {
    return revocarAccesoMecanico(id);
  }

  eliminarMecanico(id: string): Promise<{ mensaje: string }> {
    return revocarAccesoMecanico(id);
  }

  cambiarRolMecanico(id: string, nuevo_rol: MecanicoRol, password?: string): Promise<Mecanico> {
    return cambiarRolMecanico(id, nuevo_rol, password);
  }

  getDiagnosticos(params?: {
    busqueda?: string;
    estado?: string;
    modo?: string;
    mecanico_id?: string;
    limite?: number;
    offset?: number;
    fecha_desde?: string;
    fecha_hasta?: string;
  }): Promise<{ items: Diagnostico[]; total: number }> {
    return getDiagnosticos(params);
  }

  getConversacionDiagnostico(diagnosticoId: string): Promise<import('../../types').MensajeConversacion[]> {
    return getConversacionDiagnostico(diagnosticoId);
  }

  getClientes(busqueda?: string): Promise<Cliente[]> {
    return getClientes(busqueda);
  }

  toggleBloquearCliente(id: string): Promise<{ mensaje: string; bloqueado: boolean }> {
    return toggleBloquearCliente(id);
  }

  getSolicitudesAcceso(estado?: string): Promise<SolicitudAcceso[]> {
    return getSolicitudesAcceso(estado);
  }

  aprobarSolicitudAcceso(id: string): Promise<AprobarSolicitudResponseDTO> {
    return aprobarSolicitudAcceso(id);
  }

  rechazarSolicitudAcceso(id: string, motivo?: string): Promise<{ mensaje: string }> {
    return rechazarSolicitudAcceso(id, motivo);
  }

  getHealthReady() {
    return getHealthReady();
  }

  getTrabajosFallidos(limite: number = 20) {
    return getTrabajosFallidos(limite);
  }

  reintentarTrabajoFallido(trabajoId: string) {
    return reintentarTrabajoFallido(trabajoId);
  }

  getCasosValidacion(params?: {
    fecha_desde?: string;
    fecha_hasta?: string;
    fase?: string;
    marca?: string;
    acierto?: number;
    busqueda?: string;
    skip?: number;
    limit?: number;
  }) {
    return getCasosValidacion(params);
  }

  getMetricasValidacion(periodo: { fecha_desde?: string; fecha_hasta?: string } = {}): Promise<MetricasValidacionDTO> {
    return getMetricasValidacion(periodo);
  }

  crearCasoValidacion(dto: CrearCasoValidacionDTO): Promise<CasoValidacionDTO> {
    return crearCasoValidacion(dto);
  }

  crearBorradorPosttest(diagnosticoId: string): Promise<CasoValidacionDTO> {
    return crearBorradorPosttest(diagnosticoId);
  }

  confirmarPosttest(casoId: string, datos: { falla_real: string; tiempo_diagnostico_minutos: number; prediccion_correcta: 0 | 1; metodo_confirmacion: string; evidencia_ref?: string }): Promise<CasoValidacionDTO> {
    return confirmarPosttest(casoId, datos);
  }

  getExportarTrackerCsvUrl(): string {
    return getExportarTrackerCsvUrl();
  }

  descargarValidacionCsv(periodo: { fecha_desde?: string; fecha_hasta?: string }): Promise<void> {
    return descargarValidacionCsv(periodo);
  }

  getExportarFichasAnexo2CsvUrl(): string {
    return getExportarFichasAnexo2CsvUrl();
  }

  descargarFichasAnexo2Csv(periodo: { fecha_desde?: string; fecha_hasta?: string }): Promise<void> {
    return descargarFichasAnexo2Csv(periodo);
  }
}

export const apiService = new ApiService();

export {
  API_BASE_URL,
  SESSION_UPDATED_EVENT,
  SESSION_EXPIRED_EVENT,
  enmascararIdentificadorSensible,
  getAuthHeaders,
  login,
  cambiarPassword,
  logout,
  getResumenMetricas,
  getMetricasColas,
  getDiagnosticos,
  getConversacionDiagnostico,
  getMecanicos,
  registrarMecanico,
  actualizarMecanico,
  toggleActivarMecanico,
  toggleBloquearMecanico,
  revocarAccesoMecanico,
  cambiarRolMecanico,
  getClientes,
  toggleBloquearCliente,
  getSolicitudesAcceso,
  aprobarSolicitudAcceso,
  rechazarSolicitudAcceso,
  getHealthReady,
  getTrabajosFallidos,
  reintentarTrabajoFallido,
  getCasosValidacion,
  getMetricasValidacion,
  crearCasoValidacion,
  crearBorradorPosttest,
  confirmarPosttest,
  getExportarTrackerCsvUrl,
  descargarValidacionCsv,
  getExportarFichasAnexo2CsvUrl,
  descargarFichasAnexo2Csv,
};
