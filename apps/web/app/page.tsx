import { Header } from "./components/Header";
import { DropZone } from "./components/DropZone";

export default function HomePage() {
  return (
    <div className="relative flex min-h-screen flex-col overflow-x-hidden bg-surface text-on-surface">
      <div className="pointer-events-none fixed inset-0 z-0 bg-graph-pattern opacity-20" />
      <div className="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-surface via-surface/90 to-surface" />

      <Header />

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

        <DropZone />
      </main>

      <footer className="relative z-10 flex w-full flex-col items-center justify-between gap-gutter border-t border-white/5 bg-surface px-margin-mobile py-16 text-stats-mono text-tertiary md:flex-row md:px-margin-desktop">
        <div className="mb-4 text-label-caps text-on-surface opacity-80 transition-opacity hover:opacity-100 md:mb-0">
          Atlas
        </div>
        <div className="mb-4 text-center text-outline md:mb-0 md:text-left">
          © 2026 Atlas AI. Powered by AMD ROCm &amp; Fireworks AI
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
