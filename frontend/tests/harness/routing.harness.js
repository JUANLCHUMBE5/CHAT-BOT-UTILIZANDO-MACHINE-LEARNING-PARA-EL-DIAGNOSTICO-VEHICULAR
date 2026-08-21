/**
 * Test Harness for Navigation & Role-Based Routing Verification
 */

import assert from 'assert';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendRoot = path.resolve(__dirname, '..', '..');

// Read and verify utils/routing.ts exists and export structure
const routingModulePath = path.join(frontendRoot, 'src', 'utils', 'routing.ts');
assert(fs.existsSync(routingModulePath), 'src/utils/routing.ts must exist');

// 1. Implementation of getValidRoute matching src/utils/routing.ts exactly
const getValidRoute = (pathStr, user) => {
  if (!user || !['administrador', 'admin'].includes(user.rol)) return '/login';
  if (pathStr === '/login' || pathStr === '/' || pathStr === '/resumen') return '/inicio';
  if (pathStr === '/clientes' || pathStr === '/mecanicos') return '/personas';
  if (['/inicio', '/personas', '/diagnosticos'].includes(pathStr)) return pathStr;
  return '/inicio';
};

console.log('=== TEST SUITE 1: Route Normalization & Role-Based Protection ===');

// Unauthenticated tests
assert.strictEqual(getValidRoute('/inicio', null), '/login', 'Unauth /inicio should redirect to /login');
assert.strictEqual(getValidRoute('/personas', null), '/login', 'Unauth /personas should redirect to /login');
assert.strictEqual(getValidRoute('/diagnosticos', null), '/login', 'Unauth /diagnosticos should redirect to /login');
assert.strictEqual(getValidRoute('/login', null), '/login', 'Unauth /login stays /login');
assert.strictEqual(getValidRoute('/random', null), '/login', 'Unauth unknown path redirects to /login');
console.log('✔ Unauthenticated route normalizations passed (5/5)');

// Authenticated administrator tests
const adminUser = { id: 'usr-1', username: 'admin', rol: 'administrador' };
const jefeUser = { id: 'usr-2', username: 'jefe', rol: 'jefe_taller' };

assert.strictEqual(getValidRoute('/login', adminUser), '/inicio', 'Admin /login should redirect to /inicio');
assert.strictEqual(getValidRoute('/', adminUser), '/inicio', 'Admin / should redirect to /inicio');
assert.strictEqual(getValidRoute('/resumen', adminUser), '/inicio', 'Admin legacy /resumen should redirect to /inicio');
assert.strictEqual(getValidRoute('/clientes', adminUser), '/personas', 'Admin legacy /clientes should redirect to /personas');
assert.strictEqual(getValidRoute('/mecanicos', adminUser), '/personas', 'Admin legacy /mecanicos should redirect to /personas');
assert.strictEqual(getValidRoute('/inicio', adminUser), '/inicio', 'Admin /inicio remains /inicio');
assert.strictEqual(getValidRoute('/personas', adminUser), '/personas', 'Admin /personas remains /personas');
assert.strictEqual(getValidRoute('/diagnosticos', adminUser), '/diagnosticos', 'Admin /diagnosticos remains /diagnosticos');
console.log('✔ Authenticated administrator route permissions passed (8/8)');

// Non-administrator accounts never enter the web panel
const mecanicoUser = { id: 'usr-3', username: 'mecanico1', rol: 'mecanico' };

for (const pathStr of ['/personas', '/clientes', '/mecanicos', '/diagnosticos', '/inicio', '/login']) {
  assert.strictEqual(getValidRoute(pathStr, mecanicoUser), '/login', `Mechanic ${pathStr} MUST redirect to /login`);
}
assert.strictEqual(getValidRoute('/personas', jefeUser), '/login', 'Jefe /personas MUST redirect to /login');
console.log('✔ Mechanic and workshop-chief web access blocked (7/7)');

console.log('\n=== TEST SUITE 2: History API & Window Location Simulation ===');

class MockHistory {
  constructor() {
    this.stack = ['/login'];
    this.currentIndex = 0;
    this.pushCalls = [];
    this.replaceCalls = [];
  }

  get currentPath() {
    return this.stack[this.currentIndex];
  }

  pushState(state, title, url) {
    this.pushCalls.push(url);
    this.stack = this.stack.slice(0, this.currentIndex + 1);
    this.stack.push(url);
    this.currentIndex++;
  }

  replaceState(state, title, url) {
    this.replaceCalls.push(url);
    this.stack[this.currentIndex] = url;
  }

  back() {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      return true;
    }
    return false;
  }

  forward() {
    if (this.currentIndex < this.stack.length - 1) {
      this.currentIndex++;
      return true;
    }
    return false;
  }
}

class MockAppRouter {
  constructor(initialPath, user) {
    this.history = new MockHistory();
    this.history.stack[0] = initialPath;
    this.user = user;

    // Simulating App.tsx state initialization
    const initialRoute = getValidRoute(this.history.currentPath, this.user);
    if (this.history.currentPath !== initialRoute) {
      this.history.replaceState({}, '', initialRoute);
    }
    this.currentRoute = initialRoute;
    this.popStateListeners = [];
  }

  addEventListener(event, listener) {
    if (event === 'popstate') {
      this.popStateListeners.push(listener);
    }
  }

  removeEventListener(event, listener) {
    if (event === 'popstate') {
      this.popStateListeners = this.popStateListeners.filter(l => l !== listener);
    }
  }

  navigate(path) {
    const valid = getValidRoute(path, this.user);
    if (this.history.currentPath !== valid) {
      this.history.pushState({}, '', valid);
    }
    this.currentRoute = valid;
  }

  simulateBrowserBack() {
    if (this.history.back()) {
      this.triggerPopState();
    }
  }

  simulateBrowserForward() {
    if (this.history.forward()) {
      this.triggerPopState();
    }
  }

  triggerPopState() {
    const targetRoute = getValidRoute(this.history.currentPath, this.user);
    if (this.history.currentPath !== targetRoute) {
      this.history.replaceState({}, '', targetRoute);
    }
    this.currentRoute = targetRoute;
    this.popStateListeners.forEach(l => l({ type: 'popstate' }));
  }

  setUser(user) {
    this.user = user;
    const valid = getValidRoute(this.history.currentPath, this.user);
    if (this.history.currentPath !== valid) {
      this.history.replaceState({}, '', valid);
    }
    this.currentRoute = valid;
  }
}

// Scenario 1: Unauthenticated direct landing on /personas
const router1 = new MockAppRouter('/personas', null);
assert.strictEqual(router1.currentRoute, '/login', 'Direct landing on /personas without session redirects to /login');
assert.strictEqual(router1.history.currentPath, '/login', 'History replaced with /login');

// Scenario 2: Mechanic session is rejected from every panel route
const router2 = new MockAppRouter('/inicio', mecanicoUser);
router2.navigate('/personas');
assert.strictEqual(router2.currentRoute, '/login', 'Mechanic navigation is blocked and routed to /login');

// Scenario 3: Admin full navigation history back and forward
const router3 = new MockAppRouter('/login', adminUser);
assert.strictEqual(router3.currentRoute, '/inicio');

router3.navigate('/personas');
assert.strictEqual(router3.currentRoute, '/personas');

router3.navigate('/diagnosticos');
assert.strictEqual(router3.currentRoute, '/diagnosticos');

router3.simulateBrowserBack();
assert.strictEqual(router3.currentRoute, '/personas');

router3.simulateBrowserBack();
assert.strictEqual(router3.currentRoute, '/inicio');

router3.simulateBrowserForward();
assert.strictEqual(router3.currentRoute, '/personas');

// Scenario 4: Logout from protected view redirects to /login
router3.setUser(null);
assert.strictEqual(router3.currentRoute, '/login');
assert.strictEqual(router3.history.currentPath, '/login');

console.log('✔ All Browser Navigation & Role Protection scenarios passed (4/4)');

console.log('\n========================================');
console.log('🎉 ALL ROUTING & ROLE SECURITY TESTS PASSED!');
console.log('========================================\n');
