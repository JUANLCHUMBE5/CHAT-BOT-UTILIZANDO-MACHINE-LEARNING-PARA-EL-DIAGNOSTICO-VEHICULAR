/** Convierte errores desconocidos en mensajes seguros para la interfaz. */
export function getErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback;
}
