# Clippy — AI Clipping Agent: UX Architecture Specification

**Version:** 1.0
**Date:** 2026-07-26
**Target:** V1 Desktop-Only (1280px+)
**Author:** ArchitectUX

---

## Table of Contents

1. [Information Architecture](#1-information-architecture)
2. [Key User Flows](#2-key-user-flows)
3. [Page-Level UX](#3-page-level-ux)
4. [Interaction Patterns](#4-interaction-patterns)
5. [Empty States](#5-empty-states)
6. [Error & Edge Cases](#6-error--edge-cases)
7. [Design System Integration](#7-design-system-integration)
8. [Developer Handoff Notes](#8-developer-handoff-notes)

---

## 1. Information Architecture

### 1.1 Page Tree & Hierarchy

```
Dashboard (/)                    ← Landing page after login
├── Upload                        ← Modal/dedicated page for video submission
│
├── Videos (/videos)              ← List of all uploaded videos
│   └── Video Detail (/videos/:id) ← Pipeline status + clip candidates
│       └── Clip Detail (/clips/:id) ← Player + export for single clip
│
├── Clips (/clips)                ← All approved+exported clips across videos
│
├── Analytics (/analytics)        ← Aggregate performance overview
│
└── Settings (/settings)          ← Subtitle styles, account, preferences
    ├── Subtitle Style Editor
    ├── Account Settings
    └── Notification Preferences
```

### 1.2 Navigation Structure

**Sidebar (persistent, 240px collapsible to 64px icon-only):**

| Icon | Label | Badge |
|------|-------|-------|
| ⌂ | Dashboard | — |
| ▷ | Videos | Count of videos with un-reviewed candidates |
| ✂ | Clips | Count of newly exported clips |
| 📊 | Analytics | — |
| ⚙ | Settings | — |

**Top Bar (64px, spans content area):**

| Left | Center | Right |
|------|--------|-------|
| Logo + product name | Search (videos/clips) | Theme toggle → User avatar + dropdown |

### 1.3 Content Organization Per Page

| Page | Primary Content | Secondary Content | Tertiary |
|------|-----------------|-------------------|----------|
| Dashboard | Upload CTA + recent videos | Pipeline summary widget | Quick stats (clips this week) |
| Videos | Filterable/sortable video table | Bulk actions toolbar | — |
| Video Detail | Pipeline stepper (top) + candidate cards (below) | Video preview panel (right) | Clip count summary badge |
| Clip Detail | Video player with clip region highlighted | Export settings panel | Share link |
| Analytics | Time-series chart (views) | Top clips table | Summary stat cards |
| Settings | Tabbed form sections | Live preview panel (subtitle styles) | — |

---

## 2. Key User Flows

### 2.1 First-Time Upload Flow

```
START: User lands on Dashboard
  │
  1. Dashboard shows empty state → [Upload Your First Video] CTA
  │
  2. Click → Upload modal opens (full-screen backdrop, 640px modal)
  │
  3. Two tabs: [Upload File] | [Paste URL]
  │   ├─ Upload File: Drag-drop zone + file picker button
  │   └─ Paste URL: Text input + [Fetch] button
  │
  4. File selected / URL submitted
  │   ├─ Validation: format check (MP4, MOV, WebM), size check (< 2GB)
  │   ├─ *Error:* invalid format → inline error message
  │   ├─ *Error:* too large → upgrade prompt
  │   └─ *Success:* progress bar appears (upload percentage)
  │
  5. Upload completes → auto-navigate to /videos/:id
  │
  6. Pipeline stepper visible (all steps, first active highlighted):
  │   [1. Uploaded] → [2. Transcoding] → [3. Analyzing] → [4. Clipping] →
  │   [5. Review] → [6. Export Ready]
  │   ● Current step shows spinner + estimated time remaining
  │
  7. Pipeline completes → stepper turns all-green
  │   ● Candidate cards appear below in a responsive grid (3 columns)
  │
  8. User reviews candidates:
  │   ├─ Hover card → inline preview plays (loop, mute)
  │   ├─ Click card → right panel opens with full preview + waveform
  │   ├─ Keyboard: `A` = approve, `R` = reject, `←` / `→` = navigate cards
  │   └─ Bulk: checkbox top-left of each card, select-all in toolbar
  │
  9. User clicks [Approve] on individual card or batch [Approve Selected]
  │   ● Micro-animation: card fills green, checkmark appears, slides to "Approved" section
  │   ● Snackbar: "Clip approved" with [Undo] (5s timer)
  │
  10. User clicks [Export All Approved] button in top toolbar
  │    ● Export settings drawer slides from right:
  │      ├─ Output format: MP4 / MOV
  │      ├─ Resolution: 1080p / 720p
  │      ├─ Subtitle burn-in: On / Off
  │      └─ [Export] CTA
  │
  11. Export queue appears → progress per clip → download links appear
  │
  END: User can download individually or [Download All as ZIP]
```

### 2.2 Returning User Review Flow

```
START: User navigates to /videos
  │
  1. Video table shows: thumbnail, title, duration, upload date, status badge, clip count
  │
  2. Status badge system:
  │   ● Processing (blue) — pipeline in progress
  │   ● Review (amber) — candidates ready for review
  │   ● Complete (green) — all clips approved/exported
  │   ● Failed (red) — pipeline error
  │
  3. Click video row → navigate to /videos/:id
  │
  4. Pipeline stepper shows current state:
  │   ● If processing: same flow as first-time, steps 6-7
  │   ● If review-ready: all steps green, candidate cards visible
  │
  5. Batch toolbar visible:
  │   ├─ [Select All] / [Deselect All]
  │   ├─ [Approve Selected] (n) — n = count selected
  │   └─ [Reject Selected] (n)
  │   ● Disabled when selection is empty
  │   ● Shows count badge when selection > 0
  │
  6. User performs batch approve → snackbar: "5 clips approved" [Undo]
  │
  7. Individual review still available via card click
  │
  8. Export flow same as first-time (step 10-11)
  │
  END: User returns to /videos or navigates to /clips
```

### 2.3 Settings — Subtitle Style Flow

```
START: User navigates to /settings → "Subtitles" tab selected by default
  │
  1. Left panel: Settings form. Right panel: Live preview card
  │
  2. Form fields:
  │   ├─ Font family: Dropdown [Inter, Roboto, Open Sans, Montserrat, etc.]
  │   ├─ Font size: Slider 14px–48px (default 24px)
  │   ├─ Font color: Color picker (preset swatches + custom hex)
  │   ├─ Background color: Color picker + opacity slider (0–100%)
  │   ├─ Background opacity: Slider 0–100% (default 60%)
  │   ├─ Position: Radio [Bottom / Top / Dynamic (avoids faces)]
  │   ├─ Max lines: Radio [1 / 2 / 3]
  │   ├─ Word highlight: Toggle On/Off + color picker
  │   └─ Letter casing: Dropdown [Auto / UPPERCASE / lowercase / Title Case]
  │
  3. Live preview panel updates in real-time as user adjusts:
  │   ● Shows a 15-second sample clip with subtitles rendered
  │   ● Play/pause on the sample
  │
  4. Two CTAs at bottom of form:
  │   ├─ [Save as Default] — applies to all future clips
  │   └─ [Apply to Current] — only visible if accessed from clip export
  │
  5. Save → "Styles saved" snackbar with [Revert] option (10s)
  │
  END: Settings persist across sessions (server-side)
```

---

## 3. Page-Level UX

### 3.1 Dashboard (`/`)

**Layout Zones:**

```
┌──────────────────────────────────────────────────────────┐
│ Top Bar (64px)                                           │
├──────────────┬───────────────────────────────────────────┤
│              │  ┌─────────────────────────────────────┐  │
│              │  │  Welcome Back, {Name}               │  │
│   Sidebar    │  │  ┌─────────────────────────────┐    │  │
│   (240px)    │  │  │ Empty State OR Quick Stats   │    │  │
│              │  │  └─────────────────────────────┘    │  │
│              │  │  ┌─────────────────────────────┐    │  │
│              │  │  │ Recent Videos (horizontal    │    │  │
│              │  │  │ scroll, max 8 cards)         │    │  │
│              │  │  └─────────────────────────────┘    │  │
│              │  │  ┌─────────────────────────────┐    │  │
│              │  │  │ Pipeline Summary Widget      │    │  │
│              │  │  │ (shows in-progress pipelines)│    │  │
│              │  │  └─────────────────────────────┘    │  │
│              │  └─────────────────────────────────────┘  │
└──────────────┴───────────────────────────────────────────┘
```

**States:**

| State | Description | UI |
|-------|-------------|-----|
| **Loading** | Initial data fetch | Full-page skeleton: 2 rectangular skeleton blocks (stats row + video grid), each with shimmer animation. Sidebar and top bar rendered immediately. |
| **Empty** | No videos uploaded | Hero area: Large upload icon (cloud-arrow-up), heading "Upload your first video", subtext "Drop a video file or paste a URL to start generating AI-powered clips", CTA button [Upload Video]. Below: brief feature highlights (3 cards: AI Detection, Auto Subtitles, One-Click Export). |
| **Populated** | Has videos + pipelines | Stats row: 4 stat cards in a row (Total Videos, Clips Generated, Total Views, Avg. Watch Time). Recent Videos: horizontal scroll with card thumbnails, title, duration, status badge. Pipeline Summary: compact list of in-progress pipelines with mini stepper (step name + spinner). |
| **Error** | Data fetch failed | Error banner: "Could not load dashboard" with [Retry] button. Cached data shown below if available, else empty state with retry option. |

**Primary Action:** Upload a new video (hero CTA or sidebar button).

---

### 3.2 Upload (`/upload` — modal overlay)

**Layout Zones:**

```
┌─────────────────────────────────────────────────┐
│  ✕ Close (top-right)                            │
│  ┌───────────────────────────────────────────┐   │
│  │  Upload Video                             │   │
│  │                                           │   │
│  │  [Upload File]  |  [Paste URL]            │   │
│  │                                           │   │
│  │  ┌──────────────────────────────────┐     │   │
│  │  │ Drag & drop zone                 │     │   │
│  │  │ ┌────────────────────────────┐   │     │   │
│  │  │ │ Upload icon                │   │     │   │
│  │  │ │ "Drop video here or"       │   │     │   │
│  │  │ │ [Browse Files]             │   │     │   │
│  │  │ │ Supports MP4, MOV, WebM    │   │     │   │
│  │  │ └────────────────────────────┘   │     │   │
│  │  └──────────────────────────────────┘     │   │
│  │                                           │   │
│  │  ┌──────────────────────────────────┐     │   │
│  │  │ Advanced options (collapsible)   │     │   │
│  │  │ ├─ Language: [Auto-detect ▼]     │     │   │
│  │  │ ├─ Clip length: [15s / 30s / 60s]│     │   │
│  │  │ └─ Max clips: [5 / 10 / 20]     │     │   │
│  │  └──────────────────────────────────┘     │   │
│  │                                           │   │
│  │  [Start Processing] → disabled until      │   │
│  │   file selected or URL validated           │   │
│  └───────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

**States:**

| State | Description | UI |
|-------|-------------|-----|
| **Initial** | Modal opened, no file | Drop zone active (dashed border, subtle pulse). URL tab: empty input with placeholder "https://...". Both tabs show format requirements. |
| **Dragging** | File hovering over drop zone | Drop zone border turns solid brand color, background tints, icon animates. "Drop to upload" text appears. |
| **Uploading** | File transferring | Progress bar (determinate, percentage). File name + size shown. Cancel button (X). ETA text: "3.2 MB of 156 MB — 45 seconds remaining". |
| **Processing** | Upload complete, transcoding | Success checkmark. "Video uploaded! Redirecting to pipeline..." Auto-navigates after 2s. |
| **Error** | Upload failed | Red error banner: "Upload failed: [reason]". Options: [Retry] [Cancel] [Try Different File]. File picker re-opens on retry. |
| **URL Fetch Error** | URL unreachable | Inline error under input: "Could not fetch video from this URL. Check the link and try again." |

**Primary Action:** Submit file/URL and start processing.

---

### 3.3 Video Detail (`/videos/:id`)

**Layout Zones:**

```
┌────────────────────────────────────────────────────────────┐
│ Top Bar (64px) — back arrow + video title                  │
├─────────────┬──────────────────────────────────────────────┤
│             │  Pipeline Stepper (horizontal, full width)    │
│             │  1 → 2 → 3 → 4 → 5 → 6                      │
│             │  ┌────────────────────────────────────────┐   │
│   Sidebar   │  │ Time remaining: ~3 min                 │   │
│   (240px)   │  └────────────────────────────────────────┘   │
│             │                                               │
│   active    │  ┌──────────────────────┬──────────────────┐   │
│   highlight │  │ Candidate Grid       │ Video Preview    │   │
│   on        │  │ (3-column grid)      │ Panel (320px)    │   │
│   "Videos"  │  │                      │                  │   │
│             │  │ ┌─────┐ ┌─────┐ ┌──┐ │ ┌─────────────┐ │   │
│             │  │ │Card │ │Card │ │..│ │ │ Thumbnail   │ │   │
│             │  │ └─────┘ └─────┘ └──┘ │ │ Play button │ │   │
│             │  │                      │ │ Waveform    │ │   │
│             │  │ [Approve] [Reject]   │ │             │ │   │
│             │  │ Bulk toolbar         │ │             │ │   │
│             │  └──────────────────────┴──────────────────┘   │
└─────────────┴────────────────────────────────────────────────┘
```

**Pipeline Stepper — 6 Steps:**

```
[1. Uploaded] ● [2. Transcoding] ● [3. Analyzing] ● [4. Clipping] ● [5. Review] ● [6. Export Ready]

States per step:
  ● Completed — green checkmark, filled circle
  ● Active — brand color, pulsing circle, step label bold
  ● Pending — gray circle, dimmed label
  ● Failed — red X, step label red, error message below
```

**Candidate Card Structure (265px × 340px):**

```
┌─────────────────────┐
│ ┌─────────────────┐ │
│ │ Thumbnail       │ │  ← 16:9 crop, timestamp overlay top-left "01:23 - 01:38"
│ │ (265×149)       │ │  ← Duration badge bottom-right "15s"
│ │                 │ │
│ └─────────────────┘ │
│ □ Select            │  ← Checkbox, top-left corner of card body
│ Clip Title          │  ← Auto-generated: "Best reaction at 01:23"
│                    │
│ ⚡ Virality: 87     │  ← Score bar (0-100), color-coded (green ≥ 70, amber 40-69, red < 40)
│ 👁 2.3K est. views │  ← Estimated performance metric
│                    │
│ [Approve] [Reject]  │  ← Individual action buttons
└─────────────────────┘
```

**States:**

| State | Description | UI |
|-------|-------------|-----|
| **Loading** | Page fetching video data | Full-page skeleton: stepper skeleton (6 gray circles + lines), grid skeleton (6 rectangular cards with shimmer). |
| **Pipeline Active** | Processing in progress | Stepper shows current active step with spinner. "Estimated time remaining: X min" below stepper. Candidate area shows "Analyzing your video..." with animated waveform graphic. No cards visible yet. |
| **Candidates Ready** | Pipeline complete, clips generated | Stepper all green. Candidate grid populated with cards. Toolbar active. Right panel shows first clip preview (auto-select first card). |
| **All Reviewed** | All clips approved or rejected | Progress banner at top: "6/6 clips reviewed. 4 approved, 2 rejected." If any approved → [Export All] CTA prominent. If none approved → "No clips approved. Generate new candidates?" button. |
| **Pipeline Failed** | Error during processing | Step that failed shows red X + error message: "Transcoding failed: [reason]". [Retry Pipeline] button below stepper. Options to [Edit Video] or [Delete] in dropdown. |
| **Zero Candidates** | No clips detected | Stepper all green. Empty state in grid area: "No viral moments detected" with icon, subtext "Try adjusting clip settings or upload a different video". [Regenerate with Different Settings] button. |

**Primary Action:** Review clip candidates, approve/reject, and export.

---

### 3.4 Clip Detail (`/clips/:id`)

**Layout Zones:**

```
┌────────────────────────────────────────────────────────────┐
│ Top Bar (64px) — back arrow + clip title + parent video    │
├─────────────┬──────────────────────────────────────────────┤
│             │  ┌────────────────────────────────────────┐   │
│   Sidebar   │  │ Video Player (16:9, max 960px width)   │   │
│   (240px)   │  │                                        │   │
│             │  │ ● Play/pause, scrubber, volume          │   │
│             │  │ ● Clip region highlighted on timeline   │   │
│             │  │ ● Trim handles at clip boundaries       │   │
│             │  │ ● Subtitle overlay toggle               │   │
│             │  └────────────────────────────────────────┘   │
│   active    │                                               │
│   highlight │  ┌──────────────────────┬──────────────────┐   │
│   on        │  │ Export Settings       │ Clip Metadata    │   │
│   "Clips"   │  │ ├─ Format: [MP4 ▼]   │ ├─ Virality: 87  │   │
│             │  │ ├─ Resolution: [1080] │ ├─ Est. Views    │   │
│             │  │ ├─ Subtitles: [On]    │ ├─ Duration: 15s │   │
│             │  │ ├─ Watermark: [Off]   │ ├─ Source: 01:23 │   │
│             │  │ └─ [Export] button    │ └─ Tags: [... ]  │   │
│             │  └──────────────────────┴──────────────────┘   │
└─────────────┴────────────────────────────────────────────────┘
```

**States:**

| State | Description | UI |
|-------|-------------|-----|
| **Loading** | Fetching clip data | Player skeleton (16:9 gray box with shimmer), settings panel skeleton. |
| **Ready** | Clip loaded | Player ready with poster frame. Controls visible on hover. Export settings populated with defaults from /settings. |
| **Exporting** | Export in progress | Export button shows spinner + "Exporting...". Progress bar below. Remaining clips in queue shown. |
| **Exported** | Export complete | Success state: "Export complete" with download link. [Copy Link] button. Option to [Share] or [Download Again]. |
| **Error** | Clip data failed | Error card: "Could not load clip". [Retry] or [Go Back to Video] options. |

**Primary Action:** Preview, adjust export settings, and export the clip.

---

### 3.5 Analytics (`/analytics`)

**Layout Zones:**

```
┌────────────────────────────────────────────────────────────┐
│ Top Bar (64px) — "Analytics" + date range picker           │
├─────────────┬──────────────────────────────────────────────┤
│             │  ┌────────────────────────────────────────┐   │
│   Sidebar   │  │ Stats Row (4 cards)                    │   │
│   (240px)   │  │ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │   │
│             │  │ │Total │ │Total │ │Avg   │ │Avg   │  │   │
│             │  │ │Views │ │Clips │ │Watch │ │Eng.  │  │   │
│             │  │ │12.4K │ │ 86   │ │Time  │ │Rate  │  │   │
│             │  │ └──────┘ └──────┘ └──────┘ └──────┘  │   │
│   active    │  └────────────────────────────────────────┘   │
│   highlight │                                               │
│   on        │  ┌────────────────────────────────────────┐   │
│   "Analytics│  │ Views Over Time (line chart)            │   │
│   tics"     │  │ X-axis: date | Y-axis: views            │   │
│             │  │ Filter: [7d] [30d] [90d] [All]          │   │
│             │  └────────────────────────────────────────┘   │
│             │                                               │
│             │  ┌────────────────────────────────────────┐   │
│             │  │ Top Performing Clips (table)            │   │
│             │  │ Rank | Thumb | Title | Views | Virality │   │
│             │  │  1  | ...   | ...   | 2.1K |    92     │   │
│             │  │  2  | ...   | ...   | 1.8K |    88     │   │
│             │  └────────────────────────────────────────┘   │
│             │                                               │
│             │  ┌────────────────────────────────────────┐   │
│             │  │ Clip Performance Distribution (bar)     │   │
│             │  │ X-axis: virality buckets | Y-axis: count│   │
│             │  └────────────────────────────────────────┘   │
└─────────────┴──────────────────────────────────────────────┘
```

**States:**

| State | Description | UI |
|-------|-------------|-----|
| **Loading** | Fetching analytics data | Full-page skeleton: stat card skeletons (4 rectangles), chart skeleton (large rectangle with horizontal grid lines), table skeleton (5 rows × 4 columns). |
| **Empty** | No published clips | Stats row shows zeros. Chart area shows empty state: "No data yet — publish your first clips to see analytics." CTA: [Go to Videos]. Table empty: "Your top clips will appear here once published." |
| **Populated** | Data available | All charts and tables populated. Date range picker active. Table rows clickable → navigate to clip detail. |
| **Error** | Analytics API failed | Error banner: "Could not load analytics data." [Retry] button. Previous cached data shown if available. |

**Primary Action:** Review performance metrics and identify top-performing clips.

---

### 3.6 Settings (`/settings`)

**Layout Zones:**

```
┌────────────────────────────────────────────────────────────┐
│ Top Bar (64px) — "Settings"                                │
├─────────────┬──────────────────────────────────────────────┤
│             │  ┌────────────────────────────────────────┐   │
│   Sidebar   │  │ Tab Navigation:                       │   │
│   (240px)   │  │ [Subtitles] [Account] [Notifications] │   │
│             │  ├────────────────────────────────────────┤   │
│             │  │                                        │   │
│   active    │  │ ┌────────────────┐ ┌────────────────┐  │   │
│   highlight │  │ │ Settings Form  │ │ Live Preview   │  │   │
│   on        │  │ │                │ │ Panel (fixed,   │  │   │
│   "Settings"│  │ │ Font: [Inter▼] │ │ 420px)         │  │   │
│             │  │ │ Size: ───●─── │ │                │  │   │
│             │  │ │ Color: [■]    │ │ ▶ Sample clip  │  │   │
│             │  │ │ Bg:           │ │ with subtitles  │  │   │
│             │  │ │ Position: ... │ │ rendered live   │  │   │
│             │  │ │               │ │                │  │   │
│             │  │ │ [Save]        │ │                │  │   │
│             │  │ └────────────────┘ └────────────────┘  │   │
│             │  └────────────────────────────────────────┘   │
└─────────────┴──────────────────────────────────────────────┘
```

**States:**

| State | Description | UI |
|-------|-------------|-----|
| **Loading** | Fetching current settings | Form skeleton (labeled input skeletons + preview skeleton). |
| **Populated** | Settings loaded | Form populated with current values. Preview playing a looped sample clip. |
| **Saving** | Saving changes | Save button shows spinner, form fields disabled. Preview continues playing. |
| **Saved** | Changes persisted | "Settings saved" snackbar with [Revert] option (10s). Button returns to [Save]. |
| **Error** | Save failed | Error state on form: "Could not save settings. [Retry]" Form fields remain editable. |

**Sub-tabs:**

| Tab | Fields |
|-----|--------|
| **Subtitles** | Font family, size, color, background color/opacity, position, max lines, word highlight, casing. Live preview panel. |
| **Account** | Email, display name, avatar upload, plan info (current plan + upgrade CTA), usage stats (videos this month, storage used). |
| **Notifications** | Toggles: Email notifications (clip ready, export complete, weekly digest), in-app notifications (same categories). |

**Primary Action:** Customize subtitle appearance and save as default.

---

## 4. Interaction Patterns

### 4.1 Pipeline Progress Stepper

**Specification:**
- **Position:** Full-width, below top bar, above content area on /videos/:id
- **Height:** 80px (including labels)
- **Layout:** Horizontal flex, centered, 6 steps
- **Step circle:** 32px diameter
- **Connecting line:** 2px thick, spans between circles, animates width on completion
- **States per step:** Pending (gray) → Active (brand, pulsing) → Complete (green checkmark) → Failed (red X)

**Real-time updates:**
- Poll every 5 seconds for pipeline status (or use WebSocket/SSE when available)
- Active step shows animated spinner (rotating circle, 1s cycle)
- Below active step: "Analyzing speech patterns..." (contextual message changes per step)
- Step transitions animate: connecting line fills from left to right over 500ms, circle turns green with scale bounce

**Messages per step:**

| Step | Active Message | Completed Message |
|------|----------------|-------------------|
| 1. Uploaded | — | "Video received" |
| 2. Transcoding | "Converting to analysis format..." | "Format optimized" |
| 3. Analyzing | "Detecting speech, faces, and key moments..." | "Content analyzed" |
| 4. Clipping | "Generating clip candidates..." | "Candidates ready" |
| 5. Review | — | "Awaiting your review" |
| 6. Export Ready | — | "Ready to export" |

### 4.2 Candidate Card Interaction

**Hover (desktop):**
- Card lifts 4px with subtle shadow (transform: translateY(-2px), box-shadow transition, 200ms ease)
- Thumbnail overlay: 3s preview loop plays inline (muted, no controls)
- [Approve] / [Reject] buttons become fully opaque (normally 60% opacity)
- Virality score label expands to show breakdown tooltip

**Click to expand:**
- Card expands to fill a side panel (right side, 420px, slides in)
- Panel contains: larger preview player with audio, waveform visualization, trim handles (fine-tune start/end), full metadata, individual A/R buttons
- Click outside panel or [X] to close
- Panel does NOT close when approving/rejecting — user can batch through cards

**Keyboard shortcuts (when card grid is focused):**
| Key | Action |
|-----|--------|
| `←` / `→` | Navigate between cards |
| `A` | Approve current card |
| `R` | Reject current card |
| `Space` | Play/paste preview |
| `Shift + A` | Approve all visible |
| `Esc` | Close side panel / deselect |

### 4.3 Bulk Select

**Selection model:**
- Checkbox on each card (top-left of card body)
- Select-all checkbox in toolbar above grid
- Indeterminate state when some but not all selected
- Selection persists across scroll (if virtualized grid is used)

**Toolbar behavior:**
- Default: `[Select All]` text link
- When selection > 0: `[Deselect All]` + `[Approve Selected (n)]` + `[Reject Selected (n)]` + count badge "4 selected"
- Actions disabled if selection = 0
- After batch action: toolbar resets, cards removed from view or moved to approved/rejected section

**Visual feedback:**
- Selected cards: 2px brand border, subtle background tint
- Checkbox animates on check (200ms, scale bounce)
- Count badge updates in real-time with counter animation

### 4.4 Approve/Reject Feedback

**Approve animation:**
- Card fills with green background tint (from center, 300ms)
- Checkmark icon appears (scale from 0 to 1, 200ms ease-out)
- Card slides to top section "Approved ({n})" or disappears if filter active
- Counter increments: "Approved: 3" → "Approved: 4"

**Reject animation:**
- Card fills with warm gray background tint (300ms)
- X icon appears (same scale animation)
- Card slides to "Rejected ({n})" section or disappears
- Counter increments

**Snackbar (both actions):**
- Appears bottom-center, 48px above bottom edge
- Text: "Clip approved" / "3 clips approved" / "Clip rejected" / "3 clips rejected"
- Action button: [Undo] — white text, no background
- Auto-dismiss: 5 seconds
- On undo: card returns to original position, state reverts, snackbar dismisses
- Counter decrements on undo

**Stacking:** Multiple approve/reject actions batch into single snackbar: "5 clips approved" (if done rapidly within 2s window)

### 4.5 Video Preview — Side Panel

**Specification:**
- Position: Right side, slides over content (420px fixed width)
- Trigger: Click candidate card
- Close: [X] button top-right, click outside, Esc key
- Content:
  - Video player (16:9, 420x236px)
  - Audio waveform below player (interactive, click to seek)
  - Timestamp range display: "01:23 — 01:38"
  - Trim handles on waveform (adjustable, snap to detected boundaries)
  - Subtitle preview toggle
  - Approve / Reject buttons at bottom
  - Previous / Next arrows to cycle through candidates without closing panel

**Transitions:**
- Slide in: translateX(100%) → translateX(0), 300ms ease-out
- Slide out: reverse, 250ms ease-in
- Content behind dims with overlay (black, 40% opacity, 200ms)

---

## 5. Empty States

### 5.1 No Videos Yet

**Location:** Dashboard `/`

```
┌──────────────────────────────────────────────┐
│                                              │
│          ☁️ (cloud-arrow-up icon, 80px)      │
│                                              │
│          Upload Your First Video              │
│                                              │
│     Drop a video file or paste a URL to       │
│     start generating AI-powered clips.        │
│     We support MP4, MOV, and WebM.            │
│                                              │
│     [Upload Video] — primary CTA              │
│                                              │
│     ┌───────────┐ ┌───────────┐ ┌──────────┐ │
│     │ AI-Powered │ │ Auto      │ │ One-Click│ │
│     │ Detection  │ │ Subtitles │ │ Export   │ │
│     └───────────┘ └───────────┘ └──────────┘ │
│                                              │
└──────────────────────────────────────────────┘
```

### 5.2 No Clips Yet (Video uploaded, pipeline complete)

**Location:** Video Detail `/videos/:id`

```
Pipeline stepper all green (step 5 = "Awaiting your review")

┌──────────────────────────────────────────────┐
│                                              │
│        ✂️ (scissors icon, 64px)              │
│                                              │
│        No Clips Generated Yet                 │
│                                              │
│     Our AI didn't detect any viral moments    │
│     in this video. Try adjusting settings     │
│     or uploading a different video.           │
│                                              │
│     [Regenerate with Different Settings]      │
│     [Upload Another Video]                    │
│                                              │
└──────────────────────────────────────────────┘
```

### 5.3 No Analytics Yet

**Location:** Analytics `/analytics`

```
Stats row all zeros (grayed out)

┌──────────────────────────────────────────────┐
│                                              │
│        📊 (chart icon, 64px)                 │
│                                              │
│        No Analytics Data Yet                  │
│                                              │
│     Publish your first clips to start         │
│     tracking views, engagement, and more.     │
│                                              │
│     [Go to Videos]                            │
│                                              │
└──────────────────────────────────────────────┘
```

### 5.4 Empty Search Results

**Location:** Global search dropdown or /videos filtered

```
┌──────────────────────────────────────────────┐
│                                              │
│        🔍 (search icon, 48px)                │
│                                              │
│        No results for "{query}"              │
│                                              │
│     Try a different search term or browse     │
│     your videos.                              │
│                                              │
│     [Clear Search]                            │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 6. Error & Edge Cases

### 6.1 Video Upload Fails Mid-Way

**Scenario:** Upload reaches 73% then fails due to network drop, server error, or file corruption.

**UX Response:**
- Upload modal stays open, progress bar turns red at 73%
- Error message: "Upload interrupted. Your file was partially uploaded (73%)."
- Three options:
  - [Resume Upload] — attempts to resume from last chunk (if server supports byte-range)
  - [Restart Upload] — starts over from 0%
  - [Cancel] — closes modal, no file retained
- If retry succeeds: progress picks up from last checkpoint, bar continues
- If retry fails twice: "Having trouble uploading. Try a different network or file." with [Try Again] and [Cancel]

**Edge case — file too large (>2GB):**
- Error before upload starts: "Videos over 2GB require our Pro plan. Your file is 3.2GB."
- CTA: [Upgrade to Pro] or [Compress and Try Again]

**Edge case — unsupported format:**
- Inline error on file selection: "We support MP4, MOV, and WebM. Your file is .avi."
- File picker re-opens on [Try Different File]

### 6.2 Pipeline Step Fails

**Scenario:** Transcoding step fails due to codec incompatibility.

**UX Response:**
- Pipeline stepper: Step 2 shows red X, error text below: "Transcoding failed: This video uses an unsupported codec (AV1)."
- Other steps remain gray (not failed)
- Action buttons below stepper:
  - [Retry Pipeline] — primary CTA, restarts from failed step
  - [Upload Different Video] — secondary, navigates back to upload
  - [Contact Support] — opens support ticket form or chat
- On retry: offending step reverts to active (spinner), others stay completed
- If retry fails: "Retry failed. Please upload a different video or contact support."

### 6.3 Candidate Generation Produces 0 Results

**Scenario:** Pipeline completes, AI detects zero viral moments.

**UX Response:**
- Stepper all green, step 5 "Review" shows "0 candidates"
- Empty state (as in 5.2) with specific messaging: "No viral moments detected in this video."
- Reasons (if AI can determine):
  - "The video appears to be a static slideshow with no audio. Try uploading a video with speech or action."
  - "The audio quality may be too low for speech detection. Try a video with clearer audio."
  - "The video is very short (< 30s). Try uploading a longer video."
- Action buttons:
  - [Try Different Settings] → opens advanced options modal (language, clip length, sensitivity)
  - [Upload Another Video]
- Sensitivity slider in advanced options: Low / Medium / High (default Medium). Higher sensitivity generates more candidates but may include lower-quality moments.

### 6.4 Network Disconnection During Review

**Scenario:** User is reviewing candidates, network drops.

**UX Response:**
- Detection: Monitor `navigator.onLine` + periodic health-check pings
- Banner appears at top of content area (below top bar):
  - Icon: Wifi-off
  - Text: "You're offline. Your progress is saved locally."
  - Persistent until connection restored
- All interactive elements remain functional (approve/reject queued locally)
- Queue indicator in toolbar: "3 pending actions (offline)"
- On reconnection:
  - Sync queue fires automatically
  - Success: "All changes synced" snackbar
  - Conflict: "Some changes could not be synced" with [Review Conflicts] option
- If user tries to export while offline:
  - Export button disabled with tooltip: "Connect to the internet to export"

**Edge case — long offline period (>30 min):**
- Warning banner updates: "You've been offline for 30 minutes. Your local changes may expire."
- Session health-check pings
- If session expires: redirect to login with return URL on reconnection

### 6.5 Clip Export Fails

**Scenario:** Export process starts but fails mid-generation.

**UX Response:**
- Export drawer shows error for affected clip: red badge "Export failed"
- Error message: "Export failed: [reason] (e.g., subtitle rendering error)"
- [Retry Export] button on failed clip
- [Export All Failed] if multiple clips failed
- Successful clips in the batch remain exported (download links available)
- If all fail: "All exports failed. Try adjusting export settings." with [Edit Settings] and [Retry All]

### 6.6 Concurrent Session / Tab Conflict

**Scenario:** User opens same video in two tabs, approves clips in one tab.

**UX Response:**
- On action: optimistic update in current tab
- Polling detects state change from server → second tab updates
- If second tab user tries to approve already-approved clip:
  - Inline toast on card: "This clip was already approved in another session"
  - Card state updates to match server
- Conflict resolution: last-write-wins with notification

### 6.7 Rate Limiting

**Scenario:** User uploads 10 videos in rapid succession.

**UX Response:**
- After upload submit: if rate-limited, modal shows:
  - "You've reached the upload limit. Please wait before uploading again."
  - Countdown timer: "Try again in 45 seconds"
  - Queue position: "Your video is queued (#3 in line)"
- Upload progress bar shows queued state (yellow, "Waiting...")

### 6.8 Storage Quota Exceeded

**Scenario:** User's storage is full.

**UX Response:**
- Upload modal: file picker still works, but on submit:
  - Error: "Storage full. You've used 100% of your 10GB storage."
  - CTA: [Upgrade Plan] or [Manage Videos] (navigate to /videos with delete mode)
  - Suggestion: "Delete old videos to free up space"
- Sidebar: storage meter at top shows red bar "Storage full"

---

## 7. Design System Integration

### 7.1 CSS Architecture

The Clippy UI follows the standard ArchitectUX design system. Key implementation files:

```
css/
├── design-system.css    # Variables: colors, typography, spacing
├── layout.css          # App shell: sidebar + top bar + content grid
├── components.css      # All component styles
├── utilities.css       # Helper classes
└── main.css            # Project-specific overrides

js/
├── theme-manager.js     # Light/dark/system theme toggle
├── upload.js           # Upload flow logic
├── pipeline.js         # Pipeline stepper polling + state
├── review.js           # Candidate review interaction (keyboard, bulk, A/R)
├── export.js           # Export flow
└── main.js             # App initialization
```

### 7.2 Design Tokens

```css
:root {
  /* Brand */
  --brand-500: #6366F1;       /* Indigo primary */
  --brand-600: #4F46E5;       /* Hover state */
  --brand-700: #4338CA;       /* Active state */

  /* Semantic */
  --success-500: #22C55E;     /* Approved, complete */
  --warning-500: #F59E0B;     /* Pending, in-progress */
  --error-500: #EF4444;       /* Failed, rejected */

  /* Pipeline */
  --step-complete: var(--success-500);
  --step-active: var(--brand-500);
  --step-pending: #9CA3AF;
  --step-failed: var(--error-500);

  /* Candidate Cards */
  --card-selected-border: var(--brand-500);
  --card-approved-bg: rgba(34, 197, 94, 0.08);
  --card-rejected-bg: rgba(239, 68, 68, 0.06);
  --card-hover-transform: translateY(-2px);
  --card-hover-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
```

### 7.3 Theme Support

All UI states account for both light and dark themes:

| Element | Light | Dark |
|---------|-------|------|
| Page background | `#FFFFFF` | `#0F172A` |
| Surface (cards, panels) | `#F9FAFB` | `#1E293B` |
| Border | `#E5E7EB` | `#334155` |
| Text primary | `#111827` | `#F1F5F9` |
| Text secondary | `#6B7280` | `#94A3B8` |
| Overlay (modal backdrop) | rgba(0,0,0,0.4) | rgba(0,0,0,0.6) |
| Error banner bg | `#FEF2F2` | `#450A0A` |
| Success banner bg | `#F0FDF4` | `#052E16` |

---

## 8. Developer Handoff Notes

### 8.1 Implementation Priority

| Priority | Component | Files | Dependencies |
|----------|-----------|-------|--------------|
| P0 | App shell (sidebar + top bar + layout) | `layout.css`, `main.js` | Design system tokens |
| P0 | Theme toggle | `theme-manager.js` | Design system tokens |
| P0 | Upload modal | `upload.js`, `components.css` | Layout shell |
| P0 | Pipeline stepper | `pipeline.js`, `components.css` | Layout shell |
| P1 | Candidate card grid | `review.js`, `components.css` | Pipeline stepper |
| P1 | Approve/reject flow | `review.js` | Candidate cards |
| P1 | Bulk select toolbar | `review.js` | Candidate cards |
| P1 | Export flow | `export.js` | Review flow |
| P1 | Side panel preview | `review.js`, `components.css` | Candidate cards |
| P1 | Empty states | `components.css` | Layout shell |
| P2 | Analytics page | `main.js` (chart lib) | Layout shell |
| P2 | Settings page | `main.js` | Layout shell |
| P2 | Keyboard shortcuts | `review.js` | Review flow |
| P2 | Snackbar/notification system | `main.js` | — |
| P3 | Search | `main.js` | Layout shell |
| P3 | Trimming in clip detail | `export.js` | Player component |

### 8.2 Component States Checklist

Every component must implement these states before being considered complete:

| Component | Loading | Empty | Error | Populated | Edge |
|-----------|---------|-------|-------|-----------|------|
| Dashboard | ✅ | ✅ | ✅ | ✅ | Upload in progress |
| Upload modal | ✅ | ✅ | ✅ | ✅ (uploading) | File too large, wrong format |
| Pipeline stepper | ✅ | N/A | ✅ | ✅ | Step-specific failure |
| Candidate grid | ✅ | ✅ | N/A | ✅ | 0 candidates |
| Side panel | ✅ | N/A | ✅ | ✅ | Already approved |
| Bulk toolbar | ✅ | N/A | N/A | ✅ | Offline |
| Analytics | ✅ | ✅ | ✅ | ✅ | No data range |
| Settings | ✅ | N/A | ✅ | ✅ | Save conflict |
| Export | ✅ | N/A | ✅ | ✅ (progress) | Batch partial failure |
| Snackbar | N/A | N/A | N/A | ✅ | Stacking, undo expiry |

### 8.3 Responsive Considerations (V2)

While V1 is desktop-only (1280px+), the layout architecture should not prevent future tablet support:

- Sidebar: `width: 240px` with CSS custom property `--sidebar-width` for future toggling
- Content area: `calc(100% - var(--sidebar-width))` — can collapse to 64px
- Grid: `grid-template-columns: repeat(3, 1fr)` — can become `repeat(2, 1fr)` at 1024px
- Cards: `min-width: 265px` with `auto-fit` — naturally collapses

### 8.4 Accessibility Requirements

| Requirement | Implementation |
|-------------|---------------|
| Keyboard navigation | Tab order: sidebar → toolbar → card grid → actions. Arrow keys within grid. |
| Focus indicators | Visible focus ring (2px brand color + 2px offset) on all interactive elements |
| ARIA labels | `role="progressbar"` on stepper, `aria-label` on icon buttons, `role="radiogroup"` on theme toggle |
| Screen reader | Pipeline status announcements via `aria-live="polite"` region. Card state changes announced. |
| Color contrast | All text meets WCAG 2.1 AA (4.5:1 normal, 3:1 large). Status colors not sole differentiator (icons + labels). |
| Motion | `prefers-reduced-motion` respected — animations reduced to fade-only or disabled |

### 8.5 Performance Budgets

| Metric | Target |
|--------|--------|
| Initial page load (JS + CSS) | < 200KB gzipped |
| Time to interactive | < 3s on broadband |
| Pipeline poll interval | 5s (adjustable via server push in future) |
| Candidate grid render | < 500ms for 50 cards |
| Animation frame rate | 60fps (use GPU-accelerated properties: transform, opacity) |
| Image lazy loading | IntersectionObserver for candidate thumbnails |

---

*End of UX Architecture Specification. This document serves as the single source of truth for all V1 UX decisions. Any deviation from this spec during implementation must be reviewed and approved before merging.*
