// SSE frames are independent of both network chunks and UTF-8 code points.
export class SSEParser {
  constructor(onEvent) {
    this.onEvent = onEvent;
    this.buffer = '';
    this.event = '';
    this.data = [];
    this.size = 0;
    this.first = true;
  }
  feed(text) {
    if (this.first && text.length) {
      text = text.replace(/^\uFEFF/, '');
      this.first = false;
    }
    this.buffer += text;
    while (true) {
      const match = /[\r\n]/.exec(this.buffer);
      if (!match) break;
      const end = match.index;
      if (this.buffer[end] === '\r' && end === this.buffer.length - 1) break;
      const line = this.buffer.slice(0, end);
      const width = this.buffer.slice(end, end + 2) === '\r\n' ? 2 : 1;
      this.buffer = this.buffer.slice(end + width);
      this.line(line);
    }
    if (this.buffer.length + this.size > 262144) throw new Error('stream_invalid');
  }
  line(line) {
    this.size += line.length;
    if (this.size > 262144) throw new Error('stream_invalid');
    if (!line) {
      if (this.data.length) this.onEvent({ event: this.event || 'message', data: this.data.join('\n') });
      this.event = '';
      this.data = [];
      this.size = 0;
      return;
    }
    if (line.startsWith(':')) return;
    const colon = line.indexOf(':');
    const field = colon < 0 ? line : line.slice(0, colon);
    let value = colon < 0 ? '' : line.slice(colon + 1);
    if (value.startsWith(' ')) value = value.slice(1);
    if (field === 'event') this.event = value;
    if (field === 'data') this.data.push(value);
  }
  finish() {
    // A trailing CR is a line ending; unterminated events are never dispatched.
    if (this.buffer.endsWith('\r')) {
      this.line(this.buffer.slice(0, -1));
      this.buffer = '';
    }
  }
}

export async function readSSE(response, onEvent, signal) {
  if (!response.body || !response.headers.get('content-type')?.toLowerCase().includes('text/event-stream')) {
    throw new Error('stream_invalid');
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8', { fatal: true });
  const parser = new SSEParser(onEvent);
  const abort = () => { void reader.cancel().catch(() => {}); };
  signal?.addEventListener('abort', abort, { once: true });
  try {
    if (signal?.aborted) throw new Error('aborted');
    while (true) {
      const { value, done } = await reader.read();
      if (signal?.aborted) throw new Error('aborted');
      if (done) break;
      parser.feed(decoder.decode(value, { stream: true }));
    }
    parser.feed(decoder.decode());
    parser.finish();
  } finally {
    signal?.removeEventListener('abort', abort);
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}
