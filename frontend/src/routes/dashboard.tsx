import { createFileRoute } from '@tanstack/react-router';
import { InscriptionWorkspace } from '@/components/inscription-workspace';

export const Route = createFileRoute('/dashboard')({
  head: () => ({ meta: [
    { title: 'Translate an inscription — LipiAI' },
    { name: 'description', content: 'Upload an inscription to read its literal translation and summary with LipiAI.' },
    { property: 'og:title', content: 'Translate an inscription — LipiAI' },
    { property: 'og:description', content: 'Read the translation and summary of your inscription.' },
    { property: 'og:type', content: 'website' },
    { name: 'twitter:card', content: 'summary_large_image' },
  ] }),
  component: InscriptionWorkspace,
});