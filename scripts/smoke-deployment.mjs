import assert from 'node:assert/strict';
import { validateGuidance, QuestionEvents } from '../app/static/contracts.mjs';
import { readSSE } from '../app/static/sse.mjs';

const origin = process.argv[2];
if (!origin || !/^https?:\/\//.test(origin)) throw new Error('Usage: node scripts/smoke-deployment.mjs https://APP.azurecontainerapps.io [--ai]');
for (const path of ['/', '/demo', '/static/styles.css', '/static/app.js', '/static/contracts.mjs', '/static/sse.mjs', '/healthz']) {
  const response = await fetch(new URL(path, origin), { signal: AbortSignal.timeout(15000) });
  assert.equal(response.status, 200, path);
  await response.arrayBuffer();
  console.log(`PASS ${path}`);
}
const guidanceResponse = await fetch(new URL('/api/guidance', origin), { signal: AbortSignal.timeout(15000) });
assert.equal(guidanceResponse.status, 200);
const guidance = validateGuidance(await guidanceResponse.json());
assert.ok(guidance.cards.length);
console.log(`PASS guidance: ${guidance.cards.length} cards, ${guidance.dataKind}`);
if (process.argv.includes('--ai')) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 55000);
  try {
    const response = await fetch(new URL('/api/questions', origin), {
      method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
      body: JSON.stringify({ scenarioId: guidance.scenarioId, cardId: guidance.cards[0].id, question: '이 점검 예시의 이유와 적용 범위를 설명해 주세요.' }),
      signal: controller.signal,
    });
    assert.equal(response.status, 200);
    const stages = [];
    const events = new QuestionEvents(stage => stages.push(stage));
    await readSSE(response, event => events.accept(event), controller.signal);
    const result = events.finish();
    assert.equal(result.answer.kind, 'grounded');
    assert.ok(stages.includes('tool_running'), 'Actual tool progress must be observed');
    console.log(`PASS AI: ${result.answer.kind}, ${result.answer.evidenceIds.length} evidence IDs; ${result.dataKind}`);
  } finally { clearTimeout(timer); }
}
