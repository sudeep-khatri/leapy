import { createFileRoute } from '@tanstack/react-router';

export const Route = createFileRoute('/about')({
  head: () => ({ meta: [
    { title: 'About — Leapy' },
    { name: 'description', content: 'Connecting the inscriptions of the Kathmandu Valley with modern understanding.' },
    { property: 'og:title', content: 'About — Leapy' },
    { property: 'og:description', content: 'Preserving Prachalit Newa inscriptions for generations.' },
    { property: 'og:type', content: 'website' },
    { name: 'twitter:card', content: 'summary_large_image' },
  ] }),
  component: About,
});

function About() {
  return <article className="about-content screen-enter">
    <p>Inscriptions carved in Prachalit Newa script keep centuries of history, culture and wisdom in the Kathmandu Valley. Yet reading and translating these artifacts needs rare epigraphic knowledge so much cultural heritage remains out of reach for the modern world.</p>
    <p>Our platform connects history with modern technology. By connecting OCR models with LLMS such, as Gemma we automatically transcribe inscriptions and create useful context-aware summaries instantly.</p>
    <p>Whether you are a researcher, a student or a history enthusiast our goal is to make ancient texts easy to read, translate and keep safe for generations.</p>
  </article>;
}