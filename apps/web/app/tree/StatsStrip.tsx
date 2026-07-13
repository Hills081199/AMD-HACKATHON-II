"use client";

interface StatsStripProps {
  nodesShown: number;
  nodesUnlocked: number;
  totalLinks: number;
  knowledgeTiers: number;
  totalNodes: number;
  isFiltered: boolean;
}

export function StatsStrip({
  nodesShown,
  nodesUnlocked,
  totalLinks,
  knowledgeTiers,
  totalNodes,
  isFiltered,
}: StatsStripProps) {
  const stats = [
    { value: nodesShown, label: isFiltered ? `of ${totalNodes} nodes shown` : "nodes shown" },
    { value: nodesUnlocked, label: "unlocked" },
    { value: totalLinks, label: "prerequisite links" },
    { value: knowledgeTiers, label: "knowledge tiers" },
  ];

  return (
    <div className="flex flex-wrap items-center gap-x-8 gap-y-2 px-1 py-3">
      {stats.map(({ value, label }) => (
        <div key={label} className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-secondary tabular-nums">{value}</span>
          <span className="text-label-caps text-on-surface-variant">{label}</span>
        </div>
      ))}
      {isFiltered && (
        <span className="ml-auto text-label-caps text-outline italic">
          Zoom in or search to reveal all {totalNodes} nodes
        </span>
      )}
    </div>
  );
}
