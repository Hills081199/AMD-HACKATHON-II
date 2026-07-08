import Link from "next/link";
import { ArrowRight, FileText, Upload, Workflow } from "lucide-react";
import { UserMenu } from "./components/UserMenu";

export default function HomePage() {
  return (
    <div className="relative flex min-h-screen flex-col overflow-x-hidden bg-surface text-on-surface">
      <div className="pointer-events-none fixed inset-0 z-0 bg-graph-pattern opacity-20" />
      <div className="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-surface via-surface/90 to-surface" />

      <header className="fixed top-0 z-50 flex h-16 w-full items-center justify-between border-b border-white/10 bg-surface/70 px-margin-mobile shadow-sm backdrop-blur-xl md:px-margin-desktop">
        <div className="text-headline-lg font-bold tracking-tight text-on-surface">Atlas</div>
        <UserMenu />
      </header>

      <main className="z-10 flex flex-grow flex-col items-center justify-center px-margin-mobile pb-16 pt-24 md:px-margin-desktop">
        <div className="mx-auto mb-12 max-w-4xl text-center">
          <h1 className="mb-6 text-display-lg text-on-surface">
            Turn your messy documents into a masterclass.
          </h1>
          <p className="mx-auto max-w-2xl text-body-md text-on-surface-variant">
            Upload PDFs, slides, and papers. Our AI builds the optimal dependency-aware skill tree
            for you.
          </p>
        </div>

        <Link href="/tree" className="group relative mx-auto mb-4 w-full max-w-3xl cursor-pointer">
          <div className="pointer-events-none absolute inset-0 rounded-xl bg-secondary/10 opacity-0 blur-xl transition-opacity duration-500 group-hover:opacity-100" />
          <div className="glass-panel glow-active relative z-10 flex min-h-[300px] flex-col items-center justify-center rounded-xl border border-dashed border-outline-variant p-12 transition-colors duration-300 group-hover:border-secondary">
            <div className="mb-8 flex items-center justify-center gap-6 text-on-surface-variant transition-colors duration-300 group-hover:text-secondary">
              <FileText size={44} strokeWidth={1.5} />
              <ArrowRight size={28} strokeWidth={1.5} />
              <Workflow size={44} strokeWidth={1.5} />
            </div>
            <h3 className="mb-2 text-headline-lg-mobile text-on-surface">Drag &amp; Drop Files Here</h3>
            <p className="mb-6 text-body-md text-outline">Supports .pdf, .pptx, .docx</p>
            <span className="flex items-center gap-2 rounded bg-primary px-8 py-3 text-label-caps text-on-primary shadow-sm transition-colors group-hover:bg-primary-container">
              <Upload size={16} />
              BROWSE FILES
            </span>
          </div>
        </Link>
        <p className="text-stats-mono text-outline">Opens the pre-indexed demo mastery tree.</p>
      </main>

      <footer className="relative z-10 flex w-full flex-col items-center justify-between gap-gutter border-t border-white/5 bg-surface px-margin-mobile py-16 text-stats-mono text-tertiary md:flex-row md:px-margin-desktop">
        <div className="mb-4 text-label-caps text-on-surface opacity-80 transition-opacity hover:opacity-100 md:mb-0">
          Atlas
        </div>
        <div className="mb-4 text-center text-outline md:mb-0 md:text-left">
          © 2024 Atlas AI. Powered by AMD ROCm &amp; Fireworks AI
        </div>
        <div className="flex gap-6">
          <a className="text-outline underline transition-all hover:text-tertiary" href="#">
            Project Info
          </a>
          <a className="text-outline underline transition-all hover:text-tertiary" href="#">
            Privacy
          </a>
          <a className="text-outline underline transition-all hover:text-tertiary" href="#">
            Terms
          </a>
        </div>
      </footer>
    </div>
  );
}
