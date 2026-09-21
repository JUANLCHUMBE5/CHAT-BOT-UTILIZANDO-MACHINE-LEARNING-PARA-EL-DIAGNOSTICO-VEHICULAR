/** Convierte errores desconocidos en mensajes seguros para la interfaz. */
export function getErrorMessage(error: unknown, fallback: string): string {
  if (!error) return fallback;
  if (typeof error === 'string') return error;
  if (error instanceof Error && error.message) return error.message;
  if (typeof error === 'object' && error !== null) {
    const obj = error as Record<string, unknown>;
    if (typeof obj.detail === 'string') return obj.detail;
    if (Array.isArray(obj.detail)) {
      return obj.detail.map((e: unknown) => (typeof e === 'object' && e !== null && 'msg' in e ? String((e as { msg: unknown }).msg) : String(e))).join(', ');
    }
    if (typeof obj.message === 'string') return obj.message;
  }
  return fallback;
}
