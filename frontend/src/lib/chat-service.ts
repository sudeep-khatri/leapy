export type ChatScript = 'devanagari' | 'ranjana';
export type ChatLanguage = 'nepal-bhasa' | 'nepali';
export type ChatRole = 'user' | 'assistant';

export interface ChatMode {
  id: string;
  label: string;
  language: ChatLanguage;
  script: ChatScript;
  aksharaSource: string;
  aksharaTarget: string;
  fontClass: string;
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  text: string;
  displayText: string;
  fontClass: string;
  timestamp: number;
}

export const CHAT_MODES = [
  {
    id: 'nepal-bhasa-devanagari',
    label: 'नेपाल भाषा — देवनागरी',
    language: 'nepal-bhasa',
    script: 'devanagari',
    aksharaSource: 'Devanagari',
    aksharaTarget: 'Devanagari',
    fontClass: 'chat-font--devanagari',
  },
  {
    id: 'nepali-ranjana',
    label: 'नेपाली — रञ्जना लिपि',
    language: 'nepali',
    script: 'ranjana',
    aksharaSource: 'Devanagari',
    aksharaTarget: 'Ranjana',
    fontClass: 'chat-font--ranjana',
  },
  {
    id: 'nepal-bhasa-ranjana',
    label: 'नेपाल भाषा — रञ्जना लिपि',
    language: 'nepal-bhasa',
    script: 'ranjana',
    aksharaSource: 'Devanagari',
    aksharaTarget: 'Ranjana',
    fontClass: 'chat-font--ranjana',
  },
] as const satisfies ChatMode[];

export async function convertScript(
  text: string,
  source: string,
  target: string,
  signal?: AbortSignal,
): Promise<string> {
  if (source === target) return text;
  try {
    const url = new URL('https://aksharamukha.appspot.com/api/public');
    url.searchParams.set('source', source);
    url.searchParams.set('target', target);
    url.searchParams.set('text', text);
    const response = await fetch(url.toString(), { signal: signal ?? null });
    if (!response.ok) return text;
    return await response.text();
  } catch {
    return text;
  }
}

export async function sendChatMessage(
  userText: string,
  mode: ChatMode,
  history: ChatMessage[],
  signal?: AbortSignal,
  endpoint = import.meta.env['VITE_LIPIAI_CHAT_URL'],
): Promise<string> {
  if (!endpoint) {
    throw new Error('Chat is not connected yet.');
  }
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: userText,
      language: mode.language,
      history: history.map((m) => ({ role: m.role, text: m.text })),
    }),
    signal: signal ?? null,
  });
  if (!response.ok) {
    throw new Error('The chat request failed. Please try again.');
  }
  const data = (await response.json()) as Record<string, unknown>;
  const reply = data['reply'];
  if (typeof reply !== 'string') {
    throw new Error('The chat returned an invalid response.');
  }
  return reply;
}
