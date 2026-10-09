import { createFileRoute } from "@tanstack/react-router";
import { Link } from '@tanstack/react-router';
import { Button } from '@/components/ui/button';
export const Route = createFileRoute("/")({
  head: () => ({ meta: [
    { title: 'LipiAI — Readable inscription summaries' },
    { name: 'description', content: 'LipiAI turns inscriptions into readable summaries. Help people understand.' },
    { property: 'og:title', content: 'LipiAI — Readable inscription summaries' },
    { property: 'og:description', content: 'LipiAI turns inscriptions into readable summaries.' },
    { property: 'og:type', content: 'website' },
    { name: 'twitter:card', content: 'summary_large_image' },
  ] }),
  component: Index,
});
function Index() {
  return (
    <div className="home-content screen-enter">
      <h1>LipiAI turns inscriptions<br />into <em>readable summaries.</em></h1>
      <p className="home-quote">"What is written on a tablet of stone is a signature against time."</p>
      <Button asChild className="try-button"><Link to="/dashboard">Try LipiAI</Link></Button>
    </div>
  );
}
