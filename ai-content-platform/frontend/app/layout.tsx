import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Atelier — AI Content Studio",
  description:
    "Prompt-driven editorial content for digital media — Gemini drafts, evaluates, and illustrates.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-paper-200 bg-paper-50/80 backdrop-blur">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
            <Link href="/" className="flex items-center gap-3">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-ink-900 text-paper-50 font-serif text-sm">
                A
              </span>
              <span className="flex flex-col leading-tight">
                <span className="font-serif text-xl tracking-tight">Atelier</span>
                <span className="text-[10px] uppercase tracking-[0.18em] text-ink-500">
                  AI Content Studio
                </span>
              </span>
            </Link>
            <nav className="flex items-center gap-6 text-sm text-ink-700">
              <Link href="/" className="hover:text-ink-900">Studio</Link>
              <Link href="/history" className="hover:text-ink-900">Archive</Link>
              <a
                href="/docs"
                target="_blank"
                rel="noopener"
                className="hover:text-ink-900"
              >
                API
              </a>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-10">{children}</main>
        <footer className="mx-auto max-w-6xl px-6 py-10 text-xs text-ink-500">
          <div className="divider mb-6" />
          AI-driven content creation for digital media platforms — Gemini + LangChain
          orchestration with refinement, personalization, and accompanying imagery.
          Inspired by research from Dr. Ajay Kumar Sharma &amp; Chhavi Vinaik, GITS Udaipur.
        </footer>
      </body>
    </html>
  );
}
