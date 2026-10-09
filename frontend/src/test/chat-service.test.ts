import { afterEach, describe, expect, it, vi } from 'vitest';
import { convertScript, sendChatMessage, CHAT_MODES } from '@/lib/chat-service';
import type { ChatMessage } from '@/lib/chat-service';

afterEach(() => vi.unstubAllGlobals());

const testMode = CHAT_MODES[0]!;

const makeHistory = (): ChatMessage[] => [];

describe('convertScript', () => {
  it('returns original text without calling fetch when source === target', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    const result = await convertScript('hello', 'Devanagari', 'Devanagari');
    expect(result).toBe('hello');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('calls fetch with correct URL params and returns response text', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('रञ्जना', { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);
    const result = await convertScript('देवनागरी', 'Devanagari', 'Ranjana');
    expect(result).toBe('रञ्जना');
    const calledUrl = fetchMock.mock.calls[0]?.[0] as string;
    expect(calledUrl).toContain('aksharamukha.appspot.com');
    expect(calledUrl).toContain('source=Devanagari');
    expect(calledUrl).toContain('target=Ranjana');
    expect(calledUrl).toContain('text=');
  });

  it('returns original text when fetch throws (graceful degradation)', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error('Network error'));
    vi.stubGlobal('fetch', fetchMock);
    const result = await convertScript('नेपाल', 'Devanagari', 'Ranjana');
    expect(result).toBe('नेपाल');
  });
});

describe('sendChatMessage', () => {
  it('throws "not connected" error when endpoint env var is empty', async () => {
    await expect(sendChatMessage('hello', testMode, makeHistory(), undefined, '')).rejects.toThrow('not connected');
  });

  it('resolves with reply text on success', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ reply: 'धन्यवाद' }), { status: 200 }),
    );
    vi.stubGlobal('fetch', fetchMock);
    const result = await sendChatMessage('धन्यवाद', testMode, makeHistory(), undefined, 'https://example.test/chat');
    expect(result).toBe('धन्यवाद');
  });

  it('throws when response has no reply field', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ message: 'something else' }), { status: 200 }),
    );
    vi.stubGlobal('fetch', fetchMock);
    await expect(sendChatMessage('hello', testMode, makeHistory(), undefined, 'https://example.test/chat')).rejects.toThrow('invalid response');
  });
});
