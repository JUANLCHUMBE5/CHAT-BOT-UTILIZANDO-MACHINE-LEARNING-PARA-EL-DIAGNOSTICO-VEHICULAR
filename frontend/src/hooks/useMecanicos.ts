import { useState, useCallback } from 'react';
import { mechanicsApi } from '../features/management/api/mechanicsApi';
import type { Mecanico, MecanicoRol } from '../types';
import { getErrorMessage } from '../utils/errors';

export function useMecanicos() {
  const [mecanicos, setMecanicos] = useState<Mecanico[]>([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cargarMecanicos = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const data = await mechanicsApi.listar();
      setMecanicos(data);
    } catch (error: unknown) {
      setError(getErrorMessage(error, 'Error al cargar los mecánicos del taller'));
    } finally {
      setCargando(false);
    }
  }, []);

  const registrarMecanico = useCallback(async (data: {
    nombres: string;
    telefono: string;
    password?: string;
    rol: MecanicoRol;
  }) => {
    await mechanicsApi.registrar({
      nombres: data.nombres,
      telefono_whatsapp: data.telefono,
      password: data.password,
      rol: data.rol,
    });
    await cargarMecanicos();
  }, [cargarMecanicos]);

  const toggleActivar = useCallback(async (id: string) => {
    await mechanicsApi.alternarActivo(id);
    await cargarMecanicos();
  }, [cargarMecanicos]);

  const toggleBloquear = useCallback(async (id: string) => {
    await mechanicsApi.alternarBloqueo(id);
    await cargarMecanicos();
  }, [cargarMecanicos]);

  const eliminarMecanico = useCallback(async (id: string) => {
    await mechanicsApi.eliminar(id);
    await cargarMecanicos();
  }, [cargarMecanicos]);

  const cambiarRol = useCallback(async (id: string, nuevoRol: MecanicoRol) => {
    await mechanicsApi.cambiarRol(id, nuevoRol);
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
