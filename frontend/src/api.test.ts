import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeClassId, api } from './api.ts';

test('normalizeClassId: handles numeric IDs', () => {
  assert.strictEqual(normalizeClassId(1), 1);
  assert.strictEqual(normalizeClassId(42), 42);
  assert.strictEqual(normalizeClassId(100.0), 100);
});

test('normalizeClassId: handles valid numeric strings', () => {
  assert.strictEqual(normalizeClassId('1'), 1);
  assert.strictEqual(normalizeClassId(' 42 '), 42);
  assert.strictEqual(normalizeClassId('100'), 100);
});

test('normalizeClassId: handles structured class objects', () => {
  assert.strictEqual(normalizeClassId({ id: 1, name: 'B.E. CSE - Data Structures' }), 1);
  assert.strictEqual(normalizeClassId({ class_id: 2, subject: 'Algorithms' }), 2);
  assert.strictEqual(normalizeClassId({ classId: 3, student_count: 80 }), 3);
  assert.strictEqual(normalizeClassId({ id: '4', name: 'Web Dev' }), 4);
  assert.strictEqual(normalizeClassId({ class_id: '5' }), 5);
});

test('normalizeClassId: rejects invalid numbers and strings', () => {
  assert.throws(() => normalizeClassId(0), /Invalid numeric class ID/);
  assert.throws(() => normalizeClassId(-5), /Invalid numeric class ID/);
  assert.throws(() => normalizeClassId(NaN), /Invalid numeric class ID/);
  assert.throws(() => normalizeClassId(''), /Invalid string class ID/);
  assert.throws(() => normalizeClassId('abc'), /Invalid string class ID/);
  assert.throws(() => normalizeClassId('12a'), /Invalid string class ID/);
});

test('normalizeClassId: rejects null, undefined, and empty objects', () => {
  assert.throws(() => normalizeClassId(null), /Invalid class identifier provided/);
  assert.throws(() => normalizeClassId(undefined), /Invalid class identifier provided/);
  assert.throws(() => normalizeClassId({}), /Class object does not contain a valid ID property/);
  assert.throws(() => normalizeClassId({ name: 'No ID Class' }), /Class object does not contain a valid ID property/);
});

test('normalizeClassId: rejects DOM and React SyntheticBaseEvents', () => {
  assert.throws(
    () => normalizeClassId({ nativeEvent: {}, target: {} }),
    /Received DOM\/React Event object instead of class ID/
  );
  assert.throws(
    () => normalizeClassId({ preventDefault: () => {} }),
    /Received DOM\/React Event object instead of class ID/
  );
});

test('Class API methods: correctly normalize class objects and numeric IDs into valid endpoints', async () => {
  // Mock global fetch to inspect URLs requested by API methods
  const requestedUrls: string[] = [];
  const originalFetch = globalThis.fetch;

  globalThis.fetch = (async (input: RequestInfo | URL) => {
    const urlStr = typeof input === 'string' ? input : input.toString();
    requestedUrls.push(urlStr);
    return {
      ok: true,
      status: 200,
      json: async () => ({ status: 'mock_ok', class_id: 1 })
    } as Response;
  }) as typeof fetch;

  try {
    // 1. Numeric ID
    await api.getClassAnalytics(1);
    await api.getStudentsNeedingAttention(1);
    await api.getClassStudents(1);

    // 2. Structured class object with { id }
    await api.getClassAnalytics({ id: 2, name: 'Algorithms' });
    await api.getStudentsNeedingAttention({ id: 2 });
    await api.getClassStudents({ id: 2 });

    // 3. Structured class object with { class_id }
    await api.getClassAnalytics({ class_id: 3 });
    await api.getStudentsNeedingAttention({ class_id: 3 });
    await api.getClassStudents({ class_id: 3 });

    // 4. Structured class object with { classId }
    await api.getClassAnalytics({ classId: 4 });
    await api.getStudentsNeedingAttention({ classId: 4 });
    await api.getClassStudents({ classId: 4 });

    // Verify all requested URLs
    assert.strictEqual(requestedUrls.length, 12);
    for (const url of requestedUrls) {
      assert.strictEqual(url.includes('[object Object]'), false, `URL must not contain [object Object]: ${url}`);
      assert.strictEqual(url.includes('[object%20Object]'), false, `URL must not contain [object%20Object]: ${url}`);
    }

    assert.ok(requestedUrls.includes('http://127.0.0.1:8000/api/classes/1/analytics'));
    assert.ok(requestedUrls.includes('http://127.0.0.1:8000/api/classes/1/students-needing-attention'));
    assert.ok(requestedUrls.includes('http://127.0.0.1:8000/api/classes/1/students'));

    assert.ok(requestedUrls.includes('http://127.0.0.1:8000/api/classes/2/analytics'));
    assert.ok(requestedUrls.includes('http://127.0.0.1:8000/api/classes/3/students-needing-attention'));
    assert.ok(requestedUrls.includes('http://127.0.0.1:8000/api/classes/4/students'));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('Class API methods: reject event objects and prevent [object Object] requests', async () => {
  const fakeEvent = { nativeEvent: {}, target: { value: 'click' }, preventDefault: () => {} };

  await assert.rejects(
    async () => {
      await api.getClassAnalytics(fakeEvent as any);
    },
    /Received DOM\/React Event object instead of class ID/
  );

  await assert.rejects(
    async () => {
      await api.getStudentsNeedingAttention(fakeEvent as any);
    },
    /Received DOM\/React Event object instead of class ID/
  );

  await assert.rejects(
    async () => {
      await api.getClassStudents(fakeEvent as any);
    },
    /Received DOM\/React Event object instead of class ID/
  );
});
