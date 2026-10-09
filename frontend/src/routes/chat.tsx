import { createFileRoute } from '@tanstack/react-router';
import ChatInterface from '@/components/chat-interface';

export const Route = createFileRoute('/chat')({
  head: () => ({ meta: [
    { title: 'Chat — LipiAI' },
    { name: 'description', content: 'Chat in Nepal Bhasa and Nepali with script conversion.' },
    { property: 'og:title', content: 'Chat — LipiAI' },
    { property: 'og:type', content: 'website' },
    { name: 'twitter:card', content: 'summary_large_image' },
  ] }),
  component: ChatInterface,
});
