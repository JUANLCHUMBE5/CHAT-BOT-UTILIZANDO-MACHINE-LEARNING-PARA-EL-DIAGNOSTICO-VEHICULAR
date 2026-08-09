import type { Diagnostico, Mecanico, ResumenMetricas, UsuarioSesion } from '../types';
import type { LoginRequestDTO, TokenResponseDTO, ActualizarEstadoDiagnosticoDTO, MecanicoCreateDTO } from '../types/dtos';

const API_ORIGIN_OR_BASE = ((import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000/api/v1').replace(/\/$/, '');
const API_BASE_URL = API_ORIGIN_OR_BASE.endsWith('/api/v1')
  ? API_ORIGIN_OR_BASE
  : `${API_ORIGIN_OR_BASE}/api/v1`;

export function getAuthHeaders(): Record<string, string> {
  const sessionStr = localStorage.getItem('carbot_session');
  if (sessionStr) {
    try {
      const session: UsuarioSesion = JSON.parse(sessionStr);
      if (session?.token) {
        return {
          'Authorization': `Bearer ${session.token}`,
          'Content-Type': 'application/json',
        };
      }
    } catch {
      // fallback
    }
  }
  return { 'Content-Type': 'application/json' };
}

export function enmascararIdentificadorSensible(valor: string, tipo: 'placa' | 'telefono'): string {
  if (!valor) return '';
  if (tipo === 'placa') {
    const limpia = valor.replace(/[^A-Za-z0-9]/g, '').toUpperCase();
    if (limpia.length >= 6) {
      return `${limpia.slice(0, 3)}-***`;
    }
    return '***-***';
  } else {
    const ultimos4 = valor.slice(-4);
    return `+51 *** *** ${ultimos4}`;
  }
}

class ApiService {
  async login(payload: LoginRequestDTO): Promise<TokenResponseDTO> {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Error de servidor' }));
      throw new Error(errorData.detail || 'Credenciales inválidas');
    }
    return await res.json();
  }

  async cambiarPassword(
    token: string,
    passwordActual: string,
    passwordNuevo: string,
  ): Promise<{ mensaje: string; access_token: string }> {
    const res = await fetch(`${API_BASE_URL}/auth/cambiar-password`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        password_actual: passwordActual,
        password_nuevo: passwordNuevo,
      }),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Error cambiando contraseña' }));
      throw new Error(errorData.detail || 'No se pudo cambiar la contraseña');
    }
    return await res.json();
  }

  async getResumenMetricas(): Promise<ResumenMetricas> {
    const res = await fetch(`${API_BASE_URL}/metricas/resumen`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Error obteniendo métricas' }));
      throw new Error(errorData.detail || 'Error consultando métricas en PostgreSQL');
    }
    return await res.json();
  }

  async getMecanicos(): Promise<Mecanico[]> {
    const res = await fetch(`${API_BASE_URL}/mecanicos`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Error obteniendo mecánicos' }));
      throw new Error(errorData.detail || 'Error consultando mecánicos en PostgreSQL');
    }
    return await res.json();
  }

  async registrarMecanico(data: MecanicoCreateDTO): Promise<Mecanico> {
    const res = await fetch(`${API_BASE_URL}/mecanicos`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Error registrando mecánico' }));
      throw new Error(errorData.detail || 'No se pudo registrar el mecánico en PostgreSQL');
    }
    return await res.json();
  }

  async toggleActivarMecanico(id: string): Promise<Mecanico> {
    const res = await fetch(`${API_BASE_URL}/mecanicos/${id}/activar`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Error al cambiar estado' }));
      throw new Error(errorData.detail || 'No se pudo actualizar el estado del mecánico');
    }
    return await res.json();
  }

  async toggleBloquearMecanico(id: string): Promise<Mecanico> {
    const res = await fetch(`${API_BASE_URL}/mecanicos/${id}/bloquear`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Error al bloquear mecánico' }));
      throw new Error(errorData.detail || 'No se pudo bloquear el mecánico');
    }
    return await res.json();
  }

  async eliminarMecanico(id: string): Promise<{ mensaje: string }> {
    const res = await fetch(`${API_BASE_URL}/mecanicos/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Error al eliminar mecánico' }));
      throw new Error(errorData.detail || 'No se pudo eliminar el mecánico');
    }
    return await res.json();
  }

  async cambiarRolMecanico(id: string, nuevo_rol: 'mecanico' | 'jefe_taller' | 'administrador'): Promise<Mecanico> {
    const res = await fetch(`${API_BASE_URL}/mecanicos/${id}/rol`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify({ nuevo_rol }),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Error al cambiar rol del mecánico' }));
      throw new Error(errorData.detail || 'No se pudo cambiar el rol del mecánico');
    }
    return await res.json();
  }

  async getDiagnosticos(params?: {
    busqueda?: string;
    estado?: string;
    modo?: string;
    mecanico_id?: string;
  }): Promise<Diagnostico[]> {
    const url = new URL(`${API_BASE_URL}/diagnostico/historial`);
    if (params) {
      if (params.busqueda) url.searchParams.append('busqueda', params.busqueda);
      if (params.estado) url.searchParams.append('estado', params.estado);
      if (params.modo) url.searchParams.append('modo', params.modo);
      if (params.mecanico_id) url.searchParams.append('mecanico_id', params.mecanico_id);
    }

    const res = await fetch(url.toString(), {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Error obteniendo historial' }));
      throw new Error(errorData.detail || 'Error consultando diagnósticos en PostgreSQL');
    }
    return await res.json();
  }

  async actualizarEstadoDiagnostico(
    dto: ActualizarEstadoDiagnosticoDTO
  ): Promise<{ mensaje: string }> {
    const res = await fetch(`${API_BASE_URL}/diagnostico/${dto.diagnostico_id}/confirmar`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        nuevo_estado: dto.nuevo_estado,
        notas_mecanico: dto.notas_mecanico,
      }),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Error al confirmar diagnóstico' }));
      throw new Error(errorData.detail || 'No se pudo confirmar el diagnóstico en PostgreSQL');
    }
    return await res.json();
  }
}

export const apiService = new ApiService();
