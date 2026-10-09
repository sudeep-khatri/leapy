import {
  useState,
  useRef,
  useEffect,
  useCallback,
  type MutableRefObject,
  type KeyboardEvent,
} from 'react';
import { cn } from '@/lib/utils';
import {
  CHAT_MODES,
  type ChatMessage,
  convertScript,
  sendChatMessage,
} from '@/lib/chat-service';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';

export function ChatInterface() {
  const [activeModeId, setActiveModeId] = useState<string>(CHAT_MODES[0]!.id);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null) as MutableRefObject<AbortController | null>;
  const bottomRef = useRef<HTMLDivElement | null>(null) as MutableRefObject<HTMLDivElement | null>;

  const mode = CHAT_MODES.find((m) => m.id === activeModeId) ?? CHAT_MODES[0]!;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = useCallback(async () => {
    const trimmed = inputText.trim();
    if (!trimmed) return;

    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setIsLoading(true);
    setError(null);

    const userMsg: ChatMessage = {
      role: 'user',
      text: trimmed,
      displayText: trimmed,
      fontClass: mode.fontClass,
      id: crypto.randomUUID(),
      timestamp: Date.now(),
    };

    setInputText('');

    try {
      const userDisplay = await convertScript(
        trimmed,
        mode.aksharaSource,
        mode.aksharaTarget,
        ctrl.signal,
      );
      const userMsgWithDisplay: ChatMessage = { ...userMsg, displayText: userDisplay };

      setMessages((prev) => [...prev, userMsgWithDisplay]);

      const reply = await sendChatMessage(trimmed, mode, messages, ctrl.signal);

      const replyDisplay = await convertScript(
        reply,
        mode.aksharaSource,
        mode.aksharaTarget,
        ctrl.signal,
      );

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        text: reply,
        displayText: replyDisplay,
        fontClass: mode.fontClass,
        id: crypto.randomUUID(),
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') return;
      const message = err instanceof Error ? err.message : 'An unexpected error occurred.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [inputText, mode, messages]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        void handleSubmit();
      }
    },
    [handleSubmit],
  );

  return (
    <section aria-label="Chat" className="chat-page screen-enter">
      <div className="chat-mode-row">
        <label className="chat-mode-label" htmlFor="chat-mode-select">
          Mode
        </label>
        <Select value={activeModeId} onValueChange={setActiveModeId}>
          <SelectTrigger id="chat-mode-select" className="chat-mode-select">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {CHAT_MODES.map((m) => (
              <SelectItem key={m.id} value={m.id}>
                {m.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <ScrollArea className="chat-messages">
        <div role="log" aria-live="polite" aria-label="Chat messages">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                'chat-message',
                msg.role === 'user' ? 'chat-message--user' : 'chat-message--assistant',
              )}
            >
              <div className={cn('chat-message__bubble', msg.fontClass)}>{msg.displayText}</div>
              <time
                className="chat-message__time"
                dateTime={new Date(msg.timestamp).toISOString()}
              >
                {new Date(msg.timestamp).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </time>
            </div>
          ))}
          {isLoading && <p className="chat-status">…</p>}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      {error && (
        <p className="chat-error" role="alert">
          {error}
        </p>
      )}

      <div className="chat-input-row">
        <Textarea
          className="chat-input"
          placeholder="Type your message…"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={isLoading}
          aria-label="Message input"
        />
        <Button
          className="chat-send-btn"
          onClick={() => void handleSubmit()}
          disabled={isLoading || inputText.trim() === ''}
          aria-label="Send message"
        >
          Send
        </Button>
      </div>
    </section>
  );
}

export default ChatInterface;
