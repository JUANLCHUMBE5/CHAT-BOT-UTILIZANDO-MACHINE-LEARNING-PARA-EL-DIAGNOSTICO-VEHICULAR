interface Env {
  BACKEND_ORIGIN: string;
}

interface PagesContext {
  request: Request;
  env: Env;
  params: { path?: string | string[] };
}

const HOP_BY_HOP_HEADERS = [
  'connection',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailer',
  'transfer-encoding',
  'upgrade',
];

function normalizarOrigen(valor: string): URL {
  const origen = new URL(valor);
  if (origen.protocol !== 'https:') {
    throw new Error('BACKEND_ORIGIN debe usar HTTPS.');
  }
  return origen;
}

export const onRequest = async (context: PagesContext): Promise<Response> => {
  let origen: URL;
  try {
    origen = normalizarOrigen(context.env.BACKEND_ORIGIN);
  } catch {
    return new Response('Proxy de API no configurado.', { status: 503 });
  }

  const partes = Array.isArray(context.params.path)
    ? context.params.path
    : context.params.path
      ? [context.params.path]
      : [];
  const destino = new URL(`/api/v1/${partes.join('/')}`, origen);
  destino.search = new URL(context.request.url).search;

  const headers = new Headers(context.request.headers);
  for (const header of HOP_BY_HOP_HEADERS) headers.delete(header);
  headers.delete('host');
  headers.set('ngrok-skip-browser-warning', 'true');

  const respuesta = await fetch(destino, {
    method: context.request.method,
    headers,
    body: ['GET', 'HEAD'].includes(context.request.method) ? undefined : context.request.body,
    redirect: 'manual',
  });

  const respuestaHeaders = new Headers(respuesta.headers);
  for (const header of HOP_BY_HOP_HEADERS) respuestaHeaders.delete(header);
  respuestaHeaders.set('Cache-Control', 'no-store');

  return new Response(respuesta.body, {
    status: respuesta.status,
    statusText: respuesta.statusText,
    headers: respuestaHeaders,
  });
};
