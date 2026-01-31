# 🏗️ Project Architecture

## Overview

Universal IIIF Downloader & Studio separates a **FastHTML/htmx-based UI shell** (`studio_ui/`) from the pure Python core (`universal_iiif_core/`). The UI renders HTML elements, wires HTMX for asynchronous swaps, and embeds Mirador, while the back-end keeps all metadata, storage, OCR logic, and network resolution untouchable.

## System Layers

The application is strictly divided into two main layers. The **UI Layer** depends on the **Core Layer**, never the other way around.

### 1. Presentation Layer (`studio_ui/`)

* **Pages**: Layout builders (`studio_layout`, document picker, Mirador wiring).
* **Components**: Reusable UI parts (tab sets, toast holder, SimpleMDE-powered editor, Mirador viewer, snippet cards).
* **Routes**:
  * `studio_handlers.py`: Logic-heavy handlers for the editor, viewer, and OCR operations.
  * `discovery_handlers.py`: Orchestrates search, resolution, and download initiation.
* **Common**: Shared utilities (`build_toast`, htmx triggers, Mirador window presets).

### 2. Core Business Logic (`universal_iiif_core/`)

* **Discovery Module**:
  * **Resolvers**: Uses a Dispatcher pattern (`resolve_shelfmark`) to route inputs to specific implementations (`Vatican`, `Gallica`, `Oxford`).
  * **Search**: Implements SRU parsing (Gallica) and stubs for deprecated APIs.
* **Downloader Logic**:
  * Implements the **Golden Flow** (Native PDF check -> Extraction -> Fallback to IIIF).
  * Manages threading and DB updates.
* **Network Layer (`utils.py`)**:
  * Provides a resilient `requests.Session`.
  * Handles WAF Bypass (Browser User-Agents, Dynamic Brotli).
* **OCR Module**:
  * Abstracts differences between local Kraken models and Cloud APIs (OpenAI/Anthropic).
* **Storage**:
  * `VaultManager`: SQLite interface for metadata and job tracking.

---

## Interactive Flows

### 1. Discovery & Resolution

1. **User Input**: The user enters a shelfmark (e.g., "Urb.lat.1779") or a URL.
2. **Dispatcher**: `resolve_shelfmark` detects the library signature and selects the correct strategy.
3. **Normalization**: The resolver converts "dirty" inputs into a canonical IIIF Manifest URL.
4. **Preview**: The UI fetches basic metadata to display the preview card.

### 2. The Download "Golden Flow"

When a download starts, the background worker strictly follows this decision tree:

1. **Check Native PDF**: Does the manifest provide a download link?
    * **YES**: Download the PDF. Then, **EXTRACT** pages to high-quality JPGs in `scans/` (Critical for Studio compatibility).
    * **NO**: Fallback to downloading IIIF tiles/canvases one by one into `scans/`.
2. **Auto-PDF**: If (and only if) no native PDF was found **AND** `auto_generate_pdf` is true in config, generate a PDF from the images.
3. **Completion**: Update DB status to `completed`.

### 3. Studio & OCR

1. **Async Request**: Clicking "Run OCR" sends an HTMX POST to `/api/run_ocr_async`.
2. **Job State**: The server spawns a thread and tracks progress in `ocr_state.py`.
3. **Polling**: The UI shows an overlay that polls `/api/check_ocr_status` every 2 seconds.
4. **Completion**: Text is saved to `transcription.json` and the History table.

---

## UI & Configuration Details

* **Viewer Config**: The `config.json` (`settings.viewer`) section directly controls Mirador's behavior (Zoom levels) and the Visual Tab's default image filters.
* **State Persistence**:
  * **Server-side**: SQLite (`vault.db`) and JSON files (`data/local/`).
  * **Client-side**: Sidebar state (collapsed/expanded) is saved in `localStorage`.
* **Visual Feedback**:
  * **Toasts**: Floating notifications anchored to the top-right viewport.
  * **Progress**: Real-time progress bars driven by DB polling.

## Key Design Decisions

1. **Scans as Source of Truth**: The `scans/` directory must always contain extracted JPGs. The Viewer, OCR, and Cropper tools rely on these files, regardless of whether the source was a IIIF server or a PDF.
2. **Zero Legacy**: Deprecated APIs are removed or stubbed. No "dead code" is allowed in the codebase.
3. **Network Resilience**: The system assumes library servers are hostile (rate limits, firewalls) and uses aggressive retry logic and header mimicking.
4. **Pure HTTP Front-end**: No heavy client-side frameworks (React/Vue). The UI logic is driven by Python via FastHTML and HTMX.

## Local Data & Cleanup

- Runtime directories (`downloads/`, `data/local/*`, `logs/`, `temp_images/`) vengono risolti attraverso `universal_iiif_core.config_manager` e sono sempre considerati rigenerabili. Non includere asset di configurazione/chiavi in queste cartelle.
- Lo script `scripts/clean_user_data.py` usa il manager per individuare i percorsi e fornisce flag `--dry-run`, `--yes`, `--include-data-local` e `--extra` per ripulire i dati senza mai toccare `config.json`.
- Chi esegue build, test o debugging estesi dovrebbe pulire i dati (passi consigliati: `--dry-run`, quindi `--yes`, `pytest tests/`, `ruff check . --select C901`, `ruff format .`) e documentare ogni nuova directory runtime in `.gitignore`.
