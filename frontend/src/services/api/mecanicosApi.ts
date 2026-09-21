import type {
  AprobarSolicitudResponseDTO,
  Cliente,
  Mecanico,
  MecanicoCreateDTO,
  MecanicoResponseDTO,
  MecanicoRol,
  MecanicoUpdateDTO,
  SolicitudAcceso,
} from '../../types';
import {
  API_BASE_URL,
  authFetch,
  getAuthHeaders,
  extractErrorMessage,
} from './client';

export async function getMecanicos(): Promise<Mecanico[]> {
  const res = await authFetch(`${API_BASE_URL}/mecanicos`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'Error consultando mecánicos en PostgreSQL'));
  }
  return (await res.json()) as Mecanico[];
}

export async function registrarMecanico(data: MecanicoCreateDTO): Promise<Mecanico> {
  const res = await authFetch(`${API_BASE_URL}/mecanicos`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'No se pudo registrar el mecánico en PostgreSQL'));
  }
  return (await res.json()) as Mecanico;
}

export async function actualizarMecanico(id: string, data: MecanicoUpdateDTO): Promise<MecanicoResponseDTO> {
  const res = await authFetch(`${API_BASE_URL}/mecanicos/${id}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'No se pudo actualizar el perfil del mecánico'));
  }
  return (await res.json()) as MecanicoResponseDTO;
}

export async function toggleActivarMecanico(id: string): Promise<Mecanico> {
  const res = await authFetch(`${API_BASE_URL}/mecanicos/${id}/activar`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'No se pudo actualizar el estado del mecánico'));
  }
  return (await res.json()) as Mecanico;
}

export async function toggleBloquearMecanico(id: string): Promise<Mecanico> {
  const res = await authFetch(`${API_BASE_URL}/mecanicos/${id}/bloquear`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'No se pudo bloquear el mecánico'));
  }
  return (await res.json()) as Mecanico;
}

export async function revocarAccesoMecanico(id: string): Promise<{ mensaje: string }> {
  const res = await authFetch(`${API_BASE_URL}/mecanicos/${id}/revocar-acceso`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'No se pudo revocar el acceso técnico del mecánico'));
  }
  return (await res.json()) as { mensaje: string };
}

export async function cambiarRolMecanico(id: string, nuevo_rol: MecanicoRol, password?: string): Promise<Mecanico> {
  const res = await authFetch(`${API_BASE_URL}/mecanicos/${id}/rol`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify({ nuevo_rol, password }),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'No se pudo cambiar el rol del mecánico'));
  }
  return (await res.json()) as Mecanico;
}

export async function getClientes(busqueda?: string): Promise<Cliente[]> {
  const url = new URL(`${API_BASE_URL}/clientes`);
  if (busqueda) {
    url.searchParams.append('busqueda', busqueda);
  }
  const res = await authFetch(url.toString(), {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'Error consultando clientes en PostgreSQL'));
  }
  return (await res.json()) as Cliente[];
}

export async function toggleBloquearCliente(id: string): Promise<{ mensaje: string; bloqueado: boolean }> {
  const res = await authFetch(`${API_BASE_URL}/clientes/${id}/bloquear`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'No se pudo actualizar el estado del cliente'));
  }
  return (await res.json()) as { mensaje: string; bloqueado: boolean };
}

export async function getSolicitudesAcceso(estado?: string): Promise<SolicitudAcceso[]> {
  const url = new URL(`${API_BASE_URL}/clientes/solicitudes/listar`);
  if (estado) {
    url.searchParams.append('estado', estado);
  }
  const res = await authFetch(url.toString(), {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'Error consultando solicitudes de acceso'));
  }
  return (await res.json()) as SolicitudAcceso[];
}

export async function aprobarSolicitudAcceso(id: string): Promise<AprobarSolicitudResponseDTO> {
  const res = await authFetch(`${API_BASE_URL}/clientes/solicitudes/${id}/aprobar`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'No se pudo aprobar la solicitud'));
  }
  return (await res.json()) as AprobarSolicitudResponseDTO;
}

export async function rechazarSolicitudAcceso(id: string, motivo?: string): Promise<{ mensaje: string }> {
  const res = await authFetch(`${API_BASE_URL}/clientes/solicitudes/${id}/rechazar`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ motivo }),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'No se pudo rechazar la solicitud'));
  }
  return (await res.json()) as { mensaje: string };
}
