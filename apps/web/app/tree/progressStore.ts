import { create } from "zustand";

interface TreeProgressState {
  completedIds: Set<string>;
  seedCompleted: (ids: Iterable<string>) => void;
  markCompleted: (id: string) => void;
}

/** Client-side progress state so completing a node unlocks its children
 * immediately, without a page reload. page.tsx calls markCompleted() when
 * feat-008's checkpoint-quiz submission (POST .../submit-quiz) reports a
 * pass. */
export const useTreeProgressStore = create<TreeProgressState>((set) => ({
  completedIds: new Set(),
  seedCompleted: (ids) => set({ completedIds: new Set(ids) }),
  markCompleted: (id) =>
    set((state) => {
      const next = new Set(state.completedIds);
      next.add(id);
      return { completedIds: next };
    }),
}));
