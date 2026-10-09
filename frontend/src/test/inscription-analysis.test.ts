import { afterEach, describe, expect, it, vi } from "vitest";
import { analyzeInscription } from "@/lib/inscription-analysis";

afterEach(() => vi.unstubAllGlobals());
describe("Inscription analysis", () => {
  it("sends the uploaded image using the FastAPI field and returns its OCR results", async () => {
    const image = new File(["image"], "inscription.png", { type: "image/png" });
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          filename: "inscription.png",
          raw_ocr: "𑐀",
          devanagari: "अ",
          analysis: "A dedication inscription.",
        }),
        { headers: { "content-type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    await expect(
      analyzeInscription(image, undefined, "https://example.test/api/digitize"),
    ).resolves.toEqual({
      rawOcr: "𑐀",
      devanagari: "अ",
      analysis: "A dedication inscription.",
    });
    expect(fetchMock.mock.calls[0]?.[0]).toBe("https://example.test/api/digitize");
    expect(fetchMock.mock.calls[0]?.[1]?.body.get("file")).toBe(image);
  });

  it("shows FastAPI error details when analysis fails", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        new Response(
          JSON.stringify({ detail: "Invalid file type. Only PNG, JPG, and JPEG are supported." }),
          { status: 400, headers: { "content-type": "application/json" } },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);
    await expect(
      analyzeInscription(
        new File(["image"], "inscription.gif"),
        undefined,
        "https://example.test/api/digitize",
      ),
    ).rejects.toThrow("Invalid file type. Only PNG, JPG, and JPEG are supported.");
  });

  it("never fabricates results when no backend is connected", async () => {
    await expect(
      analyzeInscription(new File(["image"], "stone.png"), undefined, ""),
    ).rejects.toThrow("Analysis is not connected yet.");
  });
});
