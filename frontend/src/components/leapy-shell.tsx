import { Link } from '@tanstack/react-router';
import { Instagram, Youtube } from 'lucide-react';
import { useState, type ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/dialog';

export function LeapyShell({ children }: { children: ReactNode }) {
  const [notice, setNotice] = useState<string | null>(null);
  const DISCORD_URL = 'https://discord.com/invite/YOUR_SERVER_CODE';

  return (
    <div className="leapy-shell">
      <header className="site-header">
        <nav className="site-nav" aria-label="Main navigation">
          <Link to="/about" className="nav-link">About</Link>
          <Link to="/" className="logo-mark" aria-label="Leapy home">
            <img src="/logo.png" alt="" width={44} height={44} />
          </Link>
          <Button variant="ghost" className="nav-action" onClick={() => setNotice('Community')}>Community</Button>
        </nav>
      </header>
      <main className="page-main">{children}</main>
      <footer className="site-footer">
        <div className="footer-top">
          <div><div className="footer-brand">Leapy</div><div className="footer-tagline">Help people understand.</div></div>
          <div className="footer-links">
            <Button variant="ghost" className="footer-action" onClick={() => setNotice('Privacy Policy')}>Privacy Policy</Button>
            <Button variant="ghost" className="footer-action" onClick={() => setNotice('Terms & Conditions')}>Terms &amp; Conditions</Button>
          </div>
        </div>
        <div className="footer-bottom">
          <div className="copyright">© 2026 Leapy</div>
          <div className="footer-social">
            <a className="footer-social-link" href="https://www.instagram.com/theorist_chess/" target="_blank" rel="noopener noreferrer" aria-label="Leapy on Instagram">
              <Instagram size={29} strokeWidth={1.4} aria-hidden="true" />
            </a>
            <a className="footer-social-link" href="https://www.youtube.com/@TheoristChess" target="_blank" rel="noopener noreferrer" aria-label="Leapy on YouTube">
              <Youtube size={29} strokeWidth={1.4} aria-hidden="true" />
            </a>
          </div>
        </div>
      </footer>
      <Dialog open={notice !== null} onOpenChange={(open) => { if (!open) setNotice(null); }}>
        <DialogContent>
          <DialogTitle className="notice-title">{notice}</DialogTitle>
          <DialogDescription className="notice-body">
            {notice === 'Community' ? (
              <>
                Join the leapy community: <a href={DISCORD_URL} target="_blank" rel="noreferrer noopener" className="underline text-primary hover:opacity-80">Click here</a>
              </>
            ) : (
              'This page has not been provided yet.'
            )}
          </DialogDescription>
        </DialogContent>
      </Dialog>
    </div>
  );
}