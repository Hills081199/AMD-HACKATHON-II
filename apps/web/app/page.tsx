export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-2xl font-medium">Atlas</h1>
      <p className="text-neutral-500">
        Mastery tree UI goes here — see{" "}
        <code className="rounded bg-neutral-100 px-1">app/tree/page.tsx</code>{" "}
        (to be added) and wire it to <code className="rounded bg-neutral-100 px-1">/data/atlas_mastery_tree_sample.json</code>.
      </p>
    </main>
  );
}
