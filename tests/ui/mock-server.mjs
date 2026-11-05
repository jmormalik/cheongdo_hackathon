// Development only. Never loaded by the production UI or used as an API fallback.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { SCENARIO_ID } from '../../app/static/contracts.mjs';

export const fixture = {
  scenarioId: SCENARIO_ID, dataKind: 'fixture', reviewedAt: null,
  sources: [{ id: 'example-note', title: '수확 후 점검 화면용 예시 노트', url: null, publishedAt: null, scope: '청도 감 수확 후 점검 UI 시연에만 적용' }],
  cards: [
    { id: 'example-record', title: '수확 후 기록 살펴보기', reason: '점검 이유가 어떻게 표시되는지 확인하기 위한 예시입니다. 실제 재배 권고가 아닙니다.', caution: '실제 현장 판단에 사용하지 마세요.', evidenceIds: ['example-note'] },
    { id: 'example-observe', title: '관찰할 내용 정리하기', reason: '관찰 내용을 확인하는 카드의 사용 흐름을 시연합니다. 실제 재배 권고가 아닙니다.', caution: '현장의 점검 기준은 전문가에게 확인하세요.', evidenceIds: ['example-note'] },
    { id: 'example-consult', title: '상담할 질문 적어두기', reason: '자료의 적용 범위와 질문 맥락을 확인하는 예시입니다. 실제 재배 권고가 아닙니다.', caution: '이 예시는 농장별 처방을 제공하지 않습니다.', evidenceIds: ['example-note'] },
  ],
};

export function mockServer() {
  return createServer(async (req, res) => {
    const url = new URL(req.url, 'http://localhost');
    const mode = new URL(req.headers.referer || 'http://localhost').searchParams.get('case');
    if (url.pathname === '/api/guidance') {
      res.setHeader('Content-Type', 'application/json');
      if (mode === 'guidance-error') { res.writeHead(503).end('{}'); return; }
      const data = structuredClone(fixture);
      if (mode === 'empty') data.cards = [];
      if (mode === 'reviewed') {
        data.dataKind = 'reviewed_static'; data.reviewedAt = '2026-11-05';
        data.sources[0].url = 'https://example.com/ui-test-source';
      }
      res.end(JSON.stringify(data)); return;
    }
    if (url.pathname === '/api/questions' && req.method === 'POST') {
      let body = '';
      for await (const chunk of req) body += chunk;
      let request;
      try { request = JSON.parse(body); } catch { res.writeHead(400).end('{}'); return; }
      if (request.scenarioId !== SCENARIO_ID || !request.question?.trim() || request.question.length > 500) { res.writeHead(422).end('{}'); return; }
      if (mode === 'busy') { res.writeHead(429, { 'Content-Type': 'application/json' }).end('{"message":"busy"}'); return; }
      res.writeHead(200, { 'Content-Type': 'text/event-stream; charset=utf-8', 'Cache-Control': 'no-store' });
      const requestId = 'mock-request';
      let seq = 0;
      const frame = (event, data) => `event: ${event}\r\ndata: ${JSON.stringify({ requestId, seq: ++seq, ...data })}\r\n\r\n`;
      const chunks = [frame('status', { stage: 'tool_running' })];
      if (mode === 'slow') {
        res.write(chunks[0]);
        const timer = setTimeout(() => res.end(), 60000);
        res.on('close', () => clearTimeout(timer));
        return;
      }
      chunks.push(frame('status', { stage: 'tool_done' }));
      if (mode === 'error' || mode === 'validation-error' || mode === 'timeout') {
        chunks.push(frame('error', { code: mode === 'validation-error' ? 'answer_validation_failed' : mode === 'timeout' ? 'timeout' : 'model_error', message: '개발용 실패', retryable: true }), frame('complete', { outcome: 'error' }));
      } else {
        const outside = mode === 'out-of-scope';
        chunks.push(frame('result', { answer: { kind: outside ? 'out_of_scope' : 'grounded', text: outside ? '청도 감 수확 후 점검 자료의 범위 안에서 질문해 주세요.' : `개발용 mock 설명입니다. 실제 AI 호출이 아닙니다.\n${request.cardId ? '선택 카드: ' + request.cardId : '전체 시나리오 질문'}\n이 예시는 실제 재배 권고가 아닙니다.`, evidenceIds: outside ? [] : ['example-note'] }, sources: fixture.sources, dataKind: 'fixture' }));
        if (mode !== 'disconnect') chunks.push(frame('complete', { outcome: 'success' }));
      }
      // Split inside UTF-8 characters and SSE delimiters on purpose.
      const bytes = Buffer.from(chunks.join(''));
      let offset = 0;
      const timer = setInterval(() => {
        if (offset >= bytes.length) { clearInterval(timer); res.end(); return; }
        const width = [1, 7, 31, 3, 97][offset % 5];
        res.write(bytes.subarray(offset, offset + width)); offset += width;
      }, 2);
      res.on('close', () => clearInterval(timer));
      return;
    }
    const names = { '/': 'index.html', '/demo': 'index.html', '/static/index.html': 'index.html', '/static/styles.css': 'styles.css', '/static/app.js': 'app.js', '/static/sse.mjs': 'sse.mjs', '/static/contracts.mjs': 'contracts.mjs' };
    const name = names[url.pathname];
    if (!name) { res.writeHead(404).end('Not found'); return; }
    try {
      const content = await readFile(new URL(`../../app/static/${name}`, import.meta.url));
      res.setHeader('Content-Type', name.endsWith('.html') ? 'text/html; charset=utf-8' : name.endsWith('.css') ? 'text/css' : 'text/javascript');
      res.end(content);
    } catch { res.writeHead(500).end('Static file unavailable'); }
  });
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const server = mockServer();
  server.listen(Number(process.env.UI_PORT || 4173), '127.0.0.1', () => {
    console.log(`UI mock only: http://127.0.0.1:${server.address().port}/demo`);
  });
}
