import { apiService } from '../../../services/api';
import type { MecanicoCreateDTO, MecanicoRol } from '../../../types';

export const mechanicsApi = {
  listar: () => apiService.getMecanicos(),
  registrar: (dto: MecanicoCreateDTO) => apiService.registrarMecanico(dto),
  alternarActivo: (id: string) => apiService.toggleActivarMecanico(id),
  alternarBloqueo: (id: string) => apiService.toggleBloquearMecanico(id),
  eliminar: (id: string) => apiService.eliminarMecanico(id),
  cambiarRol: (id: string, rol: MecanicoRol) => apiService.cambiarRolMecanico(id, rol),
};
