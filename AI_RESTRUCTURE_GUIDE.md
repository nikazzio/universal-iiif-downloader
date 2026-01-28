# Universal IIIF Remodel Procedure for an AI

## Context

- The repository currently mounts at `/home/niki/work/personal/universal-iiif-downloader` and mixes two distinct UI stacks: legacy Streamlit code under `app.py` + `iiif_downloader/ui/...` and the new FastHTML/Mirador experience under `studio_ui/...`.
- Core business logic lives inside `iiif_downloader/ocr`, `iiif_downloader/storage`, and `iiif_downloader/resolvers`, and must remain untouched except where UI integration calls them.
- The goal is to strip Streamlit entirely, reorganize the UI sources for clarity, and rename the main project directory to `Universal IIIF` so future automation sees the new branding.

## Step-by-step instructions

1. **Verify working directory**
   - Run `pwd` and `git status -sb` to confirm the current repository root.
   - All commands should later operate inside this repository before the rename occurs.

2. **Catalog Streamlit references**
   - Run `rg -n "streamlit"` from the repo root to list every file importing Streamlit or its ecosystem packages.
   - Note items like `requirements.txt`, `README.md`, `app.py`, and anything under `iiif_downloader/ui/` that references Streamlit (components, styling helpers, sidebar widgets, etc.).

3. **Remove Streamlit dependencies and code**
   - Delete `app.py` and the entire `iiif_downloader/ui/` subtree; they should no longer reside in the project.
   - Remove any Streamlit-related packages (`streamlit`, `streamlit-ace`, `streamlit-antd-components`, `streamlit-cropper`) from `requirements.txt`, `requirements-dev.txt`, and any other dependency manifest.
   - Update documentation (`README.md`, `AGENTS.md`, `CHANGELOG.md`, etc.) to remove instructions that reference Streamlit commands and to highlight FastHTML as the only UI.

4. **Reorganize the FastHTML UI layout**
   - Introduce a clearer folder hierarchy for the FastHTML stack; e.g., move `studio_ui/pages/`, `components/`, and `routes/` into a top-level `studio_ui/` or `web_interface/` module if needed.
   - Create shared helper modules (e.g., `studio_ui/common.js` or `components/common.py`) for repeated logic like toasts, HTMX wiring, and Mirador configuration.
   - Ensure `app_fasthtml.py` remains the single entry point and that `config.json`/`config.example.json` document the FastHTML settings.

5. **Rename the repository root folder**
   - From one level above the repo, run `mv universal-iiif-downloader "Universal IIIF"` to rename the directory to the new title.
   - After renaming, `cd` into `/home/niki/work/personal/Universal IIIF` to continue work; update any scripts or config that expect the old path.
   - Confirm `git status -sb` still works (Git follows renaming if executed from inside the renamed folder).

6. **Update references to the new name**
   - Search for the old name (`universal-iiif-downloader`) in files and replace with `Universal IIIF` where appropriate (README, documentation, etc.).
   - Ensure build/test scripts or documentation mention the new root name.

7. **Validate and document**
   - Run `pip install -r requirements.txt` (after removing Streamlit deps) and execute any existing tests (`pytest`, `pyright`, etc.) to ensure nothing else references the removed files.
   - Summarize changes in a new `docs/REORG.md` or similar file so future contributors understand the layout and naming.

8. **Final checks**
   - Rerun `rg -n "streamlit"` to confirm no references remain.
   - Check `git status` to ensure only the expected files are staged/modified.
   - Commit the restructure with a message like `chore: remove streamlit and rename repo to Universal IIIF` if auto-commit is part of the workflow.

## Notes for the AI

- Preserve all FastHTML-related logic; only reorganize it for clarity.
- If a rename or move will break a running process (e.g., CI configuration pointing to the old path), update references accordingly.
- When in doubt about whether a Streamlit file is still needed, double-check whether its functionality exists elsewhere in the FastHTML UI before deleting.
