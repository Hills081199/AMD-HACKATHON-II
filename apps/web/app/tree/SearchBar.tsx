"use client";

import { useEffect, useRef, useState } from "react";
import { Search, X } from "lucide-react";
import type { DisplayNode } from "./types";

interface SearchBarProps {
  nodes: DisplayNode[];
  onSelect: (nodeId: string) => void;
}

export function SearchBar({ nodes, onSelect }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const results = query.trim().length > 0
    ? nodes
        .filter((n) => n.label.toLowerCase().includes(query.toLowerCase()))
        .slice(0, 8)
    : [];

  useEffect(() => {
    setActiveIdx(0);
  }, [query]);

  function handleSelect(nodeId: string) {
    onSelect(nodeId);
    setQuery("");
    setOpen(false);
    inputRef.current?.blur();
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!open || results.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (results[activeIdx]) handleSelect(results[activeIdx].id);
    } else if (e.key === "Escape") {
      setOpen(false);
      setQuery("");
    }
  }

  return (
    <div className="relative w-full max-w-xs">
      <div className="relative flex items-center">
        <Search size={14} className="absolute left-3 text-outline pointer-events-none" />
        <input
          ref={inputRef}
          id="tree-search"
          type="text"
          autoComplete="off"
          placeholder="Search concepts…"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          onKeyDown={handleKeyDown}
          className="w-full rounded-lg border border-white/10 bg-surface-container-low py-2 pl-8 pr-8 text-stats-mono text-on-surface placeholder-outline backdrop-blur focus:border-secondary/60 focus:outline-none focus:ring-1 focus:ring-secondary/40 transition-all"
        />
        {query && (
          <button
            onClick={() => { setQuery(""); setOpen(false); }}
            className="absolute right-3 text-outline hover:text-on-surface transition-colors"
            tabIndex={-1}
          >
            <X size={13} />
          </button>
        )}
      </div>

      {open && results.length > 0 && (
        <ul
          ref={listRef}
          className="absolute left-0 right-0 top-full z-50 mt-1 overflow-hidden rounded-lg border border-white/10 bg-surface-container shadow-xl"
          role="listbox"
        >
          {results.map((node, idx) => (
            <li
              key={node.id}
              role="option"
              aria-selected={idx === activeIdx}
              onMouseDown={() => handleSelect(node.id)}
              onMouseEnter={() => setActiveIdx(idx)}
              className={`flex cursor-pointer items-center gap-3 px-4 py-2.5 text-stats-mono transition-colors ${
                idx === activeIdx
                  ? "bg-secondary/15 text-secondary"
                  : "text-on-surface-variant hover:bg-white/5"
              }`}
            >
              <span
                className={`inline-block h-2 w-2 shrink-0 rounded-full ${
                  node.status === "completed"
                    ? "bg-tertiary"
                    : node.status === "unlocked"
                    ? "bg-secondary"
                    : "bg-outline-variant"
                }`}
              />
              <span className="truncate">{node.label}</span>
              <span className="ml-auto shrink-0 text-xs text-outline">L{node.level}</span>
            </li>
          ))}
        </ul>
      )}

      {open && query.trim().length > 0 && results.length === 0 && (
        <div className="absolute left-0 right-0 top-full z-50 mt-1 rounded-lg border border-white/10 bg-surface-container px-4 py-3 text-stats-mono text-outline shadow-xl">
          No concepts found
        </div>
      )}
    </div>
  );
}
