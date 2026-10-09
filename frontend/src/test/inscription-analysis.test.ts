import { afterEach, describe, expect, it, vi } from 'vitest';
import { analyzeInscription } from '@/lib/inscription-analysis';

afterEach(() => vi.unstubAllGlobals());
describe('Inscription analysis', () => {
  it('sends the uploaded image and returns the backend translation and summary', async () => {
    const image = new File(['image'], 'inscription.png', { type: 'image/png' });
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ literal_translation: 'A stone dedication.', summary: 'A dedication inscription.' })));
    vi.stubGlobal('fetch', fetchMock);
    await expect(analyzeInscription(image, undefined, 'https://example.test/analyze')).resolves.toEqual({ translation: 'A stone dedication.', summary: 'A dedication inscription.' });
    expect(fetchMock.mock.calls[0]?.[1]?.body.get('image')).toBe(image);
  });
  it('never fabricates results when no backend is connected', async () => {
    await expect(analyzeInscription(new File(['image'], 'stone.png'), undefined, '')).rejects.toThrow('Analysis is not connected yet.');
  });
});