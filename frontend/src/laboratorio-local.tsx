import { StrictMode, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { LoginView } from './features/auth';
import { LaboratorioView } from './features/laboratorio';
import './index.css';

function LaboratorioLocal() {
  const [authorized, setAuthorized] = useState(false);
  if (!['localhost', '127.0.0.1', '[::1]'].includes(window.location.hostname)) {
    return <p>Laboratorio disponible exclusivamente en localhost.</p>;
  }
  return <main>
    <h1>CarBot — laboratorio LOCAL de tesis</h1>
    <p>Datos sintéticos de desarrollo. No constituye muestra oficial ni validación clínica.</p>
    {authorized ? <LaboratorioView /> : <LoginView onLoginSuccess={(user) => {
      setAuthorized(['administrador', 'admin'].includes(user.rol));
    }} />}
  </main>;
}

createRoot(document.getElementById('root')!).render(<StrictMode><LaboratorioLocal /></StrictMode>);
