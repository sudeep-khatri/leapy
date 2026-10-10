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

const EXAMPLE_PROMPTS: Record<string, string[]> = {
  'nepal-bhasa-devanagari': [
    'नेपाल भाषा थ्व जि?',
    'काठमाडौं उपत्यकाया इतिहास वाखनं।',
    'नेवारी संस्कृतिया बारेय् वाखनं।',
  ],
  'nepali-ranjana': [
    'नमस्ते, तपाईंलाई कसरी छ?',
    'नेपालको इतिहासबारे बताउनुहोस्।',
    'रञ्जना लिपि के हो?',
  ],
  'nepal-bhasa-ranjana': [
    'नेपाल भाषाय् नमस्कार।',
    'नेवारी संस्कृतिया बारेय् वाखनं।',
    'काठमाडौंया पुलांगु इतिहास।',
  ],
};

export function ChatInterface() {
  const [activeModeId, setActiveModeId] = useState<string>(CHAT_MODES[0]!.id);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null) as MutableRefObject<AbortController | null>;
  const bottomRef = useRef<HTMLDivElement | null>(null) as MutableRefObject<HTMLDivElement | null>;
  const inputRef = useRef<HTMLTextAreaElement | null>(null) as MutableRefObject<HTMLTextAreaElement | null>;

  const mode = CHAT_MODES.find((m) => m.id === activeModeId) ?? CHAT_MODES[0]!;
  const examples = EXAMPLE_PROMPTS[activeModeId] ?? [];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleModeChange = useCallback((newModeId: string) => {
    abortRef.current?.abort();
    setActiveModeId(newModeId);
    setMessages([]);
    setError(null);
    setInputText('');
    setIsLoading(false);
  }, []);

  const handleNewConversation = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setError(null);
    setInputText('');
    setIsLoading(false);
  }, []);

  const handleSubmit = useCallback(async (textOverride?: string) => {
    const trimmed = (textOverride ?? inputText).trim();
    if (!trimmed || isLoading) return;

    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setIsLoading(true);
    setError(null);
    setInputText('');

    const userMsg: ChatMessage = {
      role: 'user',
      text: trimmed,
      displayText: trimmed,   
      fontClass: 'chat-font--devanagari',
      id: crypto.randomUUID(),
      timestamp: Date.now(),
    };

    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);

    try {
      const apiResponse = await sendChatMessage(
        trimmed,
        mode,
        messages,    
        ctrl.signal,
      );

      if (ctrl.signal.aborted) return;

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        text: apiResponse.content_devanagari,
        displayText: apiResponse.content,
        fontClass: mode.fontClass,
        id: crypto.randomUUID(),
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      if (ctrl.signal.aborted) return;
      const message = err instanceof Error ? err.message : 'An unexpected error occurred.';
      setError(message);
      setMessages(messages);
    } finally {
      if (!ctrl.signal.aborted) {
        setIsLoading(false);
        setTimeout(() => inputRef.current?.focus(), 0);
      }
    }
  }, [inputText, isLoading, mode, messages]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        void handleSubmit();
      }
    },
    [handleSubmit],
  );

  const isEmpty = messages.length === 0 && !isLoading;

  return (
    <section aria-label="Chat" className="chat-page screen-enter">

      {/* ── Mode selector ── */}
      <div className="chat-controls">
        <div className="chat-mode-row">
          <label className="chat-mode-label" htmlFor="chat-mode-select">
            भाषा / लिपि
          </label>
          <Select value={activeModeId} onValueChange={handleModeChange}>
            <SelectTrigger id="chat-mode-select" className="chat-mode-select" aria-label="Select language and script">
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

        {messages.length > 0 && (
          <Button
            variant="ghost"
            className="chat-new-btn"
            onClick={handleNewConversation}
            aria-label="Start new conversation"
          >
            New conversation
          </Button>
        )}
      </div>

      {/* ── Message area ── */}
      <ScrollArea className="chat-scroll-area">
        <div
          role="log"
          aria-live="polite"
          aria-label="Chat messages"
          aria-atomic="false"
          className="chat-messages"
        >
          {/* Welcome / empty state */}
          {isEmpty && (
            <div className="chat-welcome" aria-label="Welcome message">
              <p className="chat-welcome__title">
                {mode.label}
              </p>
              <p className="chat-welcome__subtitle">
                {mode.id === 'nepal-bhasa-devanagari' && 'Nepal Bhasa in Devanagari script'}
                {mode.id === 'nepali-ranjana' && 'Nepali in Ranjana script'}
                {mode.id === 'nepal-bhasa-ranjana' && 'Nepal Bhasa in Ranjana script'}
              </p>
              <div className="chat-examples" aria-label="Example prompts">
                {examples.map((prompt) => (
                  <button
                    key={prompt}
                    className="chat-example-chip"
                    onClick={() => void handleSubmit(prompt)}
                    type="button"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                'chat-message',
                msg.role === 'user' ? 'chat-message--user' : 'chat-message--assistant',
              )}
            >
              <div className={cn('chat-message__bubble', msg.fontClass)}>
                {msg.displayText}
              </div>
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

          {/* Loading indicator */}
          {isLoading && (
            <div className="chat-message chat-message--assistant" aria-label="Generating response">
              <div className="chat-message__bubble chat-loading">
                <span className="chat-loading__dot" />
                <span className="chat-loading__dot" />
                <span className="chat-loading__dot" />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      {/* ── Error banner ── */}
      {error && (
        <p className="chat-error" role="alert">
          {error}
        </p>
      )}

      {/* ── Input area ── */}
      <div className="chat-input-row">
        <Textarea
          ref={inputRef}
          className="chat-input"
          placeholder="Type your message… (Enter to send, Shift+Enter for new line)"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={isLoading}
          aria-label="Message input"
          aria-multiline="true"
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
