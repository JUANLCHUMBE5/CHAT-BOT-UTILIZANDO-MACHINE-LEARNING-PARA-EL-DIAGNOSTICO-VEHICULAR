import type { LoginRequestDTO, TokenResponseDTO } from '../../types';
import {
  API_BASE_URL,
  extractErrorMessage,
  setAccessTokenInMemory,
  getAccessTokenInMemory,
} from './client';

export async function login(payload: LoginRequestDTO): Promise<TokenResponseDTO> {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'Credenciales inválidas'));
  }
  const tokens = (await res.json()) as TokenResponseDTO;
  setAccessTokenInMemory(tokens.access_token);
  return tokens;
}

export async function cambiarPassword(
  token: string,
  passwordActual: string,
  passwordNuevo: string,
): Promise<{ mensaje: string; access_token: string; refresh_token?: string }> {
  const res = await fetch(`${API_BASE_URL}/auth/cambiar-password`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      password_actual: passwordActual,
      password_nuevo: passwordNuevo,
    }),
  });
  if (!res.ok) {
    throw new Error(await extractErrorMessage(res, 'No se pudo cambiar la contraseña'));
  }
  const tokens = (await res.json()) as { mensaje: string; access_token: string; refresh_token?: string };
  setAccessTokenInMemory(tokens.access_token);
  return tokens;
}

export async function logout(): Promise<void> {
  try {
    const headers = new Headers();
    const token = getAccessTokenInMemory();
    if (token) headers.set('Authorization', `Bearer ${token}`);
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers,
      credentials: 'include',
    });
  } finally {
    setAccessTokenInMemory(null);
  }
}
