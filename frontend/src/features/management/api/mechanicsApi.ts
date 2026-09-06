import { apiService } from '../../../services/api';
import type { MecanicoCreateDTO, MecanicoRol } from '../../../types';

export const mechanicsApi = {
  listar: () => apiService.getMecanicos(),
  registrar: (dto: MecanicoCreateDTO) => apiService.registrarMecanico(dto),
  alternarActivo: (id: string) => apiService.toggleActivarMecanico(id),
  alternarBloqueo: (id: string) => apiService.toggleBloquearMecanico(id),
  revocar: (id: string) => apiService.revocarAccesoMecanico(id),
  eliminar: (id: string) => apiService.revocarAccesoMecanico(id),
  cambiarRol: (id: string, rol: MecanicoRol) => apiService.cambiarRolMecanico(id, rol),
};
