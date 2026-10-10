import { afterEach, describe, expect, it, vi } from "vitest";
import { sendChatMessage, CHAT_MODES } from "@/lib/chat-service";
import type { ChatMessage } from "@/lib/chat-service";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

const testMode = CHAT_MODES[0]!;

const makeHistory = (): ChatMessage[] => [];

describe("sendChatMessage", () => {
  it('throws "not connected" error when endpoint env var is empty', async () => {
    vi.stubEnv("VITE_LIPIAI_CHAT_URL", "");
    await expect(sendChatMessage("hello", testMode, makeHistory())).rejects.toThrow(
      "Backend URL not configured",
    );
  });

  it("resolves with the chat response on success", async () => {
    vi.stubEnv("VITE_LIPIAI_CHAT_URL", "https://example.test");
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          content: "Thank you",
          content_devanagari: "धन्यवाद",
          script: "devanagari",
          mode: testMode.id,
        }),
        { status: 200 },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const result = await sendChatMessage("धन्यवाद", testMode, makeHistory());
    expect(result).toEqual({
      content: "Thank you",
      content_devanagari: "धन्यवाद",
      script: "devanagari",
      mode: testMode.id,
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "https://example.test/api/chat",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          messages: [{ role: "user", text: "धन्यवाद" }],
          mode: testMode.id,
        }),
      }),
    );
  });

  it("throws when the response is missing required content fields", async () => {
    vi.stubEnv("VITE_LIPIAI_CHAT_URL", "https://example.test");
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ message: "something else" }), { status: 200 }),
      );
    vi.stubGlobal("fetch", fetchMock);
    await expect(sendChatMessage("hello", testMode, makeHistory())).rejects.toThrow(
      "Unexpected response format",
    );
  });
});
