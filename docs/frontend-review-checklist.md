# Atlas — Frontend Review Checklist

**Reviewer:** Sanket Chaudhari  
**Date:** 2026-07-07  
**Branch/Commit reviewed:** `sonchan/vibe_code` @ `2a198c3`

> **Note:** `main` branch mein sirf placeholder `TODO` code hai. Actual implemented frontend `sonchan/vibe_code` pe hai. Saari findings us branch ke against hain.

---

## 1. Design Match (vs. Stitch mockup)

- [x] Background color matches (#0D0D0D–#141414 range)
- [ ] Accent color matches (green, ~#0F9D58–#22D3A1)
- [x] Typography matches (font, heading sizes, hero italic accents)
- [x] Rounded corners consistent across cards/buttons
- [x] Node states visually distinct (locked / unlocked / completed)

**Notes:**
- Background: Implemented as `surface: #0b1326` (deep navy-blue). Checklist ka pure black (#0D0D0D) range se thoda alag hai — intentional Stitch deviation.
- Accent: **Cyan/Indigo palette adopt ki gayi** (`secondary: #4cd7f6`, `tertiary: #4edea3`) instead of green (#0F9D58–#22D3A1). Internally consistent hai par Stitch mockup se alag.
- Typography: Inter + JetBrains Mono — proper token scale (display-lg 48px, headline-lg 32px, stats-mono 14px). ✅
- Node states: `locked` = dashed border + faded text, `unlocked` = cyan glow (`glow-active`), `completed` = emerald fill. ✅

---

## 2. Responsiveness

- [x] Layout works on desktop (1440px+)
- [x] Layout works on laptop (1280px)
- [ ] Layout doesn't break on tablet/mobile (even if not primary target)
- [ ] Sidebar collapses or adapts on smaller screens

**Notes:**
- `/tree` page ka sidebar `hidden md:flex` — mobile pe **completely hide** ho jaata hai, koi fallback nahi.
- Koi hamburger menu ya drawer/sheet nahi hai — mobile users ke liye navigation completely inaccessible.
- `/` (upload page) aur `/pitch` fully responsive hain — sirf tree page problem hai.

---

## 3. Component Structure

- [x] Repeated UI elements (cards, buttons, modals) are reusable components, not copy-pasted
- [x] Consistent naming convention for components/files
- [x] Props/state kept minimal and clear

**Notes:**
- `TreeNode`, `QuizModal`, `DropZone` — sab alag files mein properly separated. ✅
- State management: Zustand (`progressStore.ts`) cleanly separates client-side progress state from UI. ✅
- `unlock.ts` mein pure functions — easily testable. ✅

---

## 4. States Handled

- [x] Empty state — no documents uploaded yet
- [x] Loading state — upload/processing (with pipeline stage indicator)
- [x] Error state — parse failure (shows which file failed)
- [ ] Error state — graph validation issue / warning banner
- [ ] Quiz fail/retry state

**Notes:**
- DropZone ka **3-step pipeline indicator** (Chunking Documents → Extracting Concepts → Building Knowledge Graph) excellent hai. ✅
- File-level validation (invalid extension rejection with specific error message) implemented. ✅
- Graph error: `/tree` page sirf `<p className="text-error">` render karta hai — koi warning banner, icon ya actionable message nahi. ❌
- Quiz fail: Result dikhta hai (score) par **retry button nahi** — user ko modal band karke dobara kholna padta hai. ❌

---

## 5. Accessibility

- [x] Sufficient text/background contrast
- [ ] Images/icons have alt text or aria-labels
- [ ] Interactive elements reachable via keyboard (tab order)
- [ ] Form inputs (quiz options) properly labeled

**Notes:**
- Contrast: `#dae2fd` on `#0b1326` — WCAG AA pass. ✅
- Icons: Sirf account button pe `aria-label="Account"` hai. Baaki icon-only buttons pe `aria-label` missing. ❌
- Keyboard: Quiz radio options keyboard se accessible hain. ReactFlow canvas ke nodes **tab-reachable nahi** — pure mouse-only interaction. ❌
- Quiz form: `<input type="radio">` implicit label association se kaam karta hai — explicit `htmlFor` + `id` pairing nahi. ⚠️

---

## 6. Performance

- [x] No obvious unnecessary re-renders
- [x] Images optimized (compressed, correct format)
- [x] Bundle size reasonable (check with build output)
- [ ] Lazy loading used where appropriate (e.g. lesson modal, heavy graph canvas)

**Notes:**
- `useMemo` properly used for `flowNodes`, `flowEdges`, `sourceDocs` in tree page. ✅
- Koi images nahi — pure lucide SVG inline icons (zero network overhead). ✅
- Build output (production):
  - `/`       →  5.07 kB  (99.8 kB first load)
  - `/pitch`  →  7.94 kB  (103 kB first load)
  - `/tree`   → 62.6 kB  (150 kB first load — ReactFlow ki wajah se expected)
- `QuizModal` eagerly imported — `React.lazy()` use karna chahiye. ❌
- ReactFlow bhi eagerly loaded — `next/dynamic` with `ssr: false` consider karo. ❌

---

## 7. Code Structure (vs. TRD)

- [x] Folder structure matches agreed convention
- [x] Environment variables used correctly (no hardcoded keys/URLs)
- [ ] API calls centralized (not scattered inline)

**Notes:**
- Folder: `app/tree/`, `app/components/` — clean aur logical. ✅
- Env vars: `NEXT_PUBLIC_API_URL` aur `NEXT_PUBLIC_GPU_WORKER_URL` correctly used. No hardcoded secrets. ✅
- API calls **scattered hain**:
  - `DropZone.tsx` mein GPU worker URL + fetch logic inline
  - `tree/page.tsx` mein API URL + fetch inline
  - Koi central `lib/api.ts` nahi — future mein auth headers ya retry logic add karna mushkil hoga. ❌

---

## Summary of Suggested Improvements

1. Mobile sidebar / navigation drawer — `/tree` page tablet+mobile pe broken
2. Quiz retry button — fail hone ke baad user stuck, UX blocker
3. Graph error warning banner — plain text error ko proper banner/alert mein upgrade karo
4. API calls centralize karo — `lib/api.ts` banao, fetch logic wahan move karo
5. `aria-label` add karo icon-only buttons pe (QuizModal close, tree nav items)
6. `QuizModal` + ReactFlow ko `React.lazy()` / `next/dynamic` se lazy load karo

---

## Priority

**High (blocks demo):**
- Mobile sidebar missing — `/tree` judges ke phone pe completely broken dikhega
- Quiz retry button — fail hone pe user stuck ho jaata hai

**Medium (should fix before submission):**
- Graph validation warning banner (proper error UI)
- `aria-label` on icon-only interactive elements
- API calls `lib/api.ts` mein centralize karo

**Low (nice to have / post-hackathon):**
- `QuizModal` + ReactFlow lazy loading
- Accent color alignment with original Stitch green mockup (if needed)
- ReactFlow nodes keyboard accessible banana (WCAG 2.1 AA)
