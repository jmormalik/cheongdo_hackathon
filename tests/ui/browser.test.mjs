// Uses Chrome's DevTools protocol directly; no npm dependencies or browser install.
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtemp, rm, access, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { mockServer } from './mock-server.mjs';

const chrome = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
let hasChrome = true;
try { await access(chrome); } catch { hasChrome = false; }

test('browser: mobile UI, keyboard, API payload, errors, cancellation, retry and safe rendering', { skip: !hasChrome, timeout: 60000 }, async t => {
  const server = mockServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const profile = await mkdtemp(join(tmpdir(), 'cheongdo-ui-'));
  const proc = spawn(chrome, ['--headless=new', '--no-first-run', '--no-default-browser-check', '--remote-debugging-port=0', '--remote-debugging-address=127.0.0.1', `--user-data-dir=${profile}`, 'about:blank'], { stdio: ['ignore', 'ignore', 'pipe'] });
  let socket;
  t.after(async () => {
    socket?.close();
    const exited = new Promise(resolve => proc.once('exit', resolve));
    proc.kill();
    await Promise.race([exited, delay(3000)]);
    server.closeAllConnections();
    await new Promise(resolve => server.close(resolve));
    await rm(profile, { recursive: true, force: true, maxRetries: 3, retryDelay: 100 });
  });
  const debug = await new Promise((resolve, reject) => {
    let stderr = '';
    const timer = setTimeout(() => reject(new Error('Chrome startup timeout')), 12000);
    proc.stderr.on('data', chunk => {
      stderr += chunk;
      const match = /DevTools listening on (ws:\/\/[^\s]+)/.exec(stderr);
      if (match) { clearTimeout(timer); resolve(match[1]); }
    });
    proc.once('error', reject);
  });
  const debugOrigin = debug.replace(/^ws:/, 'http:').split('/devtools/')[0];
  const targets = await (await fetch(`${debugOrigin}/json/list`)).json();
  socket = new WebSocket(targets.find(target => target.type === 'page').webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
  const pending = new Map();
  let id = 0;
  socket.onmessage = ({ data }) => {
    const message = JSON.parse(data);
    if (message.id && pending.has(message.id)) {
      const { resolve, reject } = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) reject(new Error(JSON.stringify(message.error))); else resolve(message.result);
    }
  };
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    pending.set(++id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
  const evaluate = async expression => {
    const value = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (value.exceptionDetails) throw new Error(JSON.stringify(value.exceptionDetails));
    return value.result.value;
  };
  const wait = async expression => {
    for (let i = 0; i < 150; i++) { if (await evaluate(expression)) return; await delay(30); }
    throw new Error(`UI condition timeout: ${expression}; ${await evaluate(`JSON.stringify({focus:document.activeElement?.id,status:document.getElementById('guidance-status')?.textContent,answer:document.getElementById('answer-status')?.textContent,url:location.href})`)}`);
  };
  const navigate = async (mode = '') => {
    await send('Page.navigate', { url: `${origin}/demo${mode ? '?case=' + mode : ''}` });
    await wait(`document.readyState === 'complete' && document.querySelectorAll('.suggestion').length === 3`);
  };
  const load = async () => {
    await evaluate(`document.getElementById('load-guidance').click()`);
    await wait(`document.querySelectorAll('.card').length === 3`);
  };
  const ask = async question => {
    await evaluate(`document.getElementById('question').value = ${JSON.stringify(question)}; document.getElementById('question-form').requestSubmit()`);
  };
  const finish = async () => wait(`document.getElementById('question-form').getAttribute('aria-busy') === 'false'`);
  const overflow = async () => assert.equal(await evaluate(`document.documentElement.scrollWidth > innerWidth`), false);

  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await navigate();
  await overflow();
  assert.equal(await evaluate(`document.getElementById('questions').hidden`), true);
  // Tab and Enter activate the actual focused button.
  await evaluate(`document.getElementById('load-guidance').focus()`);
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', text: '\r', windowsVirtualKeyCode: 13 });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
  await wait(`document.querySelectorAll('.card').length === 3`);
  assert.equal(await evaluate(`document.getElementById('fixture-banner').compareDocumentPosition(document.getElementById('cards')) & Node.DOCUMENT_POSITION_FOLLOWING`), 4);
  assert.equal(await evaluate(`document.getElementById('fixture-banner').hidden`), false);
  await evaluate(`document.querySelector('.source-details summary').click(); document.querySelector('.card-question').click()`);
  assert.equal(await evaluate(`document.activeElement.id`), 'question');
  assert.match(await evaluate(`document.getElementById('card-context-label').textContent`), /수확 후 기록/);
  await evaluate(`window.questionRequests = 0; window.originalFetch = window.fetch; window.fetch = (...args) => { if(args[0] === '/api/questions') window.questionRequests++; return window.originalFetch(...args); }`);
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 });
  assert.equal(await evaluate(`document.activeElement.id`), 'submit-question');
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', text: '\r', windowsVirtualKeyCode: 13 });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
  await wait(`document.getElementById('cancel-question').hidden === false`);
  assert.equal(await evaluate(`document.getElementById('submit-question').disabled`), true);
  await evaluate(`document.getElementById('question-form').requestSubmit()`);
  assert.equal(await evaluate(`window.questionRequests`), 1);
  assert.equal(await evaluate(`document.getElementById('answer').hidden`), true);
  await finish();
  assert.match(await evaluate(`document.getElementById('answer-text').textContent`), /example-record/);
  assert.equal(await evaluate(`document.getElementById('answer-fixture').hidden`), false);
  await overflow();
  if (process.env.UI_SCREENSHOT_PATH) {
    const shot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
    await writeFile(process.env.UI_SCREENSHOT_PATH, Buffer.from(shot.data, 'base64'));
  }

  for (const [mode, message] of [['error', 'AI 설명을 가져오지'], ['timeout', '응답 시간이 초과'], ['validation-error', '근거를 확인할 수 없어'], ['disconnect', '연결이 끊겼'], ['busy', '요청이 많습니다']]) {
    await navigate(mode); await load(); await ask('왜 필요한가요?'); await finish();
    assert.match(await evaluate(`document.getElementById('answer-status').textContent`), new RegExp(message));
    assert.equal(await evaluate(`document.getElementById('answer').hidden`), true);
    assert.equal(await evaluate(`document.querySelectorAll('.card').length`), 3);
    assert.equal(await evaluate(`document.getElementById('retry-question').hidden`), false);
  }
  // Manual retry succeeds after recovery; no automatic replay.
  await evaluate(`history.replaceState({}, '', '/demo'); document.getElementById('retry-question').click()`);
  await finish();
  assert.equal(await evaluate(`document.getElementById('answer').hidden`), false);

  await navigate('slow'); await load(); await ask('취소할 질문');
  await wait(`document.getElementById('answer-status').textContent.includes('조회하고')`);
  await evaluate(`document.getElementById('cancel-question').click()`); await finish();
  assert.match(await evaluate(`document.getElementById('answer-status').textContent`), /취소했습니다/);
  assert.equal(await evaluate(`document.getElementById('question').value`), '취소할 질문');
  assert.equal(await evaluate(`document.querySelectorAll('.card').length`), 3);

  await navigate('empty'); await evaluate(`document.getElementById('load-guidance').click()`);
  await wait(`document.getElementById('guidance-status').textContent.includes('자료가 없습니다')`);
  assert.equal(await evaluate(`document.getElementById('questions').hidden`), true);
  await navigate('guidance-error'); await evaluate(`document.getElementById('load-guidance').click()`);
  await wait(`document.getElementById('guidance-status').classList.contains('error')`);
  assert.equal(await evaluate(`document.getElementById('questions').hidden`), true);

  await navigate('reviewed'); await load();
  await evaluate(`document.querySelector('.source-details summary').click()`);
  assert.match(await evaluate(`document.querySelector('.source-details').textContent`), /발행일 미상/);
  assert.match(await evaluate(`document.querySelector('.source-details').textContent`), /자료 검토일: 2026-11-05/);
  assert.equal(await evaluate(`document.getElementById('fixture-banner').hidden`), true);
  await overflow();

  await navigate('out-of-scope'); await load(); await ask('범위 밖 질문'); await finish();
  assert.match(await evaluate(`document.getElementById('answer-kind').textContent`), /지원 범위 안내/);

  await navigate(); await load();
  // Untrusted model HTML must remain plain text.
  await evaluate(`window.fetch = async () => new Response('event: result\\ndata: ' + JSON.stringify({requestId:'safe',seq:1,dataKind:'fixture',sources:[{id:'x',title:'예시',scope:'테스트',url:null,publishedAt:null}],answer:{kind:'grounded',text:'<img src=x onerror=alert(1)>',evidenceIds:['x']}}) + '\\n\\nevent: complete\\ndata: {"requestId":"safe","seq":2,"outcome":"success"}\\n\\n', {headers:{'Content-Type':'text/event-stream'}})`);
  await ask('안전 렌더링'); await finish();
  assert.equal(await evaluate(`document.querySelector('#answer-text img') === null`), true);
  assert.match(await evaluate(`document.getElementById('answer-text').textContent`), /<img/);
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await overflow();
});
