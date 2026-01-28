# 🏗️ Project Architecture

## Overview

Universal IIIF Downloader & Studio now separates a **FastHTML/htmx-based UI shell** (`fasthtml_ui/`) from the pure Python core (`iiif_downloader/`). The UI renders HTML elements, wires HTMX for asynchronous swaps, and embeds Mirador, while the back-end keeps all metadata, storage and OCR logic untouched.

## Module Structure

```
graph TD
    FastHTML[fasthtml_ui/pages & components] --> StudioRoutes[fasthtml_ui/routes/studio]
    StudioRoutes --> OCR[iiif_downloader/ocr]
    StudioRoutes --> Storage[iiif_downloader/ocr/storage]
    Campus[fasthtml_ui/components/viewer] --> Mirador[Mirador Viewer]
    OCR --> Models[iiif_downloader/ocr/processor]
    Storage --> Vault[VaultManager + SQLite]
```

### fasthtml_ui
- **pages/**: layout builders (`studio_layout`, document picker, Mirador wiring).
- **components/**: tab sets, toast holder, SimpleMDE-powered editor, Mirador viewer, snippet/history cards.
- **routes/studio.py**: HTMX endpoints (`/api/run_ocr_async`, `/api/check_ocr_status`, `/studio/partial/tabs`, `/studio/partial/history`), plus toast helpers and history refresh control.
- **UI Enhancements**: the SimpleMDE initializer injects a lightweight CSS/toolbar theme to keep the markdown controls legible, while `_build_toast` now anchors the floating stack at the viewport top-right with a smooth show/hide choreographed by `requestAnimationFrame`.
- **Viewer config**: the `settings.viewer` section of `config.json` now holds the Mirador/openSeadragon options and the Visual tab defaults/presets so future UI controls can edit them without touching code, and the sidebar is now collapsible with only icons in compact mode (button `☰`, `localStorage` persistence).
- **Mirador zoom**: the viewer configuration feeds `openSeadragonOptions` (higher `maxZoomPixelRatio`, `maxZoomLevel`) so study sessions can zoom deeper into scans without losing the minimized toolbar/thumbnail setup.

### iiif_downloader
- **ocr/**: processor, storage, logger helpers (history snapshots, `compute_text_diff_stats`).
- **storage/**: VaultManager keeps metadata, snippets, and manuscript registry.
- **utils/**: Shared helpers including JSON I/O and the new text diff helper powering colored history badges.

## Interactive Flow
1. **User clicks Run OCR** → HTMX POST to `/api/run_ocr_async` launches worker thread, sets `OCR_JOBS_STATE`, shows overlay + toast container.
2. **HTMX polling**: Overlay polls `/api/check_ocr_status` every 2s; success removes overlay, errors show toast/hx update.
3. **Save/Restore**: `/api/save_transcription` now returns floating toasts plus a hidden `hx-get` trigger that reloads `/studio/partial/history` (optionally carrying an info banner when no change was detected). `/api/restore_transcription` still refreshes the entire right panel and reuses `_build_toast`.
4. **Visual Tab**: introduce a compact controller that writes a `<style>` tag scoped to the current Mirador canvas, so brightness/contrast/saturation/hue/invert filters apply only to the image on screen without touching toolbars, buttons or thumbnails, and the slider values are mirrored in the UI labels.
4. **UI state**: `build_studio_tab_content` centralizes metadata/scans loading so `/studio`, `/studio/partial/tabs`, `/api/check_ocr_status` all reuse consistent tab markup, toast container, and history message pipeline.

## Key Design Decisions
- **Pure HTTP front-end**: No Streamlit sessions; the UI load is served via FastHTML and HTMX-managed partials for responsiveness.
- **Separation of concerns**: `iiif_downloader` remains business/core logic, `fasthtml_ui` handles presentation and htmx orchestration.
- **Resilient UX**: Floating toast container, SimpleMDE styling, and history diffing keep the editing experience predictable even when background OCR jobs overlap.
