---
name: Atlas Learning System
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#c7c4d7'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#908fa0'
  outline-variant: '#464554'
  surface-tint: '#c0c1ff'
  primary: '#c0c1ff'
  on-primary: '#1000a9'
  primary-container: '#8083ff'
  on-primary-container: '#0d0096'
  inverse-primary: '#494bd6'
  secondary: '#4cd7f6'
  on-secondary: '#003640'
  secondary-container: '#03b5d3'
  on-secondary-container: '#00424e'
  tertiary: '#4edea3'
  on-tertiary: '#003824'
  tertiary-container: '#00885d'
  on-tertiary-container: '#000703'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e1e0ff'
  primary-fixed-dim: '#c0c1ff'
  on-primary-fixed: '#07006c'
  on-primary-fixed-variant: '#2f2ebe'
  secondary-fixed: '#acedff'
  secondary-fixed-dim: '#4cd7f6'
  on-secondary-fixed: '#001f26'
  on-secondary-fixed-variant: '#004e5c'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  stats-mono:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.05em
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base-unit: 4px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
  container-max: 1280px
---

## Brand & Style

The design system is engineered to evoke a sense of **Structured Intelligence**. It targets lifelong learners, developers, and professionals who require a high-signal, low-noise environment to master complex subjects. The brand personality is **Technical yet Empowering**, positioning the AI not just as a tool, but as a sophisticated navigator through the vast landscape of knowledge.

The visual style follows a **Modern Glassmorphic** aesthetic. It utilizes semi-transparent layers to create a sense of depth and interconnectedness, mirroring the way disparate concepts link together in a learning path. The interface is characterized by precision, utilizing thin 1px borders, subtle glow effects, and a highly organized "bento-box" layout that partitions information into digestible, high-contrast modules.

## Colors

This design system utilizes a deep, sophisticated dark palette to prioritize focus and reduce eye strain during long study sessions.

- **Primary (Deep Indigo):** Used for main actions, brand presence, and primary navigation states. It represents the depth of the knowledge base.
- **Secondary (Electric Cyan):** Used for AI-generated suggestions, active learning nodes, and technical highlights. It provides the "tech" pulse of the UI.
- **Success (Emerald):** Reserved exclusively for completion states, unlocked milestones, and progress indicators.
- **Neutral/Background:** A multi-layered slate/navy approach. The base is near-black (`#020617`), while surfaces use a slightly lighter slate to create hierarchy.

## Typography

The typography system balances human-centric readability with technical precision. 

- **Inter** is the workhorse font, used for all instructional text and interface labels to ensure clarity. 
- **JetBrains Mono** is utilized for metadata, progress percentages, time estimates, and code snippets. This distinction helps users instantly differentiate between "content" and "system data."

Headlines should use tighter letter spacing and heavier weights to feel "architectural," while body text maintains standard spacing for maximum legibility against the dark background.

## Layout & Spacing

The layout follows a **Fluid Bento-Box** model. Content is organized into distinct, card-based modules that reflow based on screen size.

- **Grid:** A 12-column grid is used for desktop, 6-column for tablet, and a single-column stack for mobile.
- **Rhythm:** All spacing (padding, margins, gaps) must be a multiple of the 4px base unit. 
- **Skill Tree Layout:** The learning path generator uses a vertical or radial node-link diagram. Gaps between nodes should be 48px to allow for connector lines to be clearly visible.
- **Safe Areas:** Maintain a 24px inner padding within all glassmorphic cards to ensure text does not crowd the borders.

## Elevation & Depth

This design system avoids traditional drop shadows in favor of **Luminous Depth**.

- **Z-Index 1 (Base):** The dark navy background.
- **Z-Index 2 (Cards):** Semi-transparent glassmorphism. Apply a `backdrop-filter: blur(12px)` and a `1px` solid border using `border_subtle`.
- **Z-Index 3 (Active/Pop-over):** Increased transparency and a subtle outer glow (0px 0px 15px) using the `secondary_color_hex` at 20% opacity.
- **Connectors:** Lines connecting skill nodes should be 2px thick with a 0.4 opacity, glowing only when the path is "Active."

## Shapes

The shape language is **Precise and Technical**. 

- Use **Soft (0.25rem)** corners for smaller elements like tags and inputs.
- Use **Large (0.5rem - 0.75rem)** corners for the main glassmorphic containers. 
- **Nodes:** Learning nodes in the tree are circles (fully rounded) to differentiate them from the structural rectangular UI.
- **Progress Bars:** Should have fully rounded (pill-shaped) caps for a modern feel.

## Components

### Buttons
- **Primary:** Solid `primary_color_hex` with white text. High-contrast.
- **Secondary:** Ghost style. `border_subtle` with `secondary_color_hex` text.
- **Success:** Solid `tertiary_color_hex`. Used for "Mark as Complete" or "Download Certificate."

### Skill Tree Nodes
- **Locked:** Greyscale, 40% opacity, dashed border.
- **Unlocked:** White border, solid background at 10% opacity.
- **Active:** `secondary_color_hex` border with a matching 10px outer glow. 
- **Completed:** `tertiary_color_hex` background with a checkmark icon.

### Cards
All cards must use the glassmorphism effect:
- Background: `rgba(30, 41, 59, 0.7)`
- Blur: `12px`
- Border: `1px solid rgba(255, 255, 255, 0.1)`

### Input Fields
Darker than the card background to create an "inset" feel. Use `jetbrainsMono` for user input to maintain the technical aesthetic. Focus state should highlight the border in `secondary_color_hex`.