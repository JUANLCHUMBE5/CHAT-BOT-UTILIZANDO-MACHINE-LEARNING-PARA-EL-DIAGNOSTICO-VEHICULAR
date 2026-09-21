import assert from 'assert';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const currentDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(currentDir, '..', '..');
const api = fs.readFileSync(path.join(root, 'src', 'services', 'api.ts'), 'utf8');
const app = fs.readFileSync(path.join(root, 'src', 'App.tsx'), 'utf8');
const login = fs.readFileSync(path.join(root, 'src', 'components', 'views', 'LoginView.tsx'), 'utf8');

assert(api.includes("credentials: 'include'"), 'Las cookies HttpOnly deben enviarse en autenticación.');
assert(api.includes('accessTokenInMemory'), 'El access token debe mantenerse en memoria.');
assert(!login.includes('token: tokenRes.access_token'), 'LoginView no debe persistir el access token.');
assert(!login.includes('refreshToken: tokenRes.refresh_token'), 'LoginView no debe persistir el refresh token.');
assert(!api.includes('session.token = tokens.access_token'), 'La renovación no debe persistir el access token.');
assert(!app.includes('token: usuarioSesion.token'), 'App no debe guardar el access token en localStorage.');

console.log('✔ Secure HttpOnly session contract verified');
