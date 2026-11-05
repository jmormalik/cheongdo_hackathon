import test from 'node:test';
import assert from 'node:assert/strict';
import { SSEParser, readSSE } from '../../app/static/sse.mjs';
import { QuestionEvents, validateGuidance, validateResult, safeURL } from '../../app/static/contracts.mjs';
import { fixture } from './mock-server.mjs';

const result = { requestId: 'r1', seq: 2, answer: { kind: 'grounded', text: '설명', evidenceIds: ['example-note'] }, sources: fixture.sources, dataKind: 'fixture' };
const accept = (events, event, data) => events.accept({ event, data: JSON.stringify(data) });

test('SSE: arbitrary chunk boundaries, split CRLF, BOM, comments, multiline data', () => {
  const text = '\uFEFF: heartbeat\r\nevent: status\r\ndata: {"a":\r\ndata: "한글"}\r\n\r\nevent: complete\ndata: {}\n\n';
  for (let split = 0; split <= text.length; split++) {
    const events = [];
    const parser = new SSEParser(event => events.push(event));
    parser.feed(text.slice(0, split)); parser.feed(text.slice(split)); parser.finish();
    assert.deepEqual(events, [{ event: 'status', data: '{"a":\n"한글"}' }, { event: 'complete', data: '{}' }]);
  }
});
test('SSE: streaming UTF-8 decoder preserves Korean across every byte', async () => {
  const data = new TextEncoder().encode('event: result\ndata: 한글 감\n\n');
  const events = [];
  const stream = new ReadableStream({ start(controller) { for (const byte of data) controller.enqueue(Uint8Array.of(byte)); controller.close(); } });
  await readSSE(new Response(stream, { headers: { 'Content-Type': 'text/event-stream' } }), event => events.push(event));
  assert.equal(events[0].data, '한글 감');
});
test('SSE: incomplete frame never dispatched, oversized frame rejected', () => {
  const parser = new SSEParser(() => assert.fail('partial event dispatched'));
  parser.feed('event: result\ndata: {}'); parser.finish();
  assert.throws(() => parser.feed('a'.repeat(262145)), /stream_invalid/);
});
test('SSE: abort cancels a waiting reader', async () => {
  let cancelled = false;
  const stream = new ReadableStream({ cancel() { cancelled = true; } });
  const controller = new AbortController();
  const promise = readSSE(new Response(stream, { headers: { 'Content-Type': 'text/event-stream' } }), () => {}, controller.signal);
  controller.abort();
  await assert.rejects(promise, /aborted/);
  assert.equal(cancelled, true);
});
test('protocol: result requires successful complete; disconnection fails', () => {
  const events = new QuestionEvents(() => {});
  accept(events, 'result', result);
  assert.throws(() => events.finish(), /disconnected/);
  accept(events, 'complete', { requestId: 'r1', seq: 3, outcome: 'success' });
  assert.equal(events.finish(), events.result);
});
test('protocol: rejects sequence regression, changed request, malformed JSON, and premature success', () => {
  for (const bad of [{ requestId: 'r1', seq: 2 }, { requestId: 'different', seq: 3 }]) {
    const events = new QuestionEvents(() => {});
    accept(events, 'status', { requestId: 'r1', seq: 2 });
    assert.throws(() => accept(events, 'status', bad), /stream_invalid/);
  }
  assert.throws(() => new QuestionEvents(() => {}).accept({ event: 'result', data: '{' }), /stream_invalid/);
  assert.throws(() => accept(new QuestionEvents(() => {}), 'complete', { requestId: 'r1', seq: 1, outcome: 'success' }), /stream_invalid/);
});
test('protocol: error discards result and preserves retry policy', () => {
  const events = new QuestionEvents(() => {});
  accept(events, 'result', result);
  accept(events, 'error', { requestId: 'r1', seq: 3, code: 'answer_validation_failed', retryable: false });
  accept(events, 'complete', { requestId: 'r1', seq: 4, outcome: 'error' });
  assert.equal(events.result, null);
  assert.throws(() => events.finish(), error => error.message === 'answer_validation_failed' && error.retryable === false);
});
test('data: unknown evidence, missing dates, over three cards and unsafe source links rejected', () => {
  assert.equal(validateGuidance(fixture), fixture);
  const bad = structuredClone(fixture); bad.cards[0].evidenceIds = ['invented'];
  assert.throws(() => validateGuidance(bad), /data_invalid/);
  assert.throws(() => validateGuidance({ ...fixture, cards: [...fixture.cards, fixture.cards[0]] }), /data_invalid/);
  assert.throws(() => validateResult({ ...result, answer: { ...result.answer, evidenceIds: ['invented'] } }), /data_invalid/);
  assert.throws(() => validateGuidance({ ...fixture, dataKind: 'reviewed_static' }), /data_invalid/);
  assert.equal(safeURL('javascript:alert(1)'), null);
  assert.equal(safeURL('https://user:password@example.com'), null);
  assert.equal(safeURL('https://example.com/'), 'https://example.com/');
  const reviewed = { ...fixture, dataKind: 'reviewed_static', reviewedAt: '2026-11-05', sources: [{ ...fixture.sources[0], url: 'https://example.com/' }] };
  assert.equal(validateGuidance(reviewed).sources[0].publishedAt, null);
});
