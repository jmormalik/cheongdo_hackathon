import { readSSE } from './sse.mjs';
import { SCENARIO_ID, safeURL, validateGuidance, QuestionEvents } from './contracts.mjs';

const $ = id => document.getElementById(id);
const state = { guidance: null, cardId: null, active: null, lastRequest: null };
const suggestions = ['왜 이 점검이 필요한가요?', '점검할 때 무엇을 주의해야 하나요?', '이 자료는 어디까지 적용할 수 있나요?'];
const stages = { accepted: '질문을 접수했습니다.', queued: '질문 처리를 기다리고 있습니다.', tool_running: '점검 자료를 조회하고 있습니다.', tool_done: '점검 자료 조회를 마쳤습니다.', generating: '자료를 바탕으로 설명을 준비하고 있습니다.', validating: '답변의 근거를 확인하고 있습니다.' };
const errors = { timeout: '응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.', answer_validation_failed: '답변의 근거를 확인할 수 없어 설명을 표시하지 않았습니다.', disconnected: '답변 완료 전에 연결이 끊겼습니다. 다시 시도해 주세요.', stream_invalid: '응답 형식을 확인할 수 없습니다. 다시 시도해 주세요.', data_invalid: '자료와 근거의 형식을 확인할 수 없습니다.', capacity_exceeded: '현재 질문 요청이 많습니다. 잠시 후 다시 시도해 주세요.', invalid_request: '질문 또는 선택한 카드가 유효하지 않습니다. 입력을 확인해 주세요.', configuration_error: 'AI 연결을 준비 중입니다. 점검 카드는 계속 확인할 수 있습니다.', model_error: 'AI 설명을 가져오지 못했습니다. 점검 카드는 계속 확인할 수 있습니다.', network_error: '서버에 연결하지 못했습니다. 연결 상태를 확인한 뒤 다시 시도해 주세요.' };

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function notice(id, text, error = false) {
  const node = $(id);
  node.textContent = text;
  node.hidden = !text;
  node.classList.toggle('error', error);
}
function currentWeek() {
  const today = new Date(new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date()) + 'T00:00:00Z');
  const day = today.getUTCDay() || 7;
  today.setUTCDate(today.getUTCDate() - day + 1);
  const start = today.toISOString().slice(0, 10);
  today.setUTCDate(today.getUTCDate() + 6);
  return `${start} ~ ${today.toISOString().slice(0, 10)} · 한국 시간 기준`;
}
function sourcesDetails(sources, dataKind, reviewedAt) {
  const details = el('details', 'source-details');
  details.append(el('summary', '', `근거 상세 보기 (${sources.length})`));
  for (const source of sources) {
    const entry = el('div', 'source');
    entry.append(el('p', 'source-title', source.title));
    entry.append(el('p', '', `적용 범위: ${source.scope}`));
    if (dataKind === 'fixture') {
      entry.append(el('p', '', `데모 예시 ID: ${source.id} · 실제 원문 없음`));
    } else {
      entry.append(el('p', '', source.publishedAt ? `발행일: ${source.publishedAt}` : '발행일 미상'));
      entry.append(el('p', '', `자료 검토일: ${source.reviewedAt || reviewedAt || '제공되지 않음'}`));
      if (source.usageTerms) entry.append(el('p', '', `이용 조건: ${source.usageTerms}`));
      const href = safeURL(source.url);
      if (href) {
        const link = el('a', '', '원문 확인 ↗');
        link.href = href;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.setAttribute('aria-label', `${source.title} 원문 확인 (새 탭)`);
        entry.append(link);
      }
    }
    details.append(entry);
  }
  return details;
}
function setContext(cardId) {
  state.cardId = cardId;
  $('card-context').hidden = !cardId;
  $('card-context-label').textContent = cardId ? `선택한 점검: ${state.guidance.cards.find(card => card.id === cardId).title}` : '';
}
function prepareQuestion(question, cardId = state.cardId) {
  if (state.active) return;
  setContext(cardId);
  $('question').value = question;
  $('question').setCustomValidity('');
  $('retry-question').hidden = true;
  updateCount();
  $('question').focus();
}
function renderGuidance(data) {
  $('fixture-banner').hidden = data.dataKind !== 'fixture';
  $('data-meta').hidden = false;
  $('data-meta').textContent = data.dataKind === 'fixture' ? '예시 자료로 화면의 사용 흐름을 확인할 수 있습니다.' : `원문 검토 정적 자료 · 자료 검토일 ${data.reviewedAt} · 이번 주에 발행된 자료라는 뜻은 아닙니다.`;
  $('week-range').textContent = currentWeek();
  $('cards').replaceChildren();
  data.cards.forEach((card, index) => {
    const article = el('article', 'card');
    article.append(el('span', 'card-number', `CHECK ${String(index + 1).padStart(2, '0')}`), el('h3', '', card.title), el('p', '', card.reason));
    if (card.caution) article.append(el('p', 'caution', `주의할 점 · ${card.caution}`));
    article.append(sourcesDetails(data.sources.filter(source => card.evidenceIds.includes(source.id)), data.dataKind, data.reviewedAt));
    const button = el('button', 'button secondary card-question', '이 점검의 이유 질문하기 ↗');
    button.type = 'button';
    button.addEventListener('click', () => prepareQuestion('왜 이 점검이 필요한가요?', card.id));
    article.append(button);
    $('cards').append(article);
  });
  $('questions').hidden = !data.cards.length;
  notice('guidance-status', data.cards.length ? '' : '현재 제공할 점검 자료가 없습니다. 자료가 준비된 뒤 다시 확인해 주세요.');
  $('load-guidance').textContent = data.cards.length ? '점검 목록 다시 보기 ↗' : '점검 목록 다시 불러오기 ↗';
}
async function loadGuidance() {
  if ($('load-guidance').disabled || state.active) return;
  if (state.guidance?.cards.length) {
    $('checklist-title').focus();
    return;
  }
  $('load-guidance').disabled = true;
  $('checklist').hidden = false;
  $('checklist').setAttribute('aria-busy', 'true');
  notice('guidance-status', '점검 자료를 불러오고 있습니다.');
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch('/api/guidance', { signal: controller.signal, headers: { Accept: 'application/json' }, cache: 'no-store' });
    if (!response.ok) throw new Error('network_error');
    state.guidance = validateGuidance(await response.json());
    renderGuidance(state.guidance);
  } catch (error) {
    notice('guidance-status', controller.signal.aborted ? '자료를 불러오는 시간이 초과되었습니다. 다시 시도해 주세요.' : (errors[error.message] || errors.network_error), true);
    $('load-guidance').textContent = '점검 목록 다시 불러오기 ↗';
  } finally {
    clearTimeout(timer);
    $('load-guidance').disabled = false;
    $('checklist').setAttribute('aria-busy', 'false');
    $('checklist-title').focus();
  }
}
function updateCount() { $('question-count').textContent = `${$('question').value.length} / 500`; }
function setBusy(busy) {
  $('question-form').setAttribute('aria-busy', String(busy));
  for (const node of document.querySelectorAll('#submit-question, #question, #clear-context, .suggestion, .card-question, #load-guidance')) node.disabled = busy;
  $('cancel-question').hidden = !busy;
  if (busy) $('retry-question').hidden = true;
}
function renderAnswer(result) {
  $('answer-fixture').hidden = result.dataKind !== 'fixture';
  $('answer-kind').textContent = result.answer.kind === 'out_of_scope' ? '지원 범위 안내 · 근거 기반 재배 답변이 아닙니다.' : '서버에서 근거 ID 확인을 마친 설명입니다. 내용 전체의 정확성을 보증하지 않습니다.';
  $('answer-text').textContent = result.answer.text;
  $('answer-sources').replaceChildren();
  const sources = result.sources.filter(source => result.answer.evidenceIds.includes(source.id));
  if (sources.length) $('answer-sources').append(sourcesDetails(sources, result.dataKind, result.reviewedAt || state.guidance.reviewedAt));
  $('answer').hidden = false;
}
async function sendQuestion(request) {
  if (state.active || !state.guidance?.cards.length) return;
  const controller = new AbortController();
  const active = { controller, cancelled: false, timedOut: false };
  state.active = active;
  state.lastRequest = request;
  setBusy(true);
  $('answer').hidden = true;
  $('answer-text').textContent = '';
  notice('answer-status', '질문을 보내고 있습니다.');
  const timer = setTimeout(() => { active.timedOut = true; controller.abort(); }, 50000);
  try {
    const response = await fetch('/api/questions', { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' }, body: JSON.stringify(request), signal: controller.signal, cache: 'no-store' });
    if (!response.ok) {
      const code = response.status === 429 ? 'capacity_exceeded' : [400, 413, 422].includes(response.status) ? 'invalid_request' : 'model_error';
      throw Object.assign(new Error(code), { retryable: ![400, 413, 422].includes(response.status) });
    }
    const events = new QuestionEvents(stage => notice('answer-status', stages[stage] || '질문을 처리하고 있습니다.'));
    await readSSE(response, event => events.accept(event), controller.signal);
    const result = events.finish();
    renderAnswer(result);
    notice('answer-status', result.answer.kind === 'out_of_scope' ? '지원 범위 안내가 도착했습니다.' : '근거를 확인한 AI 설명이 도착했습니다.');
  } catch (error) {
    const code = active.timedOut ? 'timeout' : error.message;
    notice('answer-status', active.cancelled ? '요청을 취소했습니다. 점검 카드와 입력한 질문은 그대로 남아 있습니다.' : (errors[code] || errors.network_error), !active.cancelled);
    $('retry-question').hidden = !active.cancelled && error.retryable === false;
  } finally {
    clearTimeout(timer);
    state.active = null;
    setBusy(false);
    $('submit-question').focus({ preventScroll: true });
  }
}

$('load-guidance').addEventListener('click', loadGuidance);
$('question').addEventListener('input', () => { updateCount(); $('retry-question').hidden = true; });
$('clear-context').addEventListener('click', () => { setContext(null); $('retry-question').hidden = true; $('question').focus(); });
$('question-form').addEventListener('submit', event => {
  event.preventDefault();
  const question = $('question').value.trim();
  if (!question || question.length > 500) { $('question').setCustomValidity('1~500자의 질문을 입력해 주세요.'); $('question').reportValidity(); return; }
  const request = { scenarioId: SCENARIO_ID, question };
  if (state.cardId) request.cardId = state.cardId;
  void sendQuestion(request);
});
$('question').addEventListener('input', () => $('question').setCustomValidity(''));
$('question').addEventListener('keydown', event => {
  if (event.key === 'Enter' && (event.ctrlKey || event.metaKey) && !event.isComposing) { event.preventDefault(); $('question-form').requestSubmit(); }
});
$('cancel-question').addEventListener('click', () => { if (state.active) { state.active.cancelled = true; state.active.controller.abort(); } });
$('retry-question').addEventListener('click', () => { if (state.lastRequest) { prepareQuestion(state.lastRequest.question, state.lastRequest.cardId || null); void sendQuestion({ ...state.lastRequest }); } });
for (const question of suggestions) {
  const button = el('button', 'suggestion', question);
  button.type = 'button';
  button.addEventListener('click', () => prepareQuestion(question));
  $('suggestions').append(button);
}
window.addEventListener('pagehide', () => state.active?.controller.abort());
