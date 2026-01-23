# Repository Guidelines

## Project Structure & Module Organization
- `app.py` boots the Streamlit studio; `main.py` exposes CLI workflows. The reusable logic lives inside the `iiif_downloader` package (storage, OCR helpers, download orchestration) and the `models/`, `data/`, and `logs/` folders store generated binaries, the SQLite vault, and runtime traces.
- `assets/` and `downloads/` capture user-created snippets and manuscripts; they are mutable data directories excluded from version control. Use `temp_images/` for transient processing artifacts.
- Static docs and architecture notes live in `docs/`, while `tests/` mirrors the module layout with `test_*.py` files covering core behaviors. Keep new modules grouped logically under `iiif_downloader/` and update `docs/ARCHITECTURE.md` when you add major flows.

## Build, Test, and Development Commands
- `pip install -r requirements.txt` (or `pip install -r requirements-dev.txt` for lint/test extras) to recreate the virtual environment dependencies.
- `streamlit run app.py` to launch the studio UI with the full OCR/snippet feature set.
- `python3 main.py "<manifest-id>" --ocr kraken` for CLI-driven downloads and Kraken OCR runs; substitute other providers via `config.json`.
- `python -m pytest tests` executes the unit + integration suite (configured with `tests/test_*.py`).
- `ruff check .` enforces the lint set defined in `pyproject.toml` (double quotes, 4-space indent, Google docstrings, Ruff select list). Run `ruff format .` before committing if you rely on auto-format.

## Coding Style & Naming Conventions
- Python code follows PEP 8 with tiny captions: 4-space indentation, double-quoted strings, Google-style docstrings, and short, descriptive function/class names. Ruff catches naming, complexity, and security issues; run it locally before pushing.
- Keep UI assets in `assets/`, core configuration logic in `iiif_downloader/config.py` (if added), and `tests/` mirrors the naming pattern `test_<module>.py`.

## Testing Guidelines
- The suite runs under `pytest` (min version 6.0, quiet output). Choose `test_<feature>.py` for new files and place helper fixtures in `tests/conftest.py` as needed.
- There is no enforced coverage gate, but cover new download steps, Vault interactions, and Streamlit callbacks.

## Commit & Pull Request Guidelines
- Follow the conventional-style prefix (`feat:`, `fix:`, `chore:`, `docs:`) before a concise summary (see recent history for guidance). Mention the subsystem (`snippets`, `ocr`, etc.) when helpful.
- PRs should include a summary of changes, testing steps (commands run), and links to related issues. Attach screenshots when touching the UI. Ensure `config.json` is regenerated locally if defaults change and avoid committing it.

## Configuration & Environment Notes
- Keep `config.example.json` as the single committed template; copy it to `config.json` locally (`cp config.example.json config.json`) and update via the Streamlit settings panel to avoid leaking secrets.
- Python 3.10+ is required; prefer virtual environments (`.venv` or `venv`).

## Application Overview
- `app.py` e la UI Streamlit sono la porta principale per l'esperienza studio + snippet + OCR; `main.py` offre la CLI batch con flag `--ocr` per Kraken e i provider configurati in `config.json`.
- Il package `iiif_downloader/` incapsula orchestrazione download (`logic/downloader.py`), resolver specifici (es. `resolvers/vatican.py`), storage persistenza (`storage/vault_manager.py`), helper OCR (`ocr/storage.py`) e componenti UI (`ui/discovery.py`, `ui/search.py`).
- `assets/`, `downloads/`, `temp_images/`, `data/vault.db` e `logs/` conservano rispettivamente snippet, manoscritti salvati, cache temporanea, vault SQLite e tracce runtime. La documentazione chiave vive in `docs/` (vedi `docs/ARCHITECTURE.md` per l'architettura aggiornata).
- `tests/test_*.py` seguono la struttura dei moduli principali e vanno aggiornati quando si tocca la logica di download, snippet o vault.

## Agent Collaboration
- Tu (sviluppatore) descrivi chiaramente cosa vuoi ottenere; l'agente (Codex) esegue comandi shell, modifica file, applica patch e riferisce i risultati seguendo la policy del repository.
- Fornisci priorità (es. bug vs feature) e indica eventuali test/tool desiderati (`python -m pytest`, `ruff check .`, `streamlit run app.py`). L'agente non assume nulla: chiedi conferma prima di operazioni distruttive.
- Quando servono info contestuali (log, contenuti docs, risultati test) specificali, così l'agente può limitare il recupero a quanto necessario.
- L'agente riporta sempre lo stato finale, suggerisce passi successivi (es. quali test servono) e descrive eventuali limitazioni rilevate.
