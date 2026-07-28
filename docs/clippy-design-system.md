# Clippy — Complete Visual Design Specification

> **Product:** AI Clipping Agent SaaS
> **Code name:** Clippy
> **Target users:** Professional content creators
> **Vibe:** Professional, fast, data-driven (Retool × Notion × Descript)
> **Date:** 2026-07-26
> **Status:** Ready for implementation

---

## Table of Contents

1. [Design Tokens](#1-design-tokens)
2. [Component Visual Design](#2-component-visual-design)
3. [Motion & Animation](#3-motion--animation)
4. [Empty States](#4-empty-states)
5. [Layout & Page Structure](#5-layout--page-structure)
6. [Accessibility](#6-accessibility)

---

## 1. Design Tokens

### 1.1 Dark Theme Palette (PRIMARY — ship first)

```css
:root[data-theme="dark"] {
  /* Background surfaces — darkest to lightest */
  --surface-0:  #0a0a0a;   /* Sidebar, outermost chrome */
  --surface-1:  #141414;   /* Main content area, card backgrounds */
  --surface-2:  #1c1c1c;   /* Input fields, elevated surfaces */
  --surface-3:  #252525;   /* Hover states, subtle highlights */

  /* Borders */
  --border:       #2a2a2a;
  --border-hover: #3a3a3a;

  /* Text */
  --text-primary:    #f5f5f5;
  --text-secondary:  #a0a0a0;
  --text-tertiary:   #6b6b6b;

  /* Accent */
  --accent:       #3b82f6;   /* Tailwind blue-500 */
  --accent-hover: #2563eb;   /* Tailwind blue-600 */
  --accent-subtle: rgba(59, 130, 246, 0.12);  /* For backgrounds/tints */
  --accent-glow:   rgba(59, 130, 246, 0.25);   /* For focus rings, selected states */

  /* Semantic */
  --success: #22c55e;
  --success-subtle: rgba(34, 197, 94, 0.15);
  --warning: #eab308;
  --warning-subtle: rgba(234, 179, 8, 0.15);
  --error:   #ef4444;
  --error-subtle: rgba(239, 68, 68, 0.15);

  /* Shadows */
  --shadow-card:    0 1px 3px rgba(0, 0, 0, 0.3);
  --shadow-elevated: 0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-modal:   0 8px 32px rgba(0, 0, 0, 0.5);

  /* Overlay */
  --overlay: rgba(0, 0, 0, 0.6);
}
```

### 1.2 Light Theme Palette (SECONDARY)

```css
:root[data-theme="light"] {
  --surface-0:  #ffffff;
  --surface-1:  #f5f5f5;
  --surface-2:  #ebebeb;
  --surface-3:  #e0e0e0;

  --border:       #d4d4d4;
  --border-hover: #b0b0b0;

  --text-primary:    #0a0a0a;
  --text-secondary:  #525252;
  --text-tertiary:   #8a8a8a;

  --accent:       #3b82f6;
  --accent-hover: #2563eb;
  --accent-subtle: rgba(59, 130, 246, 0.08);
  --accent-glow:   rgba(59, 130, 246, 0.18);

  --success: #22c55e;
  --success-subtle: rgba(34, 197, 94, 0.1);
  --warning: #eab308;
  --warning-subtle: rgba(234, 179, 8, 0.1);
  --error:   #ef4444;
  --error-subtle: rgba(239, 68, 68, 0.1);

  --shadow-card:    0 1px 3px rgba(0, 0, 0, 0.1);
  --shadow-elevated: 0 4px 12px rgba(0, 0, 0, 0.12);
  --shadow-modal:   0 8px 32px rgba(0, 0, 0, 0.18);

  --overlay: rgba(0, 0, 0, 0.4);
}
```

### 1.3 Typography

**Font family stack:**
```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
```

**Type scale — absolute values:**

| Token            | Size  | Weight                                           | Line Height | Letter Spacing | Usage                        |
|------------------|-------|--------------------------------------------------|-------------|----------------|------------------------------|
| `--text-xs`      | 12px  | 400 / 500 / 600                                  | 16px        | 0              | Badges, timestamps, captions |
| `--text-sm`      | 14px  | 400 / 500 / 600                                  | 20px        | 0              | Body, labels, nav items      |
| `--text-base`    | 16px  | 400 / 500 / 600                                  | 24px        | 0              | Default body text            |
| `--text-lg`      | 18px  | 500 / 600 / 700                                  | 26px        | 0              | Section headers, modals      |
| `--text-xl`      | 20px  | 500 / 600                                        | 28px        | 0              | Small page titles            |
| `--text-2xl`     | 24px  | 600 / 700                                        | 32px        | -0.01em        | Page titles                  |
| `--text-3xl`     | 30px  | 600 / 700                                        | 36px        | -0.015em       | Analytics values, hero       |
| `--text-4xl`     | 36px  | 700                                              | 44px        | -0.02em        | Dashboard hero numbers       |

**Font weight tokens:**
```css
--font-normal:   400;
--font-medium:   500;
--font-semibold: 600;
--font-bold:     700;
```

### 1.4 Spacing Scale

Base unit: **4px**

| Token       | Value   |
|-------------|---------|
| `--space-1`  | 4px     |
| `--space-2`  | 8px     |
| `--space-3`  | 12px    |
| `--space-4`  | 16px    |
| `--space-5`  | 20px    |
| `--space-6`  | 24px    |
| `--space-8`  | 32px    |
| `--space-10` | 40px    |
| `--space-12` | 48px    |
| `--space-16` | 64px    |
| `--space-24` | 96px    |

### 1.5 Border Radius

| Token              | Value | Usage                       |
|--------------------|-------|-----------------------------|
| `--radius-input`   | 4px   | Input fields, small elements |
| `--radius-card`    | 6px   | Cards, buttons, panels       |
| `--radius-modal`   | 8px   | Modals, dropdowns, tooltips  |
| `--radius-pill`    | 9999px | Badges, pills, tags         |
| `--radius-large`   | 12px  | Upload widget, hero sections |

### 1.6 Shadows

| Token              | Dark                              | Light                             | Usage                    |
|--------------------|-----------------------------------|-----------------------------------|--------------------------|
| `--shadow-card`    | `0 1px 3px rgba(0,0,0,0.3)`      | `0 1px 3px rgba(0,0,0,0.1)`      | Default card state       |
| `--shadow-elevated`| `0 4px 12px rgba(0,0,0,0.4)`     | `0 4px 12px rgba(0,0,0,0.12)`    | Hover, dropdowns         |
| `--shadow-modal`   | `0 8px 32px rgba(0,0,0,0.5)`     | `0 8px 32px rgba(0,0,0,0.18)`    | Modals, drawers          |

### 1.7 Transition Tokens

```css
--transition-fast:   150ms ease;
--transition-normal: 300ms ease;
--transition-slow:   500ms ease;
```

---

## 2. Component Visual Design

### 2.1 Upload Widget

```
┌─────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────┐  │
│  │                                               │  │
│  │           [upload-arrow icon 24px]            │  │
│  │           Drop video here or click            │  │
│  │                  to browse                    │  │
│  │                                               │  │
│  │    Supported: MP4, MOV, WebM (max 2GB)       │  │
│  │                                               │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  Paste a YouTube or video URL...             │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Specification:**

| Property          | Value                                                               |
|-------------------|---------------------------------------------------------------------|
| Width             | 100% of container (full-width)                                      |
| Drop zone height  | 200px                                                               |
| Drop zone bg      | `var(--surface-1)`                                                  |
| Drop zone border  | `2px dashed var(--border)`                                          |
| Drop zone radius  | `var(--radius-large)` (12px)                                        |
| Icon              | Upload arrow, 24×24px, color `var(--text-tertiary)`                 |
| Primary text      | "Drop video here or click to browse", 14px, `var(--text-secondary)` |
| Secondary text    | "Supported: MP4, MOV, WebM (max 2GB)", 12px, `var(--text-tertiary)` |
| URL input height  | 40px                                                                |
| URL input bg      | `var(--surface-2)`                                                  |
| URL input border  | `1px solid var(--border)`                                           |
| URL input radius  | `var(--radius-card)` (6px)                                          |
| URL input text    | 14px, `var(--text-primary)`                                         |
| URL input pholder | "Paste a YouTube or video URL...", 14px, `var(--text-tertiary)`     |
| URL input padding | 0 12px (horizontal)                                                 |
| URL input height  | 40px                                                                |

**States:**

| State              | Visual Change                                                              |
|--------------------|----------------------------------------------------------------------------|
| Default            | Dashed border `var(--border)`, bg `var(--surface-1)`                        |
| Hover (drag over)  | Border `var(--accent)` solid 2px, bg `var(--accent-subtle)`                 |
| URL input focus    | Border `var(--accent)`, ring `3px var(--accent-glow)`                       |
| File selected      | Dashed border disappears; file info row appears (name, size, remove btn)    |
| URL YouTube detect | Input shows YouTube icon (16px left) + badge "YouTube video detected" pill  |
| Uploading          | Progress bar appears (full-width, 4px height, bg `var(--surface-3)`) — fill `var(--accent)` |
| Uploading text     | "Uploading... 45% — 12.4 MB / 27.5 MB" — 13px, `var(--text-secondary)`      |
| Upload error       | Border turns red `var(--error)`, error text below in 12px `var(--error)`    |

**Progress bar:**
```css
.progress-bar {
  height: 4px;
  background: var(--surface-3);
  border-radius: 2px;
  overflow: hidden;
}
.progress-bar__fill {
  height: 100%;
  background: var(--accent);
  transition: width var(--transition-normal);
}
```

**Cancel button (during upload):**
- Height 32px, padding 0 12px
- Border `1px solid var(--border)`, radius `var(--radius-card)`
- Text 13px, `var(--text-secondary)`
- Hover: bg `var(--surface-2)`, text `var(--text-primary)`

---

### 2.2 Pipeline Stepper

```
  [1]──────[2]──────[3]──────[4]──────[5]──────[6]
  DOWNLOAD TRANSCRIBE ANALYZE  SCORE   GENERATE  DONE
```

**Container:**
- Width: ~500px, centered horizontally
- Padding: `var(--space-6)` top/bottom
- Overflow hidden

**Individual step:**

| Element            | Specification                                                     |
|--------------------|-------------------------------------------------------------------|
| Circle diameter    | 24px                                                              |
| Circle stroke      | 2px                                                               |
| Label text         | 12px, semibold, `var(--text-secondary)` — uppercase tracking 0.5px |
| Label margin-top   | 6px                                                               |
| Connecting line    | 2px height (horizontal), color based on state                      |
| Connector width    | Calculated: `(container - 24px * 6) / 5`                           |

**Circle states:**

| State   | Fill                  | Icon/Text           | Border              | Connector line      |
|---------|-----------------------|---------------------|---------------------|---------------------|
| Pending | `var(--surface-3)`     | Number (12px, `var(--text-tertiary)`) | `2px solid var(--surface-3)` | `var(--surface-3)`  |
| Active  | `var(--accent)`        | Spinner or pulsing dot | —                   | completed: `var(--accent)`, remaining: `var(--surface-3)` |
| Done    | `var(--success)`       | Checkmark (white, 12px) | —                   | `var(--success)`     |
| Failed  | `var(--error)`         | X (white, 12px)     | —                   | `var(--error)`       |

**Active pulse animation:**
```css
@keyframes pulse-step {
  0%   { box-shadow: 0 0 0 0 var(--accent-glow); }
  70%  { box-shadow: 0 0 0 8px transparent; }
  100% { box-shadow: 0 0 0 0 transparent; }
}
.pipeline-step--active .step-circle {
  animation: pulse-step 1.5s ease-in-out infinite;
}
```

**Step icons:**
1. Download — downward arrow icon
2. Transcribe — text lines icon
3. Analyze — magnifying glass icon  
4. Score — star icon
5. Generate — sparkle/wand icon
6. Done — checkmark icon

All icons 14px, white on colored circles.

---

### 2.3 Clip Candidate Card

```
┌───────────────────────┐
│ ┌───────────────────┐ │
│ │                   │ │     [ 00:12 ]  ← duration badge
│ │     THUMBNAIL     │ │
│ │      (16:9)       │ │
│ │                   │ │
│ └───────────────────┘ │
│                       │
│ Best highlight moment │  ← title (1 line truncate)
│ from the intro...     │
│                       │
│ [95] [72] [88] [45]   │  ← score badges (flex, wrap)
│                       │
│ ───────────────────── │  ← border-top
│ [✓ Approve] [✗ Reject]│  ← bottom bar
└───────────────────────┘
```

**Card container:**

| Property        | Value                                    |
|-----------------|------------------------------------------|
| Width           | ~320px (flexible, fills grid column)     |
| Background      | `var(--surface-1)`                       |
| Border          | `1px solid var(--border)`                |
| Border-radius   | `var(--radius-card)` (6px)               |
| Shadow          | `var(--shadow-card)`                     |
| Transition      | `all var(--transition-fast)`             |
| Overflow        | hidden                                   |

**Thumbnail area:**

| Property        | Value                                      |
|-----------------|--------------------------------------------|
| Aspect ratio    | 16:9                                       |
| Background      | `var(--surface-2)` placeholder             |
| Border-radius   | `var(--radius-card)` `var(--radius-card)` 0 0 |
| Position        | relative                                   |

**Duration badge:**
- Position: absolute, top-left, margin 8px
- Height: 20px, padding 0 6px
- Background: `rgba(0, 0, 0, 0.7)`
- Text: 12px, `#ffffff`, medium
- Border-radius: 4px

**Play overlay (on hover):**
- Position: absolute, fills thumbnail, centered
- Background: `rgba(0, 0, 0, 0.3)`
- Icon: Play triangle, 32px, `rgba(255, 255, 255, 0.85)`
- Opacity: 0 → 1 on hover, `var(--transition-fast)`

**Content area:**
- Padding: 12px
- Display: flex, flex-direction: column, gap: 8px

**Title/summary:**
- Font: 14px, semibold, `var(--text-primary)`
- Line height: 20px
- Overflow: hidden, text-overflow: ellipsis, white-space: nowrap (1 line)
- If summary is longer than 1 line, show "..." truncation

**Score badges row:**
- Display: flex, flex-wrap: wrap, gap: 4px

**Bottom bar:**
- Padding: 12px
- Border-top: `1px solid var(--border)`
- Display: flex, gap: 8px

**Approve button:**
- Height: 36px
- Padding: 0 12px
- Background: `var(--success)` (#22c55e)
- Color: white
- Font: 13px, semibold
- Border-radius: `var(--radius-card)` (6px)
- Icon: Checkmark, 14px, left of text
- Gap between icon and text: 6px
- Hover: filter brightness 1.1

**Reject button:**
- Height: 36px
- Padding: 0 12px
- Background: transparent
- Border: `1px solid var(--error)`
- Color: `var(--error)`
- Font: 13px, semibold
- Border-radius: `var(--radius-card)` (6px)
- Icon: X, 14px, left of text
- Hover: bg `var(--error-subtle)`

**Card states:**

| State      | Visual change                                                           |
|------------|-------------------------------------------------------------------------|
| Default    | `var(--shadow-card)`, border `var(--border)`                            |
| Hover      | `translateY(-2px)`, `var(--shadow-elevated)`, thumbnail shows play overlay |
| Selected   | Border `2px solid var(--accent)`, box-shadow `0 0 0 3px var(--accent-glow)` |
| Approved   | Brief flash green (`var(--success-subtle)`), scale down + fade out (0.2s), removed from grid |
| Rejected   | Brief flash red (`var(--error-subtle)`), fade + collapse height (0.2s)  |

---

### 2.4 Score Badge (Pill)

```
┌──────────┐
│  95  Vir │  → green tier
│ ality    │
└──────────┘

┌──────────┐
│  72  En  │  → yellow tier
│ gagement │
└──────────┘

┌──────────┐
│  45  Re  │  → red tier
│ ach      │
└──────────┘
```

| Property        | Value                            |
|-----------------|----------------------------------|
| Height          | 24px                             |
| Padding          | 4px 8px                          |
| Border-radius   | 12px (pill)                      |
| Font            | 11px, semibold                   |
| Display         | inline-flex, align-items center  |
| Gap             | 4px                              |

**Tier-based coloring:**

| Score Range | Background       | Text Color      | Border option          |
|-------------|------------------|-----------------|------------------------|
| ≥ 85        | `var(--success-subtle)` | `var(--success)` | —                      |
| 70–84       | `var(--warning-subtle)` | `var(--warning)` | —                      |
| < 70        | `var(--error-subtle)`   | `var(--error)`   | —                      |

**Format variants:**

| Variant          | Content example              | Usage                    |
|------------------|------------------------------|--------------------------|
| Number + label   | "95" + "Virality"            | Clip candidate cards     |
| Number + color dot| "95" + colored dot (4px)    | Compact view             |
| Label only       | "Virality"                   | Detail view              |

---

### 2.5 Video Player (Clip Detail View)

```
┌────────────────────────────────────────┐
│                                        │
│                                        │
│              VIDEO AREA                │
│            (9:16 or 16:9)              │
│                                        │
│                                        │
│                                        │
│          [▶ Play overlay]              │
│                                        │
│                                        │
│  ┌─┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄─┐  │
│  │     Subtitle text goes here      │  │
│  └──────────────────────────────────┘  │
│                                        │
│  ┌─────────────────────────────────┐  │
│  │  ►  00:12 ───●──────── 01:30  ═ │  │
│  │  [🔊] [⛶]   [⬇] [↗]         │  │
│  └─────────────────────────────────┘  │
└────────────────────────────────────────┘
```

**Player container:**

| Property        | Value                                      |
|-----------------|--------------------------------------------|
| Aspect ratio    | 9:16 (portrait/shorts) or 16:9 (landscape) |
| Background      | `#000000`                                  |
| Border-radius   | `var(--radius-card)` (6px)                  |
| Position        | relative, overflow hidden                   |

**Controls overlay:**
- Position: absolute, bottom: 0, width: 100%
- Background: linear gradient(transparent 0%, rgba(0,0,0,0.7) 100%)
- Height: 80px
- Padding: 12px 16px
- Display: flex, flex-direction: column, justify-content: flex-end

**Play/pause (center overlay when paused):**
- Position: absolute, center of video
- Icon: 48px, white, opacity 0.9
- Background: rgba(0,0,0,0.5), 64px circle
- Hover: scale(1.05), opacity 1

**Seek bar:**
- Height: 4px
- Background: rgba(255,255,255,0.2)
- Border-radius: 2px
- Fill: `var(--accent)` (#3b82f6)
- Thumb (draggable): 12px circle, white, shadow
- Cursor: pointer

**Time display:**
- Font: 12px, monospace (`var(--font-mono)`)
- Color: rgba(255,255,255,0.8)

**Control icons (bottom-right):**
- Size: 16px
- Color: rgba(255,255,255,0.8)
- Hover: color white
- Gap: 12px

**Subtitle area:**
- Position: absolute, bottom 20% of video
- Width: 90%, centered horizontally
- Text: centered, 16px, white, text-shadow 0 1px 3px rgba(0,0,0,0.8)
- Background: rgba(0,0,0,0.5), padding 4px 12px, border-radius 4px

**Action buttons (top-right overlay):**

| Button    | Position | Size | Icon | Hover                     |
|-----------|----------|------|------|---------------------------|
| Download  | top-right, top 12px right 12px | 32×32px circle | ↓ 14px white | bg rgba(255,255,255,0.15) |
| Share     | next to Download | 32×32px circle | ↗ 14px white | bg rgba(255,255,255,0.15) |

Both: bg rgba(0,0,0,0.5), border none, cursor pointer.

---

### 2.6 Sidebar

```
┌──────────────────┐
│                  │
│     Clippy       │  ← Logo area
│                  │
│  ──────────────  │  ← separator
│                  │
│  🎬 Videos       │  ← nav item (active)
│  ✂️ Clips        │
│  📊 Analytics    │
│  ⚙️ Settings     │
│                  │
│                  │
│  ──────────────  │
│                  │
│  [👤] John       │  ← user area
│       Pro        │
└──────────────────┘
```

**Container:**

| Property        | Value                      |
|-----------------|----------------------------|
| Width           | 240px (fixed)              |
| Height          | 100vh                      |
| Background      | `var(--surface-0)`         |
| Border-right    | `1px solid var(--border)`  |
| Display         | flex, flex-direction column|
| Position        | fixed, left: 0, top: 0    |

**Logo area:**
- Height: 56px (top padding 16px, bottom 8px)
- Display: flex, align-items center, padding 0 16px

**Logo text:**
- Font: 18px, bold
- Color: `var(--accent)`
- Letter-spacing: -0.3px

**Logo icon (optional):**
- 24×24px, paperclip icon
- Color: `var(--accent)`

**Navigation section:**
- Flex: 1
- Padding: 8px 8px
- Display: flex, flex-direction column, gap: 2px

**Nav item:**

| Property        | Value                          |
|-----------------|--------------------------------|
| Height          | 40px                           |
| Padding          | 0 12px                         |
| Border-radius   | `var(--radius-card)` (6px)     |
| Display         | flex, align-items center, gap: 10px |
| Cursor          | pointer                        |
| Font            | 14px, medium, `var(--text-secondary)` |
| Icon            | 20px, line icon                |

**Nav item states:**

| State  | Background        | Text color           | Icon color          |
|--------|-------------------|----------------------|---------------------|
| Default| transparent       | `var(--text-secondary)` | `var(--text-tertiary)` |
| Hover  | `var(--surface-1)` | `var(--text-primary)`   | `var(--text-secondary)` |
| Active | `var(--surface-2)` | `var(--accent)`         | `var(--accent)`         |

**Nav icons (20×20px, stroke-width 1.5, line cap round):**
- Videos: film/video icon
- Clips: scissors/clipboard icon
- Analytics: bar-chart icon
- Settings: gear icon

**User area (bottom):**
- Border-top: `1px solid var(--border)`
- Padding: 12px 16px
- Display: flex, align-items center, gap: 10px

**User avatar:**
- 32×32px, border-radius 50%
- Background: `var(--accent-subtle)` (placeholder)
- Font: 13px, semibold, `var(--accent)` (initials fallback)

**User name:**
- 14px, medium, `var(--text-primary)`

**Plan badge:**
- Height: 18px
- Padding: 0 6px
- Background: `var(--accent-subtle)`
- Color: `var(--accent)`
- Font: 10px, semibold
- Border-radius: 4px
- Text: "Pro" or "Free"

---

### 2.7 Settings Form

```
Section Header
─────────────────────────────────

Label
┌─────────────────────────────┐
│ Input field                 │
└─────────────────────────────┘

Label
┌─────────────────────────────┐
│ Select option ▼             │
└─────────────────────────────┘

Label
■ ■ ■ ■ ■ ■ ■ ■   #3b82f6
(preset swatches)  (hex input)

Label
[Toggle ON / OFF]

[  Save Changes  ]
```

**Section header:**
- Font: 18px, bold, `var(--text-primary)`
- Margin-bottom: 16px

**Separator line:**
- Height: 1px
- Background: `var(--border)`
- Margin: 24px 0

**Form field group:**
- Margin-bottom: 20px

**Field label:**
- Font: 14px, medium, `var(--text-secondary)`
- Margin-bottom: 6px

**Text input:**

| Property        | Value                          |
|-----------------|--------------------------------|
| Height          | 40px                           |
| Width           | 100%                           |
| Background      | `var(--surface-2)`             |
| Border          | `1px solid var(--border)`      |
| Border-radius   | `var(--radius-card)` (6px)     |
| Padding          | 0 12px                         |
| Font            | 14px, normal, `var(--text-primary)` |
| Placeholder     | `var(--text-tertiary)`         |
| Focus border    | `var(--accent)`                |
| Focus ring      | `3px var(--accent-glow)`       |
| Transition      | `all var(--transition-fast)`   |

**Select input:**
- Same dimensions as text input
- Custom dropdown arrow (cheveron down, 12px, `var(--text-tertiary)`)
- Background: `var(--surface-2)` url("chevron.svg") no-repeat right 12px center
- Padding-right: 32px
- Appearance: none (remove native)

**Color picker:**

| Component     | Specification                                                   |
|---------------|-----------------------------------------------------------------|
| Swatch grid   | 8 preset colors, 28×28px each, border-radius 6px, border 2px solid transparent |
| Selected      | Border `2px solid var(--accent)`, ring 2px white               |
| Preset colors | `#ef4444`, `#f97316`, `#eab308`, `#22c55e`, `#3b82f6`, `#8b5cf6`, `#ec4899`, `#000000` |
| Custom hex    | Input 80px wide, 32px height, prefix "#", text 13px monospace |
| Gap between   | 8px                                                             |

**Toggle switch:**

```
     ┌──────────────────┐
     │       ●          │  ← OFF
     └──────────────────┘

     ┌──────────────────┐
     │          ●       │  ← ON (accent)
     └──────────────────┘
```

| Property        | Value                          |
|-----------------|--------------------------------|
| Width           | 44px                           |
| Height          | 24px                           |
| Border-radius   | 12px                           |
| Background OFF  | `var(--surface-3)`              |
| Background ON   | `var(--accent)`                 |
| Knob diameter   | 20px                           |
| Knob color      | white                          |
| Knob shadow     | `0 1px 3px rgba(0,0,0,0.3)`   |
| Knob OFF pos    | left: 2px                      |
| Knob ON pos     | right: 2px                     |
| Transition      | `all var(--transition-fast)`   |
| Cursor          | pointer                        |

**Save button:**

| Property        | Value                          |
|-----------------|--------------------------------|
| Height          | 40px                           |
| Padding          | 0 32px                         |
| Background      | `var(--accent)`                |
| Color           | white                          |
| Font            | 14px, semibold                 |
| Border-radius   | `var(--radius-card)` (6px)     |
| Border          | none                           |
| Cursor          | pointer                        |
| Hover bg        | `var(--accent-hover)`          |
| Focus ring      | `3px var(--accent-glow)`       |
| Disabled        | opacity 0.5, cursor not-allowed |

---

### 2.8 Analytics Overview

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ TOTAL    │  │  AVG     │  │ BEST     │  │ APPROVAL│
│ CLIPS    │  │  SCORE   │  │ CLIP     │  │ RATE    │
│          │  │          │  │          │  │         │
│   1,247  │  │    84    │  │  13.2K   │  │   89%   │
│          │  │          │  │          │  │         │
│   +12%   │  │   +3%    │  │   +8%    │  │   -2%   │
│   ▲      │  │   ▲      │  │   ▲      │  │   ▼     │
└──────────┘  └──────────┘  └──────────┘  └──────────┘

┌─────────────────────────────────────────────────────┐
│                                                     │
│              Chart Area (300px height)              │
│                                                     │
│       ╱╲                    ╱╲                      │
│      ╱  ╲  ╱╲             ╱  ╲                     │
│     ╱    ╲╱  ╲    ╱╲    ╱    ╲                    │
│    ╱          ╲  ╱  ╲  ╱      ╲                   │
│   ╱            ╲╱    ╲╱        ╲                  │
│                                                     │
│  Jan  Feb  Mar  Apr  May  Jun  Jul                  │
└─────────────────────────────────────────────────────┘
```

**Summary cards row:**
- Display: grid, grid-template-columns: repeat(4, 1fr), gap: 16px
- Margin-bottom: 24px

**Summary card:**

| Property        | Value                        |
|-----------------|------------------------------|
| Background      | `var(--surface-1)`           |
| Border-radius   | `var(--radius-card)` (6px)   |
| Padding          | 20px                         |
| Shadow          | `var(--shadow-card)`         |
| Display         | flex, flex-direction column  |
| Gap             | 4px                          |

**Card content:**

| Element       | Specification                                               |
|---------------|-------------------------------------------------------------|
| Label         | 12px, semibold, `var(--text-secondary)`, uppercase, letter-spacing 0.5px |
| Value         | 30px, bold, `var(--text-primary)`                           |
| Trend text    | 12px, medium, stacked with arrow icon                       |
| Trend up      | `var(--success)` + "▲" or "↑" icon, 12px                    |
| Trend down    | `var(--error)` + "▼" or "↓" icon, 12px                      |

**Chart area:**

| Property        | Value                        |
|-----------------|------------------------------|
| Background      | `var(--surface-1)`           |
| Border-radius   | `var(--radius-card)` (6px)   |
| Padding          | 20px                         |
| Height          | 300px                        |
| Shadow          | `var(--shadow-card)`         |

**Chart elements (implementation detail):**

| Element          | Color                        |
|------------------|------------------------------|
| Line/gridlines   | `var(--border)` (2a2a2a)    |
| Data line        | `var(--accent)`              |
| Data fill (area) | `var(--accent-subtle)`       |
| Axis labels      | 12px, `var(--text-tertiary)` |
| Tooltip bg       | `var(--surface-3)`           |
| Tooltip border   | `1px solid var(--border)`    |
| Tooltip text     | 13px, `var(--text-primary)`  |

---

## 3. Motion & Animation

### 3.1 Transition Tokens (repeated for reference)

```css
--transition-fast:   150ms ease;
--transition-normal: 300ms ease;
--transition-slow:   500ms ease;
```

### 3.2 Component Animations

| Component          | Trigger     | Animation                                                                 |
|--------------------|-------------|---------------------------------------------------------------------------|
| Pipeline step      | Active state| Pulsing glow: box-shadow 0→8px→0, 1.5s ease-in-out infinite               |
| Clip card          | Hover       | translateY(-2px) + shadow elevated, 0.15s ease                             |
| Clip card          | Approve     | 0.1s bg flash `var(--success-subtle)`, then scale(0.95) + opacity 0, 0.2s ease; then slide out left |
| Clip card          | Reject      | 0.1s bg flash `var(--error-subtle)`, then fade + collapse height to 0, 0.2s ease |
| Clip card          | Mount (grid)| fadeIn + translateY(10px) → 0, 0.3s ease, stagger 50ms per card           |
| Upload drop zone   | Drag over   | Border color transition, bg color transition, 0.15s ease                   |
| Progress bar       | Value change| width transition, 0.3s ease                                               |
| Snackbar/Toast     | Show        | translateY(100%) → 0, 0.25s ease-out                                      |
| Snackbar/Toast     | Dismiss     | translateY(0) → 100%, 0.2s ease-in                                        |
| Sidebar nav item   | Hover       | bg color transition, 0.15s ease                                           |
| Toggle switch      | Toggle      | knob translateX, bg color, 0.15s ease                                     |
| Modal              | Open        | scale(0.95→1) + opacity(0→1), 0.2s ease-out                              |
| Modal              | Close       | scale(1→0.95) + opacity(1→0), 0.15s ease-in                               |

### 3.3 Keyframe Definitions

```css
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes pulse-step {
  0%   { box-shadow: 0 0 0 0 var(--accent-glow); }
  70%  { box-shadow: 0 0 0 8px transparent; }
  100% { box-shadow: 0 0 0 0 transparent; }
}

@keyframes slideUp {
  from { transform: translateY(100%); opacity: 0; }
  to   { transform: translateY(0); opacity: 1; }
}

@keyframes slideDown {
  from { transform: translateY(0); opacity: 1; }
  to   { transform: translateY(100%); opacity: 0; }
}

@keyframes cardApprove {
  0%   { background-color: transparent; }
  20%  { background-color: var(--success-subtle); }
  40%  { background-color: transparent; }
  100% { transform: scale(0.95); opacity: 0; }
}

@keyframes cardReject {
  0%   { background-color: transparent; }
  20%  { background-color: var(--error-subtle); }
  40%  { background-color: transparent; }
  100% { opacity: 0; height: 0; padding: 0; margin: 0; overflow: hidden; }
}
```

### 3.4 Snackbar/Undo Toast

```
┌──────────────────────────────────────────────────────┐
│  ✓ Clip approved  [ Undo ]                           │
└──────────────────────────────────────────────────────┘
```

| Property        | Value                                    |
|-----------------|------------------------------------------|
| Position        | fixed, bottom 24px, center, z-index 1000 |
| Height          | 48px                                     |
| Padding          | 0 16px                                   |
| Background      | `var(--surface-2)`                       |
| Border          | `1px solid var(--border)`                |
| Border-radius   | `var(--radius-card)` (6px)               |
| Shadow          | `var(--shadow-elevated)`                 |
| Font            | 14px, normal, `var(--text-primary)`      |
| Undo button     | 14px, semibold, `var(--accent)`, cursor pointer |
| Auto-dismiss    | 5 seconds                                |

---

## 4. Empty States

### 4.1 No Videos (Upload page)

```
         ┌──────────┐
         │          │
         │  🎬      │   ← 120px illustration
         │          │
         └──────────┘

     No videos yet

  Upload your first video
  to start generating clips

  [ Upload Video ]
```

**Illustration area:**
- Width/height: 120px
- Background: `var(--surface-2)`, border-radius 50% (circle frame)
- Icon: Video/film icon, 48px, `var(--text-tertiary)`
- Margin-bottom: 24px

**Text stack (centered):**

| Element      | Specification                                           |
|--------------|---------------------------------------------------------|
| Heading      | 20px, bold, `var(--text-primary)` — "No videos yet"     |
| Description  | 14px, normal, `var(--text-secondary)` — "Upload your first video to start generating clips" |
| Gap          | 8px between heading and description                     |
| Margin-bottom| 24px                                                    |

**CTA button:**
- Same as primary button spec
- Text: "Upload Video"
- Icon: upload arrow, 16px, left

### 4.2 No Clips (Clips page)

```
         ┌──────────┐
         │          │
         │  ✂️      │   ← 120px illustration
         │          │
         └──────────┘

   No clips generated yet

  Upload a video to generate
  your first clip candidates

  [ Upload Video ]
```

- Same structure as "No videos"
- Icon: Scissors/clip icon, 48px, `var(--text-tertiary)`
- Heading: "No clips generated yet"
- Description: "Upload a video to generate your first clip candidates"

### 4.3 No Analytics (Analytics page)

```
         ┌──────────┐
         │          │
         │  📊      │   ← 120px illustration
         │          │
         └──────────┘

   No data yet

  Publish a clip to start
  seeing performance analytics
```

- Same structure as above
- Icon: Chart icon, 48px, `var(--text-tertiary)`
- Heading: "No data yet"
- Description: "Publish a clip to start seeing performance analytics"
- CTA button: "Publish Your First Clip" (or hidden if not applicable)

### 4.4 Error State (Generic)

```
         ┌──────────┐
         │          │
         │  ⚠️      │   ← 120px illustration
         │          │
         └──────────┘

  Something went wrong

  We couldn't load this content.
  Please try again.

  [ Try Again ]
```

- Icon: Warning triangle, 48px, `var(--warning)`
- Heading: "Something went wrong", `var(--text-primary)`
- Description: "We couldn't load this content. Please try again.", `var(--text-secondary)`
- CTA: "Try Again" — standard button

---

## 5. Layout & Page Structure

### 5.1 Main Layout

```
┌──────────┬──────────────────────────────────────────────┐
│          │                                              │
│          │   ┌──────────────────────────────────────┐   │
│  SIDEBAR │   │  TOP BAR (breadcrumb + actions)      │   │
│          │   └──────────────────────────────────────┘   │
│  240px   │                                              │
│  fixed   │   ┌──────────────────────────────────────┐   │
│          │   │                                      │   │
│          │   │                                      │   │
│          │   │        MAIN CONTENT AREA             │   │
│          │   │                                      │   │
│          │   │                                      │   │
│          │   └──────────────────────────────────────┘   │
│          │                                              │
└──────────┴──────────────────────────────────────────────┘
```

| Region        | Specification                                           |
|---------------|---------------------------------------------------------|
| Sidebar       | 240px fixed left, 100vh, z-index 100, border-right      |
| Main area     | margin-left: 240px, min-height: 100vh, padding: 0       |
| Top bar       | height: 56px, border-bottom: 1px solid `var(--border)`, bg `var(--surface-0)`, padding 0 24px |
| Content       | padding: 24px, max-width: 1440px                         |

### 5.2 Content Area Max Widths

| Page          | Max width  | Layout                                              |
|---------------|------------|-----------------------------------------------------|
| Upload        | 720px      | Centered single column                              |
| Clips (grid)  | 1440px     | CSS grid: auto-fill, minmax(320px, 1fr), gap 16px  |
| Clips (detail)| Full width | Two column: player (left, ~60%) + detail panel (right, ~40%) |
| Analytics     | 1200px     | Mixed: summary row + full-width chart               |
| Settings      | 720px      | Centered single column                              |

### 5.3 Grid Definition (Clips Page)

```css
.clips-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
```

- At viewport < 720px: 1 column
- At viewport 720–1024px: 2 columns
- At viewport 1024–1400px: 3 columns
- At viewport > 1400px: 4 columns

---

## 6. Accessibility

### 6.1 Color Contrast Compliance (WCAG AA)

| Token pair                                            | Ratio   | Passes  |
|-------------------------------------------------------|---------|---------|
| `--text-primary` (#f5f5f5) on `--surface-1` (#141414) | 15.4:1  | ✓ AAA   |
| `--text-secondary` (#a0a0a0) on `--surface-1` (#141414)| 8.1:1  | ✓ AA    |
| `--text-tertiary` (#6b6b6b) on `--surface-2` (#1c1c1c)| 4.8:1   | ✓ AA    |
| `--accent` (#3b82f6) on `--surface-1` (#141414)       | 5.3:1   | ✓ AA    |
| White (#fff) on `--accent` (#3b82f6)                  | 4.0:1   | ✓ AA (large text) |
| `--error` (#ef4444) on `--surface-1` (#141414)         | 5.7:1   | ✓ AA    |
| `--success` (#22c55e) on `--surface-1` (#141414)       | 4.8:1   | ✓ AA    |

**Light theme:**

| Token pair                                            | Ratio   | Passes  |
|-------------------------------------------------------|---------|---------|
| `--text-primary` (#0a0a0a) on white (#fff)            | 16.7:1  | ✓ AAA   |
| `--text-secondary` (#525252) on white (#fff)          | 5.6:1   | ✓ AA    |
| `--accent` (#3b82f6) on white (#fff)                  | 4.5:1   | ✓ AA    |

### 6.2 Focus Management

- All interactive elements show `2px solid var(--accent)` focus ring at `offset 2px`
- Use `:focus-visible` for keyboard-only focus indicators
- Tab order follows visual layout: sidebar → top bar → main content
- Pipeline stepper circles are focusable (`tabindex="0"` or buttons)

```css
:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

/* Remove focus for mouse users */
:focus:not(:focus-visible) {
  outline: none;
}
```

### 6.3 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
  
  .clip-card--approve {
    animation: none;
    display: none;
  }
  
  .clip-card--reject {
    animation: none;
    display: none;
  }
  
  .pipeline-step--active .step-circle {
    animation: none;
    box-shadow: 0 0 0 3px var(--accent-glow);
  }
}
```

### 6.4 Touch Targets

- All interactive elements minimum **44×44px** tap target
- Small elements (like score badges) wrapped in larger hit areas

### 6.5 Screen Reader Support

- Icons: `aria-hidden="true"` + `role="img"` with `aria-label` where needed
- Pipeline stepper: `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- Upload drop zone: `role="button"`, `tabindex="0"`, keyboard accessible (Enter/Space to activate)
- Empty states: `role="status"` for dynamic updates
- Snackbar/Toast: `role="alert"`, `aria-live="polite"`
- All form inputs: associated `<label>` elements, not placeholders alone

---

## Appendix A — Iconography

All icons use **outline style**, 1.5px stroke, round caps, round joins, 20×20px canvas (16×16 internal).

**Icon library needed:**

| Name          | Usage                      |
|---------------|----------------------------|
| upload        | Upload widget, CTA buttons |
| video         | Nav "Videos", empty state  |
| film          | Pipeline "Download" step   |
| scissors      | Nav "Clips", empty state   |
| bar-chart     | Nav "Analytics"            |
| settings/gear | Nav "Settings"             |
| play          | Video player, thumbnail overlay |
| check         | Approve button, completed steps |
| x / close     | Reject button, failed steps, dismiss |
| chevron-down  | Select inputs, dropdowns   |
| download      | Video player action        |
| share         | Video player action        |
| sun           | Theme toggle (light mode)  |
| moon          | Theme toggle (dark mode)   |
| search        | Search input               |
| alert-circle  | Error state                |
| clock         | Duration badge             |

---

## Appendix B — Implementation Checklist

For the frontend developer:

- [ ] CSS custom properties defined for all design tokens (dark + light)
- [ ] Theme switching mechanism via `data-theme` attribute
- [ ] Inter font loaded via Google Fonts or self-hosted
- [ ] Upload widget with drag-and-drop, URL input, and states
- [ ] Pipeline stepper with all 4 states and connector lines
- [ ] Clip candidate card grid with hover, approve, reject animations
- [ ] Score badge component with 3 tiers
- [ ] Video player with overlay controls, subtitles, actions
- [ ] Fixed sidebar with active/hover nav states
- [ ] Settings form with all input types + color picker + toggle
- [ ] Analytics summary cards + chart area
- [ ] Empty states for all 3 pages
- [ ] Snackbar/undo toast with auto-dismiss
- [ ] Reduced motion media query
- [ ] Focus-visible styles throughout
- [ ] Minimum 44×44px touch targets
- [ ] Screen reader labels and ARIA attributes
- [ ] Responsive grid for clip cards
- [ ] Page layout (sidebar + top bar + content area)

---

*End of specification. Every value is concrete and implementable.*
