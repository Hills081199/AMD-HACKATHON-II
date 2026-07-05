import { create } from "zustand";

interface TreeProgressState {
  completedIds: Set<string>;
  seedCompleted: (ids: Iterable<string>) => void;
  markCompleted: (id: string) => void;
}

/** Client-side progress state so completing a node unlocks its children
 * immediately, without a page reload — a stand-in for feat-008's real
 * checkpoint-quiz submission, which will call markCompleted() on a pass. */
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
