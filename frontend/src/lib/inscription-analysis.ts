export type InscriptionResult = {
  rawOcr: string;
  devanagari: string;
  analysis: string;
};

export async function analyzeInscription(
  image: File,
  signal?: AbortSignal,
  endpoint = import.meta.env["VITE_LIPIAI_ANALYSIS_URL"],
): Promise<InscriptionResult> {
  if (!endpoint) {
    throw new Error("Image selected. Analysis is not connected yet.");
  }
  const form = new FormData();
  form.append("file", image);
  const response = await fetch(endpoint, { method: "POST", body: form, signal: signal ?? null });
  if (!response.ok) {
    if (response.headers.get("content-type")?.includes("application/json")) {
      const errorOutput: unknown = await response.json();
      if (
        errorOutput &&
        typeof errorOutput === "object" &&
        "detail" in errorOutput &&
        typeof errorOutput.detail === "string"
      ) {
        throw new Error(errorOutput.detail);
      }
    }
    throw new Error(`The image could not be analyzed (HTTP ${response.status}).`);
  }
  const output: unknown = await response.json();
  if (!output || typeof output !== "object" || Array.isArray(output)) {
    throw new Error("The analysis returned an invalid result.");
  }
  const data = output as Record<string, unknown>;
  const rawOcr = data["raw_ocr"];
  const devanagari = data["devanagari"];
  const analysis = data["analysis"];
  if (
    typeof rawOcr !== "string" ||
    typeof devanagari !== "string" ||
    typeof analysis !== "string"
  ) {
    throw new Error(
      "The analysis did not return the expected OCR and manuscript analysis results.",
    );
  }
  return { rawOcr, devanagari, analysis };
}
