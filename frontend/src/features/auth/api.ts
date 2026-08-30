import { apiService } from '../../services/api';
import type { LoginRequestDTO } from '../../types';

export const authApi = {
  login: (dto: LoginRequestDTO) => apiService.login(dto),
  cambiarPassword: (token: string, actual: string, nueva: string) =>
    apiService.cambiarPassword(token, actual, nueva),
  establecerAccessToken: (token: string | null) => apiService.setAccessToken(token),
  logout: () => apiService.logout(),
};
