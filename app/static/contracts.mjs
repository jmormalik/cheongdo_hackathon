export const SCENARIO_ID = 'cheongdo-persimmon-postharvest';
const kinds = ['fixture', 'reviewed_static'];
const nonempty = value => typeof value === 'string' && value.trim().length > 0;
const invalid = () => { throw new Error('data_invalid'); };

export function safeURL(value) {
  try {
    const url = new URL(value);
    return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? url.href : null;
  } catch { return null; }
}

function validateSources(sources, dataKind) {
  if (!Array.isArray(sources)) invalid();
  const ids = new Set();
  for (const source of sources) {
    if (!source || !nonempty(source.id) || ids.has(source.id) || !nonempty(source.title) || !nonempty(source.scope)) invalid();
    if (dataKind === 'reviewed_static' && !safeURL(source.url)) invalid();
    if (source.publishedAt !== null && !nonempty(source.publishedAt)) invalid();
    ids.add(source.id);
  }
  return ids;
}

export function validateGuidance(data) {
  if (!data || data.scenarioId !== SCENARIO_ID || !kinds.includes(data.dataKind) || !Array.isArray(data.cards) || data.cards.length > 3) invalid();
  if (data.dataKind === 'reviewed_static' && !nonempty(data.reviewedAt)) invalid();
  const sourceIds = validateSources(data.sources, data.dataKind);
  const cardIds = new Set();
  for (const card of data.cards) {
    if (!card || !nonempty(card.id) || cardIds.has(card.id) || !nonempty(card.title) || !nonempty(card.reason) || typeof card.caution !== 'string') invalid();
    if (!Array.isArray(card.evidenceIds) || !card.evidenceIds.length || card.evidenceIds.some(id => !sourceIds.has(id))) invalid();
    cardIds.add(card.id);
  }
  return data;
}

// The server owns evidence verification. This guard prevents malformed payloads
// or unsafe source URLs from being presented as a validated answer in the UI.
export function validateResult(data) {
  const answer = data?.answer;
  if (!kinds.includes(data?.dataKind) || !answer || !['grounded', 'out_of_scope'].includes(answer.kind) || !nonempty(answer.text)) invalid();
  const sourceIds = validateSources(data.sources, data.dataKind);
  if (!Array.isArray(answer.evidenceIds) || answer.evidenceIds.some(id => !sourceIds.has(id))) invalid();
  if (answer.kind === 'grounded' && !answer.evidenceIds.length) invalid();
  return data;
}

export class QuestionEvents {
  constructor(onStatus) {
    this.onStatus = onStatus;
    this.requestId = null;
    this.seq = -1;
    this.result = null;
    this.error = null;
    this.complete = false;
  }
  accept({ event, data }) {
    if (!['status', 'result', 'error', 'complete'].includes(event)) return;
    let payload;
    try { payload = JSON.parse(data); } catch { throw new Error('stream_invalid'); }
    if (this.complete || !payload || !nonempty(payload.requestId) || !Number.isInteger(payload.seq) || payload.seq <= this.seq) throw new Error('stream_invalid');
    if (this.requestId && payload.requestId !== this.requestId) throw new Error('stream_invalid');
    this.requestId = payload.requestId;
    this.seq = payload.seq;
    if (event === 'status') {
      if (this.result || this.error) throw new Error('stream_invalid');
      this.onStatus(payload.stage);
    }
    if (event === 'result') {
      if (this.result || this.error) throw new Error('stream_invalid');
      this.result = validateResult(payload);
    }
    if (event === 'error') {
      if (this.error) throw new Error('stream_invalid');
      this.result = null;
      this.error = { code: payload.code, retryable: payload.retryable === true };
    }
    if (event === 'complete') {
      if (!['success', 'error'].includes(payload.outcome) || (payload.outcome === 'success' && (!this.result || this.error)) || (payload.outcome === 'error' && !this.error)) throw new Error('stream_invalid');
      this.complete = true;
    }
  }
  finish() {
    if (!this.complete) throw new Error('disconnected');
    if (this.error) throw Object.assign(new Error(this.error.code || 'model_error'), { retryable: this.error.retryable });
    return this.result;
  }
}
