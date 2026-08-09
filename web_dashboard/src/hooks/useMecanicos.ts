import { useState, useCallback } from 'react';
import { apiService } from '../services/api';
import type { Mecanico } from '../types';

export function useMecanicos() {
  const [mecanicos, setMecanicos] = useState<Mecanico[]>([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cargarMecanicos = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const data = await apiService.getMecanicos();
      setMecanicos(data);
    } catch (err: any) {
      setError(err?.message || 'Error al cargar los mecánicos del taller');
    } finally {
      setCargando(false);
    }
  }, []);

  const registrarMecanico = useCallback(async (data: {
    nombres: string;
    telefono: string;
    password: string;
    rol: 'mecanico' | 'jefe_taller' | 'administrador';
  }) => {
    await apiService.registrarMecanico({
      nombres: data.nombres,
      telefono_whatsapp: data.telefono,
      password: data.password,
      rol: data.rol,
    });
    await cargarMecanicos();
  }, [cargarMecanicos]);

  const toggleActivar = useCallback(async (id: string) => {
    await apiService.toggleActivarMecanico(id);
    await cargarMecanicos();
  }, [cargarMecanicos]);

  const toggleBloquear = useCallback(async (id: string) => {
    await apiService.toggleBloquearMecanico(id);
    await cargarMecanicos();
  }, [cargarMecanicos]);

  const eliminarMecanico = useCallback(async (id: string) => {
    await apiService.eliminarMecanico(id);
    await cargarMecanicos();
  }, [cargarMecanicos]);

  const cambiarRol = useCallback(async (id: string, nuevoRol: 'mecanico' | 'jefe_taller' | 'administrador') => {
    await apiService.cambiarRolMecanico(id, nuevoRol);
    await cargarMecanicos();
  }, [cargarMecanicos]);

  return {
    mecanicos,
    cargando,
    error,
    cargarMecanicos,
    registrarMecanico,
    toggleActivar,
    toggleBloquear,
    eliminarMecanico,
    cambiarRol,
  };
}
