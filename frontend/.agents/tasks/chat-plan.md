# Implementation Plan — Nepal Bhasa & Nepali AI Chat Platform

## Exploration findings

### Critical discovery: Ranjana is font-rendering, not Unicode script conversion

The Aksharamukha public API (`https://aksharamukha.appspot.com/api/public`) returns the **same Devanagari codepoints** for `target=ranjana` — the visual transformation is entirely font-based. The `RanjanaUNICODE1.0.ttf` font maps Devanagari code points to Ranjana glyphs. Consequence: the chat UI must load the `RanjanaUnicode` font and apply it as `font-family` to message bubbles when the active mode is a `ranjana` script. No special Unicode output from the API is needed for the Ranjana modes.

The `ranjana` Aksharamukha script key is **all lowercase**. The capitalized form `Devanagari` also works for the source param (API is case-insensitive based on tests, but the script_mapping keys are all lowercase).

Noto Sans Newa renders the `newa` Unicode block (U+11400–U+1147F) — this is actual Unicode script conversion, not font-only. However per the task spec, there is no `newa` chat mode; all three modes are either `devanagari` or `ranjana` target scripts.

### TypeScript strict mode flags present

`tsconfig.json` enables: `strict`, `noPropertyAccessFromIndexSignature`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitReturns`. These require:
- Array index access returns `T | undefined` — always guard with `?? ''` or explicit check
- No `obj[key]` without type assertion or index signature type
- Optional properties cannot be assigned `undefined` explicitly — use `?` rather than `| undefined`
- All code paths must return in non-void functions

### Build & test
- Build: `npm run build` (in `c:\Users\bipul\OneDrive\Desktop\leapy\frontend`)
- Test: `npm run test` or `npx vitest run` (vitest with jsdom, `src/**/*.{test,spec}.{ts,tsx}`)
- Route registration: create `src/routes/chat.tsx` — TanStack Router auto-generates `routeTree.gen.ts` on next build

---

## Plan

- [ ] 1. Create `src/lib/chat-service.ts` — types and service functions.
      Define `ChatMode`, `ChatMessage`, and `ChatState` types. Export the three chat mode objects. Implement `convertScript(text: string, source: string, target: string): Promise<string>` using the public Aksharamukha GET API. Implement `sendChatMessage(userText: string, mode: ChatMode, history: ChatMessage[], signal?: AbortSignal): Promise<string>` that POSTs to `import.meta.env['VITE_LIPIAI_CHAT_URL']`.

      **Types:**
      ```ts
      export type ChatScript = 'devanagari' | 'ranjana';
      export type ChatLanguage = 'nepal-bhasa' | 'nepali';
      export interface ChatMode {
        id: string;
        label: string;       // native script label
        language: ChatLanguage;
        script: ChatScript;
        aksharaSource: string;  // e.g. 'Devanagari'
        aksharaTarget: string;  // e.g. 'Devanagari' | 'Ranjana'
        fontClass: string;      // CSS class to apply to output text
      }
      export type ChatRole = 'user' | 'assistant';
      export interface ChatMessage {
        id: string;
        role: ChatRole;
        text: string;           // devanagari-base text
        displayText: string;    // script-converted text for rendering
        timestamp: number;
      }
      ```

      **Three modes:**
      - `nepal-bhasa-devanagari`: aksharaSource `'Devanagari'`, aksharaTarget `'Devanagari'`, fontClass `'chat-font--devanagari'`
      - `nepali-ranjana`: aksharaSource `'Devanagari'`, aksharaTarget `'Ranjana'`, fontClass `'chat-font--ranjana'`
      - `nepal-bhasa-ranjana`: aksharaSource `'Devanagari'`, aksharaTarget `'Ranjana'`, fontClass `'chat-font--ranjana'`

      **Aksharamukha call:**
      ```ts
      const AKSHARA_URL = 'https://aksharamukha.appspot.com/api/public';
      export async function convertScript(text: string, source: string, target: string): Promise<string> {
        if (source === target) return text;
        const url = new URL(AKSHARA_URL);
        url.searchParams.set('source', source);
        url.searchParams.set('target', target);
        url.searchParams.set('text', text);
        const res = await fetch(url.toString());
        if (!res.ok) return text; // graceful degradation
        return res.text();
      }
      ```

      **sendChatMessage** checks for missing endpoint and throws `'Chat is not connected yet.'`.
      Request body: `{ message: string, language: ChatLanguage, history: Array<{role: ChatRole, text: string}> }` as JSON.
      Response shape: `{ reply: string }` — validate `typeof reply === 'string'` before returning.

      Files: `src/lib/chat-service.ts`
      Verify: `npx vitest run src/test/chat-service.test.ts` — tests for convertScript (mocked fetch), sendChatMessage (no-endpoint error, success path) pass. If no test file yet, this step includes creating `src/test/chat-service.test.ts` following the pattern in `src/test/inscription-analysis.test.ts`.

- [ ] 2. Create `src/components/chat-interface.tsx` — full chat UI component.

      **Component state:**
      ```ts
      const [activeModeId, setActiveModeId] = useState<string>(CHAT_MODES[0].id);
      // CHAT_MODES[0] is always defined — still guard: const mode = CHAT_MODES.find(m => m.id === activeModeId) ?? CHAT_MODES[0]!
      const [messages, setMessages] = useState<ChatMessage[]>([]);
      const [inputText, setInputText] = useState('');
      const [isLoading, setIsLoading] = useState(false);
      const [error, setError] = useState<string | null>(null);
      const abortRef = useRef<AbortController | null>(null);
      const bottomRef = useRef<HTMLDivElement | null>(null);
      ```

      **Message send flow:**
      1. User submits → create user `ChatMessage`, immediately append to `messages`.
      2. Call `convertScript(inputText, mode.aksharaSource, mode.aksharaTarget)` → set `displayText` on the user message.
      3. Call `sendChatMessage(inputText, mode, messages, abortRef.current.signal)` → get `reply`.
      4. Call `convertScript(reply, mode.aksharaSource, mode.aksharaTarget)` for assistant `displayText`.
      5. Append assistant `ChatMessage`.
      6. Auto-scroll via `bottomRef.current?.scrollIntoView({ behavior: 'smooth' })` in a `useEffect` on `messages`.

      **Important**: Both `convertScript` calls run sequentially (not parallel) so the user sees the typed form first, then the converted reply. If `convertScript` fails, fall back to the original text (no error state for conversion failures).

      **shadcn/ui mapping:**
      - Mode selector: `<Select>` + `<SelectTrigger>` + `<SelectContent>` + `<SelectItem>` from `@/components/ui/select`
      - Message list container: `<ScrollArea>` from `@/components/ui/scroll-area` with `className="chat-messages"`
      - Input field: `<Textarea>` from `@/components/ui/textarea` (already in ui/) — auto-resize via `onInput` adjusting `rows`
      - Send button: `<Button>` with `variant="default"` and `disabled={isLoading || inputText.trim() === ''}`
      - Error display: plain `<p className="chat-error">` — no Dialog needed

      **Keyboard handling:** `onKeyDown` on Textarea — `Enter` without `Shift` submits; `Shift+Enter` inserts newline.

      **Accessibility:**
      - `<section aria-label="Chat">` wrapping the whole component
      - Message list: `role="log"` `aria-live="polite"` on the ScrollArea viewport
      - Mode selector: `<label htmlFor="chat-mode-select">` linked via id
      - Send button: `aria-label="Send message"` when icon-only

      **Font family per message:** render each message bubble with `className={cn('chat-message__bubble', mode.fontClass)}`. The font class is determined by the *mode active at send time*, so store a `fontClass` field on each `ChatMessage`.

      Update `ChatMessage` interface to add `fontClass: string`.

      Files: `src/components/chat-interface.tsx`
      Verify: `npm run build` completes with no TypeScript errors.

- [ ] 3. Create `src/routes/chat.tsx` — TanStack route for `/chat`.

      Follow the exact pattern from `src/routes/about.tsx` and `src/routes/dashboard.tsx`:
      ```ts
      import { createFileRoute } from '@tanstack/react-router';
      import { ChatInterface } from '@/components/chat-interface';
      export const Route = createFileRoute('/chat')({
        head: () => ({ meta: [...] }),
        component: ChatInterface,
      });
      ```
      Meta: title `'Chat — LipiAI'`, description `'Chat in Nepal Bhasa and Nepali with script conversion.'`.

      Files: `src/routes/chat.tsx`
      Verify: `npm run build` — TanStack Router regenerates `routeTree.gen.ts` with `/chat` included (check file timestamp or search for `'chat'` in the gen file). Do NOT manually edit `routeTree.gen.ts`.

- [ ] 4. Modify `src/components/lipiAI-shell.tsx` — add Chat nav link.

      In the `.site-nav` `<nav>`, add a `<Link>` to `/chat` between the About link and the logo mark. Exact insertion:
      ```tsx
      <Link to="/about" className="nav-link">About</Link>
      <Link to="/chat" className="nav-link">Chat</Link>   {/* ← add this line */}
      <Link to="/" className="logo-mark" aria-label="LipiAI home">
      ```
      No other changes to this file.

      Files: `src/components/lipiAI-shell.tsx`
      Verify: `npm run build` passes; manually confirm nav renders 3 links + logo at dev server.

- [ ] 5. Modify `src/routes/__root.tsx` — add Noto Sans Newa + Noto Serif Tibetan fonts.

      In the `head()` function's `links` array, add after the existing Google Fonts link:
      ```ts
      { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Noto+Sans+Newa&family=Noto+Serif+Tibetan&display=swap' },
      ```
      Note: the Google Fonts `href` parameter syntax uses `+` for spaces within a family name. Keep the existing EB Garamond + Lato link intact.

      Files: `src/routes/__root.tsx`
      Verify: `npm run build` passes with no errors.

- [ ] 6. Append chat-specific CSS to `src/styles.css`.

      Add at the very bottom of the file, after the existing `.notice-body` rule:

      ```css
      /* ── Fonts ─────────────────────────────────────────────── */
      @font-face {
        font-family: 'RanjanaUnicode';
        src: url('https://cdn.jsdelivr.net/gh/virtualvinodh/aksharamukha/aksharamukha-front/src/statics/RanjanaUNICODE1.0.ttf') format('truetype');
        font-display: swap;
      }

      :root {
        --chat-bg:          oklch(0.243 0.064 247);      /* same as --result-panel */
        --chat-msg-user:    oklch(0.299 0.082 249);      /* same as --result-field */
        --chat-msg-ai:      oklch(0.22 0.055 246);
        --chat-text:        oklch(0.805 0.019 244);      /* same as --result-text */
        --chat-input-bg:    oklch(0.299 0.082 249);
        --chat-border:      oklch(0.38 0.07 247 / 60%);
        --chat-send-bg:     oklch(0.255 0.036 242);      /* same as --primary */
        --chat-send-fg:     oklch(0.95 0.008 244);
      }

      /* Page layout */
      .chat-page { width: 100%; max-width: 780px; padding: 28px 4% 40px; display: flex; flex-direction: column; gap: 20px; margin-top: -20px; }

      /* Mode selector row */
      .chat-mode-row { display: flex; align-items: center; gap: 12px; }
      .chat-mode-label { font-size: 14px; font-weight: 700; color: var(--nav-ink); white-space: nowrap; }
      .chat-mode-select { min-width: 260px; background: var(--chat-input-bg); border-color: var(--chat-border); color: var(--chat-text); }

      /* Message list */
      .chat-messages { background: var(--chat-bg); border-radius: 12px; height: 440px; padding: 16px; display: flex; flex-direction: column; gap: 12px; }

      /* Message bubbles */
      .chat-message { display: flex; flex-direction: column; max-width: 78%; }
      .chat-message--user { align-self: flex-end; align-items: flex-end; }
      .chat-message--assistant { align-self: flex-start; align-items: flex-start; }
      .chat-message__bubble { padding: 10px 14px; border-radius: 14px; font-size: 16px; line-height: 1.55; color: var(--chat-text); white-space: pre-wrap; word-break: break-word; }
      .chat-message--user   .chat-message__bubble { background: var(--chat-msg-user); border-bottom-right-radius: 4px; }
      .chat-message--assistant .chat-message__bubble { background: var(--chat-msg-ai); border-bottom-left-radius: 4px; }
      .chat-message__time { font-size: 11px; color: var(--chat-text); opacity: 0.55; margin-top: 3px; }

      /* Font variants applied to message bubbles */
      .chat-font--devanagari { font-family: var(--font-body); }
      .chat-font--ranjana    { font-family: 'RanjanaUnicode', var(--font-body); }

      /* Status messages */
      .chat-status { font-family: var(--font-literary); font-style: italic; font-size: 15px; color: var(--chat-text); opacity: 0.7; align-self: center; padding: 6px 0; }
      .chat-error  { font-size: 13px; color: var(--destructive); margin: 4px 0 0; text-align: center; }

      /* Input row */
      .chat-input-row { display: flex; align-items: flex-end; gap: 10px; }
      .chat-input { flex: 1; background: var(--chat-input-bg); border-color: var(--chat-border); color: var(--chat-text); resize: none; min-height: 44px; max-height: 140px; overflow-y: auto; scrollbar-color: var(--scroll-thumb) var(--chat-input-bg); scrollbar-width: thin; }
      .chat-input::placeholder { color: var(--chat-text); opacity: 0.45; }
      .chat-send-btn { height: 44px; padding: 0 18px; background: var(--chat-send-bg); color: var(--chat-send-fg); flex-shrink: 0; }
      .chat-send-btn:hover { background: oklch(from var(--chat-send-bg) calc(l + 0.05) c h); }
      .chat-send-btn:disabled { opacity: 0.45; }

      /* Responsive */
      @media (max-width: 640px) {
        .chat-page { padding: 20px 5% 32px; margin-top: 0; }
        .chat-messages { height: 360px; }
        .chat-message { max-width: 90%; }
        .chat-mode-select { min-width: 200px; }
      }
      ```

      Files: `src/styles.css`
      Verify: `npm run build` passes; no duplicate CSS variable names introduced.

- [ ] 7. Create `frontend/.env.example`.

      ```
      # AI chat endpoint — receives { message, language, history } JSON, returns { reply: string }
      VITE_LIPIAI_CHAT_URL=

      # Inscription analysis endpoint — receives multipart/form-data with 'image' field
      VITE_LIPIAI_ANALYSIS_URL=
      ```

      Files: `frontend/.env.example`
      Verify: file exists with both variables documented.

- [ ] 8. Write unit tests for `chat-service.ts` in `src/test/chat-service.test.ts`.

      Follow `inscription-analysis.test.ts` patterns:
      - `convertScript`: mock `fetch` to return `'𑐣𑐩𑐴𑐾'`, assert the URL built contains correct `source`, `target`, `text` params.
      - `convertScript` with `source === target`: assert fetch is NOT called and original text is returned.
      - `convertScript` fetch error: assert original text returned (graceful degradation — no throw).
      - `sendChatMessage` with no endpoint: assert throws `'Chat is not connected yet.'`.
      - `sendChatMessage` success: mock fetch returns `{ reply: 'धन्यवाद' }`, assert resolved value is `'धन्यवाद'`.
      - `sendChatMessage` invalid response: mock returns `{}` (no `reply`), assert throws.

      `afterEach(() => vi.unstubAllGlobals())` required per project pattern.

      Files: `src/test/chat-service.test.ts`
      Verify: `npx vitest run src/test/chat-service.test.ts` — all tests pass.

- [ ] 9. Final build verification.

      Run `npm run build` from `c:\Users\bipul\OneDrive\Desktop\leapy\frontend`. Confirm: exit code 0, no TypeScript errors, `routeTree.gen.ts` now references `/chat`. Then run `npm run test` — all existing + new tests pass.

      Files: none
      Verify: `npm run build && npm run test` — both exit 0.

---

## Strict-mode pitfalls to avoid

1. **`CHAT_MODES[0]`** — `noUncheckedIndexedAccess` makes this `ChatMode | undefined`. Use `CHAT_MODES[0]!` (non-null assertion with `!`) only in places where the array is a const tuple, or use `CHAT_MODES.find(...)  ?? CHAT_MODES[0]!` with a fallback.

2. **Array destructuring from `find()`** — returns `T | undefined`. Always guard: `const mode = CHAT_MODES.find(m => m.id === id) ?? CHAT_MODES[0]!`.

3. **Optional chaining on `abortRef.current`** — `abortRef.current?.abort()` not `abortRef.current.abort()`.

4. **`response.json()`** returns `unknown` — cast via `const data = await response.json() as Record<string, unknown>` then narrow `reply` field.

5. **`exactOptionalPropertyTypes`** — do not write `fontClass?: string | undefined`; write `fontClass?: string`.

6. **`noImplicitReturns`** — every switch branch and if/else in non-void functions must return.

7. **`import.meta.env['VITE_LIPIAI_CHAT_URL']`** — use bracket notation (not dot) to satisfy `noPropertyAccessFromIndexSignature` on the Vite `ImportMeta` interface.

---

## Architecture decision record

**Aksharamukha API call placement**: conversion happens on the service layer (`chat-service.ts`), not inside the component render. This keeps the component stateless w.r.t. async font loading and lets tests mock a single `fetch` stub.

**Ranjana rendering strategy**: font-only (load `RanjanaUNICODE1.0.ttf` from CDN via `@font-face`, apply via `.chat-font--ranjana` class). The API returns Devanagari codepoints; the font does the visual work. This is exactly how the Aksharamukha web frontend handles it.

**AI endpoint contract**: kept identical in shape to `inscription-analysis.ts` (simple `fetch` + JSON) to minimise backend surface. The endpoint receives `{ message, language, history }` and returns `{ reply }`.

**No client-side streaming**: the spec doesn't require it and SSR with TanStack Start adds complexity. A simple awaited fetch is sufficient.
