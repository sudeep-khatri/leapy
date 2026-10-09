import { createFileRoute } from "@tanstack/react-router";
import { Link } from '@tanstack/react-router';
import { Button } from '@/components/ui/button';
export const Route = createFileRoute("/")({
  head: () => ({ meta: [
    { title: 'Leapy — Readable inscription summaries' },
    { name: 'description', content: 'Leapy turns inscriptions into readable summaries. Help people understand.' },
    { property: 'og:title', content: 'Leapy — Readable inscription summaries' },
    { property: 'og:description', content: 'Leapy turns inscriptions into readable summaries.' },
    { property: 'og:type', content: 'website' },
    { name: 'twitter:card', content: 'summary_large_image' },
  ] }),
  component: Index,
});
function Index() {
  return (
    <div className="home-content screen-enter">
      <h1>Leapy turns inscriptions<br />into <em>readable summaries.</em></h1>
      <p className="home-quote">"What is written on a tablet of stone is a signature against time."</p>
      <Button asChild className="try-button"><Link to="/dashboard">Try Leapy</Link></Button>
    </div>
  );
}
