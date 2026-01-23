# Repository Guidelines (AI Agents)

## Quick Orientation
- `app.py` boots the Streamlit UI (Studio); `main.py` calls the CLI entrypoint in `iiif_downloader/cli.py`.
- Core logic lives in `iiif_downloader/` (download orchestration, resolvers, OCR, storage, UI pages).
- `docs/ARCHITECTURE.md` describes the module map and flows; update it when you add major new pipelines or UI pages.

## Key Paths (What to Read/Change)
- **CLI**: `iiif_downloader/cli.py` (arg parsing, resolver selection, DB management commands).
- **Download pipeline**: `iiif_downloader/logic/downloader.py` (IIIF fetch, output layout, PDF generation, DB updates).
- **Resolvers**: `iiif_downloader/resolvers/` (`BaseResolver`, `vatican.py`, `gallica.py`, `oxford.py`, `generic.py`, `discovery.py`).
- **OCR**: `iiif_downloader/ocr/` (model manager, processor, storage helpers).
- **UI**: `iiif_downloader/ui/` and `iiif_downloader/ui/pages/` (Studio, Export Studio, Discovery, Search).
- **Storage**: `iiif_downloader/storage/vault_manager.py` (SQLite for manuscripts + snippets).

## Runtime Data & Output Layout (Do Not Commit)
- `downloads/{Library}/{ms_id}/`
  - `scans/` page images (`pag_####.jpg`)
  - `pdf/` exported PDFs
  - `data/` `metadata.json`, `manifest.json`, `image_stats.json`, `transcription.json`
- `data/vault.db` is the SQLite vault (manuscripts + snippets).
- `assets/`, `downloads/`, `models/`, `temp_images/`, `logs/` are mutable user data directories and should stay out of version control.

## Configuration & Secrets (Single Source of Truth)
- Runtime config is **only** `config.json` managed by `iiif_downloader/config_manager.py`.
- `config.json` path priority: `./config.json` if writable, else `~/.universal-iiif-downloader/config.json`.
- **Do not** import `iiif_downloader/config.py` (legacy module intentionally raises an error).
- Keep `config.example.json` as the committed template; never commit `config.json` or secrets.
- Live tests are gated by `settings.testing.run_live_tests=true` inside `config.json`.

## Build, Run, Test
- Install: `pip install -r requirements.txt` (or `requirements-dev.txt` for lint/test).
- UI: `streamlit run app.py`
- CLI: `python3 main.py "<manifest-or-url>" --ocr kraken --create-pdf`
- Tests: `python -m pytest tests`
- Lint/format: `ruff check .` and `ruff format .` (double quotes + Google docstrings enforced).

## Testing Notes
- Some tests require network access (e.g., `tests/test_live.py`, `tests/test_search_apis.py`) and are skipped unless `settings.testing.run_live_tests=true`.
- Oxford search API is deprecated and expected to fail; related tests are retained for documentation.
- Add fixtures under `tests/fixtures/` and document new tests in `tests/README.md`.

## Adding New Features Safely
- **New library resolver**: implement in `iiif_downloader/resolvers/`, add it to `iiif_downloader/cli.py` and any UI discovery lists.
- **New settings**: extend `DEFAULT_CONFIG_JSON` in `iiif_downloader/config_manager.py` and surface it in the Streamlit settings panel.
- **UI changes**: keep state in `iiif_downloader/ui/state.py` or `ui/pages/.../studio_state.py`; update CSS in `ui/styling.py`; attach screenshots in PRs.
- **Storage changes**: update `VaultManager` schema carefully and consider migration behavior (existing DBs are in user data).

## Commit & PR Expectations
- Use conventional prefixes (`feat:`, `fix:`, `docs:`, `chore:`) and mention the subsystem when helpful.
- PRs should include: summary, tests run, related issues, and UI screenshots when applicable.

