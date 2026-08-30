import { apiService } from '../../../services/api';
import type { ActualizarEstadoDiagnosticoDTO } from '../../../types';

export const diagnosticsApi = {
  listar: (filtros?: {
    busqueda?: string;
    estado?: string;
    modo?: string;
    mecanico_id?: string;
  }) => apiService.getDiagnosticos(filtros),
  actualizarEstado: (dto: ActualizarEstadoDiagnosticoDTO) =>
    apiService.actualizarEstadoDiagnostico(dto),
};
