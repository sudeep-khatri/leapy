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
  /** Raw Devanagari text — sent to backend for AI context */
  text: string;
  /** Text in the display script (Devanagari or Ranjana) */
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

export interface ChatApiResponse {
  content: string;
  content_devanagari: string;
  script: ChatScript;
  mode: string;
}

/**
 * Send a chat message to the LipiAI backend.
 *
 * Backend pipeline:
 *   1. Gemini → Nepali (Devanagari)
 *   2. Google Translate → Nepal Bhasa  (Nepal Bhasa modes only)
 *   3. aksharamukha → Ranjana script   (Ranjana modes only)
 */
export async function sendChatMessage(
  userText: string,
  mode: ChatMode,
  history: ChatMessage[],
  signal?: AbortSignal,
): Promise<ChatApiResponse> {
  // Always use the explicit backend URL from env.
  // VITE_LIPIAI_CHAT_URL must be set to http://localhost:5001 in frontend/.env
  const base = (import.meta.env['VITE_LIPIAI_CHAT_URL'] as string | undefined)?.replace(/\/$/, '') ?? '';

  if (!base) {
    throw new Error(
      'Backend URL not configured. Set VITE_LIPIAI_CHAT_URL=http://localhost:5001 in frontend/.env, then restart the dev server.',
    );
  }

  const messages = [
    ...history.map((m) => ({ role: m.role, text: m.text })),
    { role: 'user' as const, text: userText },
  ];

  let response: Response;
  try {
    response = await fetch(`${base}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, mode: mode.id }),
      signal: signal ?? null,
    });
  } catch {
    throw new Error(
      'Cannot reach the backend. Make sure it is running:\n  cd leapy/backend\n  python app.py',
    );
  }

  if (!response.ok) {
    const err = await response.json().catch(() => ({ error: `HTTP ${response.status}` })) as Record<string, unknown>;
    throw new Error(typeof err['error'] === 'string' ? err['error'] : `Chat request failed (${response.status}).`);
  }

  const data = await response.json() as Record<string, unknown>;
  const content = data['content'];
  const content_devanagari = data['content_devanagari'];

  if (typeof content !== 'string' || typeof content_devanagari !== 'string') {
    throw new Error('Unexpected response format from backend.');
  }

  return {
    content,
    content_devanagari,
    script: (data['script'] as ChatScript) ?? mode.script,
    mode: (data['mode'] as string) ?? mode.id,
  };
}
