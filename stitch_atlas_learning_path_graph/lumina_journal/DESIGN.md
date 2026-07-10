---
name: Lumina Journal
colors:
  surface: '#121316'
  surface-dim: '#121316'
  surface-bright: '#38393c'
  surface-container-lowest: '#0d0e11'
  surface-container-low: '#1a1b1e'
  surface-container: '#1f1f23'
  surface-container-high: '#292a2d'
  surface-container-highest: '#343538'
  on-surface: '#e3e2e6'
  on-surface-variant: '#bacbbe'
  inverse-surface: '#e3e2e6'
  inverse-on-surface: '#2f3033'
  outline: '#859589'
  outline-variant: '#3c4a41'
  surface-tint: '#26e19a'
  primary: '#78ffbd'
  on-primary: '#003823'
  primary-container: '#2ee59d'
  on-primary-container: '#00623f'
  inverse-primary: '#006c47'
  secondary: '#dab9ff'
  on-secondary: '#460283'
  secondary-container: '#602b9d'
  on-secondary-container: '#cfa7ff'
  tertiary: '#ffe0d7'
  on-tertiary: '#5e1700'
  tertiary-container: '#ffbaa5'
  on-tertiary-container: '#92381a'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#53feb4'
  primary-fixed-dim: '#26e19a'
  on-primary-fixed: '#002112'
  on-primary-fixed-variant: '#005234'
  secondary-fixed: '#eedbff'
  secondary-fixed-dim: '#dab9ff'
  on-secondary-fixed: '#2a0053'
  on-secondary-fixed-variant: '#5e289b'
  tertiary-fixed: '#ffdbd0'
  tertiary-fixed-dim: '#ffb59e'
  on-tertiary-fixed: '#3a0b00'
  on-tertiary-fixed-variant: '#7f2a0d'
  background: '#121316'
  on-background: '#e3e2e6'
  surface-variant: '#343538'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 34px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Space Grotesk
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: 0.05em
  annotation:
    fontFamily: Plus Jakarta Sans
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-padding: 24px
  gutter: 16px
  margin-sm: 16px
  margin-md: 32px
  margin-lg: 64px
---

## Brand & Style

The design system is centered on the concept of an "Enchanted Lab Notebook"—a digital sanctuary where the rigor of data meets the whimsy of discovery. It is designed for researchers, students, and creative thinkers who want to gamify their cognitive workflows. The aesthetic is a high-fidelity blend of **Modern Glassmorphism** and **Analog Sketching**, creating a "Techno-Parchment" feel.

The emotional response should be one of "Inspired Focus"—dark enough to minimize eye strain during deep work, but punctuated with vibrant neon "sparks" that signify AI activity and personal achievements.

**Key Stylistic Pillars:**
- **Techno-Parchment:** Deep, textured backgrounds that feel like heavy paper but behave like liquid glass.
- **Ink & Glow:** High-contrast interactions where buttons feel like glowing stickers and lines appear as organic ink strokes.
- **Gamified Momentum:** Every interaction should feel tactile and rewarding, using bouncy physics and "sparkle" motifs for AI-driven insights.

## Colors

The palette shifts away from clinical grays toward a "Deep Midnight" foundation.
- **Primary (Mint Glow):** Used for "Success" states, primary actions, and AI-generated text highlights. It represents growth and discovery.
- **Secondary (Electric Purple):** Used for secondary interactions, "Magic" AI features, and deep-link navigation.
- **Tertiary (Sunset Orange):** Used for gamification elements, streaks, and urgent notifications.
- **Base (Midnight Ink):** A very dark navy-charcoal (#0F1115) with a subtle grain texture, serving as the "paper."
- **Surface (Glass):** Semi-transparent layers of the base color with a slight blur to create depth without losing the "dark journal" atmosphere.

## Typography

The typography system balances the technical precision of **Inter** with the friendly, rounded geometry of **Plus Jakarta Sans**. 

- **Headlines:** Use Plus Jakarta Sans with tight tracking. On desktop, use XL for section headers to create a "title page" feel.
- **Body Text:** Inter is the workhorse for all long-form journal entries and AI summaries, ensuring maximum readability against dark, textured backgrounds.
- **Technical Accents:** **Space Grotesk** is used for labels, metadata, and "system" messages to provide a slight futuristic, technical edge.
- **Annotations:** Italicized Plus Jakarta Sans is used for margin notes and user-added "scribbles" to mimic the look of side-notes in a physical journal.

## Layout & Spacing

This design system uses a **Fluid Center-Aligned Grid** to mimic the focus of a physical notebook. 

- **Desktop:** A 12-column grid with a max-width of 1200px. Content is centered with wide "margin" gutters (64px+) used for floating AI annotations and "sticker" badges.
- **Tablet:** 8-column grid with 32px margins. Sidebars collapse into glassmorphic overlays.
- **Mobile:** 4-column grid with 16px margins. Layout relies on vertical stacking with "card" containers that have organic, slightly irregular padding (e.g., 20px top, 24px sides) to feel less rigid.

Spacing follows an 8px base unit. Use generous whitespace (margins) between conceptual blocks to allow the "paper" texture to breathe.

## Elevation & Depth

Depth in this design system is achieved through **Luminous Layering** rather than traditional gray shadows.

1.  **The Base:** A textured, dark background with a very subtle fixed noise overlay.
2.  **The Page (Level 1):** Subtle glassmorphism (10% opacity white fill, 12px backdrop blur). Use a thin, 1px semi-transparent border to define the edge.
3.  **Floating Elements (Level 2):** Stronger blur (24px) and a "Mint Glow" or "Purple Glow" ambient shadow. These shadows should have a 15-20% opacity and a large spread (30px+) to look like light emitting from the element.
4.  **Stickers & Badges:** These occupy the highest "z-index" but have no blur. They use a solid 2px "ink" border and a sharp, offset shadow (4px 4px) to look like they are physically stuck onto the glass.

## Shapes

The shape language is "Organic Geometric." While the base containers are standard rounded rectangles, specific interactive elements should feel more hand-crafted.

- **Primary Containers:** 1rem (16px) corner radius.
- **Buttons & Input Fields:** 0.5rem (8px) corner radius for a sturdy feel.
- **Stickers/Badges:** Use a mix of "Pill-shaped" and custom "Wavy" or "Starburst" SVG masks for achievement badges.
- **Stroke Style:** Where borders are used (cards, inputs), apply a subtle "roughness" or "hand-drawn" SVG filter to mimic ink on paper, avoiding perfectly straight vector lines.

## Components

### Buttons
- **Primary:** "Mint Glow" background, black text. On hover, the button scales up by 5% (`scale: 1.05`) and the ambient glow increases in intensity.
- **Ghost:** Transparent with a 2px "Ink" border. Hover state fills the button with a 10% Mint tint.

### Cards & Notes
- Use the "The Page" elevation style.
- Headers within cards should be underlined with a "marker-style" stroke in the secondary color.
- **AI Cards:** Feature a rotating "sparkle" icon in the top-right and a subtle Electric Purple gradient border.

### Chips & Stickers
- **Category Chips:** Pill-shaped, low-contrast glass.
- **Achievement Stickers:** High-contrast, bright colors (Sunset Orange), slightly rotated (2-3 degrees) to look hand-placed.

### Input Fields
- Underline-style inputs are preferred for notes (mimicking ruled paper), while boxed glassmorphic inputs are used for system settings.
- Focus state: The underline or border glows in Mint Green.

### Lists
- Use custom "check-mark" icons that look like hand-drawn "X"s or circles for a more personal journal feel.
- Bullet points are replaced with "ink dots" of varying sizes.