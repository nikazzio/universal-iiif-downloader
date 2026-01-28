# 🤖 Agent Guidelines

**Current Context**: You are working on the **Universal IIIF Downloader & Studio** (FastHTML/HTMX UI + Python core; Streamlit is being retired).

## 🧭 Refactor Status (27-01-2026)

FastHTML UI refactor is mid-flight. The Studio UI is now FastHTML/HTMX based and the Streamlit UI is being phased out. Keep the left/right layout, tab system, and OCR async flow stable while continuing to clean up legacy code.

### ✅ Recent Milestones (Session Resume)

- **FastHTML UI**: Studio layout finalized (55/45 split), tabs, floating toasts, SimpleMDE styling, history diff cards, Visual filters for Mirador.
- **Mirador**: Minimal UI with deep zoom; page-change events wired to update Studio panels.
- **OCR**: Async worker with timeouts + debug logging, updated 2026 model list.
- **Persistence**: History refresh trigger and toast stack are unified across routes/partials.
- **Navigation**: Sidebar is collapsible with state persisted via `localStorage`.

### 🧯 Strict Rules During Refactor

- **Zero iniziativa**: do not add features or tasks not explicitly requested.
- **No legacy**: if a component changes, refactor cleanly and remove old code paths.
- **UI/Core separation**: keep UI in `studio_ui/`, logic in `iiif_downloader/`.

## 🗺️ Orientation

* **Fast Context**: Read `repomix-output.xml` (if available) for a packed, AI-ready representation of the entire codebase and structure.
- **Architecture**: Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) FIRST. It is the source of truth for module structure.
- **User Guide**: Read [docs/DOCUMENTAZIONE.md](docs/DOCUMENTAZIONE.md) for feature workflows.
- **Setup**: [README.md](README.md) contains installation steps.

## ⚠️ Critical Constraints

1. **Config**: NEVER hardcode API keys or paths. Use `iiif_downloader.config_manager`.
    - Runtime config is `config.json` (git-ignored).
    - Template is `config.example.json`.
2. **State Management**:
    - UI State -> `st.session_state` (managed via `studio_state.py`).
    - Persistent Data -> `VaultManager` (SQLite) or JSON files in `downloads/`.
3. **Path Safety**: Always use `Path` objects (pathlib). Relative paths should be resolved vs project root.

## 🧪 Testing & Validation

* Run tests: `pytest tests/`
- **Note**: Some tests requiring live network (Vatican/Gallica) may be skipped by default unless configured.
- **Visual Verify**: When touching UI, request screenshots or check `app_fasthtml.py` runs without errors.

## 📂 Key Directories (Quick Reference)

* `iiif_downloader/logic/`: Download engine (threading, tiling).
- `studio_ui/pages/`: Studio layout orchestration and tab composition.
- `iiif_downloader/resolvers/`: Library adapters.
- `iiif_downloader/storage/`: Database logic (`vault_manager.py`).

## 🔄 Common Tasks

* **New Library**: Add resolver in `resolvers/`, list in `discovery.py`.
- **New Tool**: Add widgets under `studio_ui/components/`, route handling in `studio_ui/routes/`, shared helpers in `studio_ui/common/`.

## 🚀 GitHub & PR Strategy (MANDATORY)

- **Use GitHub CLI**: Always use `gh` for remote operations.
- **Push & PR**: To publish changes, run `gh pr create --fill`. This command handles the upload via HTTPS/Token and creates the PR automatically.
- **Sync**: Use `gh repo sync` to pull changes if `git pull` fails.

## 🌿 Branching Rule (MANDATORY)

- **Never commit on `main`/`master`**. Always create a feature branch and open a PR.

# Repository Guidelines (AI Agents)

## Quick Orientation

- `app_fasthtml.py` boots the FastHTML UI; `main.py` calls the CLI entrypoint in `iiif_downloader/cli.py`.
- Core logic lives in `iiif_downloader/` (download orchestration, resolvers, OCR, storage, UI pages) while the presentation layer sits in `studio_ui/`.
- `docs/ARCHITECTURE.md` describes the module map and flows; update it when you add major new pipelines or UI pages.

## Key Paths (What to Read/Change)

- **CLI**: `iiif_downloader/cli.py` (arg parsing, resolver selection, DB management commands).
- **Download pipeline**: `iiif_downloader/logic/downloader.py` (IIIF fetch, output layout, PDF generation, DB updates).
- **Resolvers**: `iiif_downloader/resolvers/` (`BaseResolver`, `vatican.py`, `gallica.py`, `oxford.py`, `generic.py`, `discovery.py`).
- **OCR**: `iiif_downloader/ocr/` (model manager, processor, storage helpers).
- **UI**: `studio_ui/` (layout, components, routes, shared FastHTML helpers).
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
- UI: `python app_fasthtml.py`
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
- **UI changes**: keep state and components under `studio_ui/`; attach screenshots in PRs for sizeable visual changes.
- **Storage changes**: update `VaultManager` schema carefully and consider migration behavior (existing DBs are in user data).

## Commit & PR Expectations

- Use conventional prefixes (`feat:`, `fix:`, `docs:`, `chore:`) and mention the subsystem when helpful.
- PRs should include: summary, tests run, related issues, and UI screenshots when applicable.

## 📦 Semantic Release (Automation)

- Release automation runs on pushes to `main` and requires **Conventional Commits** (or squash-merge with a conventional title).
- Manual fallback (local): `semantic-release version` then `semantic-release publish`.
