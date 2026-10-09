export type InscriptionResult = { translation: string; summary: string };

// An existing backend can be connected without adding server code to this site.
export async function analyzeInscription(
  image: File,
  signal?: AbortSignal,
  endpoint = import.meta.env['VITE_LEAPY_ANALYSIS_URL'],
): Promise<InscriptionResult> {
  if (!endpoint) {
    throw new Error('Image selected. Analysis is not connected yet.');
  }
  const form = new FormData();
  form.append('image', image);
  const response = await fetch(endpoint, { method: 'POST', body: form, signal: signal ?? null });
  if (!response.ok) throw new Error('The image could not be analyzed. Please try again.');
  const output: unknown = await response.json();
  if (!output || typeof output !== 'object') throw new Error('The analysis returned an invalid result.');
  const data = output as Record<string, unknown>;
  const translation = data['translation'] ?? data['literal_translation'];
  const summary = data['summary'];
  if (typeof translation !== 'string' || typeof summary !== 'string') {
    throw new Error('The analysis did not return a translation and summary.');
  }
  return { translation, summary };
}