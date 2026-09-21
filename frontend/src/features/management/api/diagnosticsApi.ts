import { apiService } from '../../../services/api';

export const diagnosticsApi = {
  listar: (filtros?: {
    busqueda?: string;
    estado?: string;
    modo?: string;
    mecanico_id?: string;
    limite?: number;
    offset?: number;
    fecha_desde?: string;
    fecha_hasta?: string;
  }) => apiService.getDiagnosticos(filtros),
};
