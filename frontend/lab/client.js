export function payload(scenario, message) {
  if (!['yaris', 'sentra'].includes(scenario)) throw new Error('Escenario inválido');
  const text = String(message).trim();
  if (!text || text.length > 4000) throw new Error('Mensaje entre 1 y 4000 caracteres');
  return {scenario, message: text};
}
export function summarize(result) {
  return JSON.stringify(result, null, 2);
}
if (typeof document !== 'undefined') {
  const output = document.querySelector('#results');
  const status = document.querySelector('#status');
  const buttons = [...document.querySelectorAll('button')];
  async function request(path, body, method = 'POST') {
    buttons.forEach(b => {b.disabled = true;});
    status.textContent = 'Procesando en API y worker aislados…';
    try {
      const response = await fetch(path, {method, headers: {'Content-Type': 'application/json'}, ...(method === 'GET' ? {} : {body: JSON.stringify(body)})});
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
      output.textContent = summarize(data);
      status.textContent = 'Resultado real del stack de pruebas; datos sintéticos.';
    } catch (error) { status.textContent = String(error); }
    finally { buttons.forEach(b => {b.disabled = false;}); }
  }
  document.querySelector('#send').onclick = () => {
    try { request('/lab/turn', payload(document.querySelector('#scenario').value, document.querySelector('#message').value)); }
    catch (error) { status.textContent = String(error); }
  };
  document.querySelector('#report').onclick = () => request('/lab/results', undefined, 'GET');
  document.querySelector('#run').onclick = () => request('/lab/run', {});
}

