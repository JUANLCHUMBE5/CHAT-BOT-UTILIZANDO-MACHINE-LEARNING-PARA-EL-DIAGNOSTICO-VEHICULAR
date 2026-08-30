import { apiService } from '../../services/api';

/** Operaciones HTTP exclusivas del panel ejecutivo. */
export const dashboardApi = {
  getResumenMetricas: (fechaInicio?: string, fechaFin?: string) =>
    apiService.getResumenMetricas(fechaInicio, fechaFin),
};
