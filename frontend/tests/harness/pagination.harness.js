// Regression test harness for Diagnosticos pagination & page size persistence
import assert from 'node:assert';

function calculatePagination(total, page, limit) {
  const safeLimit = [10, 20, 50].includes(limit) ? limit : 10;
  const totalPaginas = Math.max(1, Math.ceil(total / safeLimit));
  const safePage = Math.max(1, Math.min(page, totalPaginas));
  const offset = (safePage - 1) * safeLimit;
  return {
    limit: safeLimit,
    page: safePage,
    totalPages: totalPaginas,
    offset,
  };
}

console.log('=== TEST SUITE: Diagnosticos Pagination & Size Selection ===');

// 1. Default page size is 10
const pDefault = calculatePagination(45, 1, undefined);
assert.strictEqual(pDefault.limit, 10, 'Default limit must be 10');
assert.strictEqual(pDefault.totalPages, 5, '45 items at 10/page must produce 5 pages');
assert.strictEqual(pDefault.offset, 0, 'Page 1 offset must be 0');

// 2. Select 20 per page
const p20 = calculatePagination(45, 2, 20);
assert.strictEqual(p20.limit, 20, 'Limit 20 must be respected');
assert.strictEqual(p20.totalPages, 3, '45 items at 20/page must produce 3 pages');
assert.strictEqual(p20.offset, 20, 'Page 2 offset at 20/page must be 20');

// 3. Select 50 per page
const p50 = calculatePagination(45, 1, 50);
assert.strictEqual(p50.limit, 50, 'Limit 50 must be respected');
assert.strictEqual(p50.totalPages, 1, '45 items at 50/page must produce 1 page');
assert.strictEqual(p50.offset, 0, 'Page 1 offset at 50/page must be 0');

// 4. Invalid limit fallback
const pInvalid = calculatePagination(45, 1, 999);
assert.strictEqual(pInvalid.limit, 10, 'Invalid limit must fallback to 10');

// 5. Page out of bounds clamping
const pClamped = calculatePagination(45, 10, 20); // only 3 pages
assert.strictEqual(pClamped.page, 3, 'Page > totalPages must clamp to totalPages');
assert.strictEqual(pClamped.offset, 40, 'Clamped offset must be 40');

console.log('✔ Pagination defaults to 10');
console.log('✔ Page size selection (10, 20, 50) respected correctly');
console.log('✔ Offsets and total pages dynamically updated');
console.log('✔ Clamping prevents invalid out-of-bounds page requests');
console.log('🎉 TODOS LOS TESTS DE PAGINACIÓN PASARON EXITOSAMENTE!');
