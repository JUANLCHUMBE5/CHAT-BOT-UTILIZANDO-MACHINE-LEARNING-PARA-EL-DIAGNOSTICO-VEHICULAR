import { apiService } from '../../services/api';

/** Operaciones HTTP exclusivas del panel ejecutivo. */
export const dashboardApi = {
  getResumenMetricas: (fechaInicio?: string, fechaFin?: string, todo = false) =>
    apiService.getResumenMetricas(fechaInicio, fechaFin, todo),
  getMetricasColas: () => apiService.getMetricasColas(),
};
