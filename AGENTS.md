# 🤖 Agent Guidelines

**Current Context**: You are working on the **Universal IIIF Downloader & Studio** (FastHTML/HTMX UI + Python core + CLI). The FastHTML experience and CLI packages are the only supported front ends.

## 🧭 Refactor Status (28-01-2026)

Il progetto ha adottato un **Modern Package Layout (SRC Layout)**. La logica è separata tra `core`, `ui` e `cli`, tutti residenti sotto la cartella `src/`.

### ✅ Recent Milestones (Session Resume)

- **Architecture**: Migrazione completata al layout `src/`.
- **Entry Points**: Implementati `iiif-studio` e `iiif-cli` via `pyproject.toml`.
- **Dependency Management**: Centralizzata in `pyproject.toml`. `requirements.txt` ridotto a `-e .`.
- **Linting**: Ruff configurato con vincoli di complessità ciclica (C901).

---

## 🏗️ Project Structure & Rules (MANDATORY)

### 📂 Layout SRC

- **Source Code**: Tutto il codice sorgente deve risiedere in `src/`.
- **Root Clean Policy**: NRoot Clean Policy: Nessun file Python è ammesso nella root. Tutto il codice, inclusi gli entry point dell'applicazione (`studio_app.py`), deve risiedere esclusivamente dentro la cartella `src/`.
- **No Legacy**: Il file `main.py` nella root è eliminato. La CLI vive in `src/universal_iiif_cli/`.

### 📦 Dependency & Config

1. **Dependencies**: Aggiungi nuove librerie SOLO in `pyproject.toml` (`[project.dependencies]`).
2. **Editable Install**: Il progetto si installa con `pip install -e .`.
3. **Static Analysis**: La configurazione Pyright vive **esclusivamente** in `pyrightconfig.json`. Non aggiungere impostazioni di analisi nel file `settings.json` di VS Code.

### 🐍 Coding Standards (Ruff)

- **Ruff** è l'unico linter e formatter ammesso.
- **Complexity (C901)**: Se una funzione supera il valore di complessità **10**, DEVE essere spezzettata in helper functions o classi di servizio. Non negoziare su questo.
- **Pathlib**: Usa sempre `Path` (pathlib) per la gestione dei percorsi.

---

## 🗺️ Orientation

- **CLI Entry Point**: `src/universal_iiif_cli/cli.py` (funzione `main()`).
- **Web Entry Point**: `src/studio_app.py` (funzione `main()`).
- **Core Logic**: `src/universal_iiif_core/`.
- **UI & Routes**: `src/studio_ui/`.

---

## 🚀 Build, Run, Test

- **Install**: `pip install -e .`
- **Run Web UI**: `iiif-studio` (oppure `python studio_app.py`)
- **Run CLI**: `iiif-cli "<manifest-url>"`
- **Test**: `pytest tests/`
- **Lint & Format**: `ruff check . --fix` e `ruff format .`

---

## ⚠️ Critical Constraints

1. **Config Management**: Usa `universal_iiif_core.config_manager`. Non hardcodare mai percorsi.
2. **State Management**: Lo stato della UI fluisce attraverso `studio_ui/ocr_state.py` e gli endpoint HTMX.
3. **Data Directories**: Le cartelle `downloads/`, `data/local/`, `logs/` e `temp_images/` sono user-data e devono restare nel `.gitignore`.

---

## 🧹 User-Data Workflow

- **Cleanup script**: `scripts/clean_user_data.py` usa il `ConfigManager` per individuare `downloads`, `temp_images`, `logs` e (se richiesto) l’intero `data/local`. Esegui `python scripts/clean_user_data.py --dry-run` per valutare l’impatto e aggiungi `--include-data-local` solo quando serve resettare anche modelli e snippet generati.
- **Checklist prima della PR**:
  1. Aggiorna `.gitignore` per includere nuove directory di runtime e registra il path nel `config.json` solo tramite `universal_iiif_core.config_manager`.
  2. Conferma cosa verrebbe rimosso con `python scripts/clean_user_data.py --dry-run`.
  3. Esegui `python scripts/clean_user_data.py --yes` (aggiungi `--include-data-local` se hai toccato config o resolver di storage) e poi `pytest tests/`.
  4. Termina con `ruff check . --select C901` e `ruff format .` per assicurarti che le modifiche rispettino le regole di complessità.
- **Quando pulire**: prima di lanciarе test locali completi, dopo modifiche ai resolver/storage e quando ti servono dati freschi per debugging. Lo script preserva `config.json` e richiede conferma a meno che non passi `--yes`.

## 🚀 GitHub & PR Strategy (MANDATORY)

- **Use GitHub CLI**: Usa sempre `gh` per le operazioni remote.
- **PR Creation**: Esegui `gh pr create --fill` per ogni modifica.
- **Branching**: **Mai committare su `main`**. Crea sempre un feature branch. Nomina i branch seguendo `feat/`, `fix/`, `docs/`, `chore/` + descrizione corta.
- **Conventional Commits**: Usa prefissi `feat:`, `fix:`, `docs:`, `chore:`.
- **PR Readiness**: Prima di aprire un PR, conferma lo stato locale con `gh pr status` e correggi eventuali controlli falliti; usa `gh pr view --web` solo dopo aver rivisto i risultati.

## 📦 Semantic Release

- L'automazione dei rilasci si basa sui commit messaggi. Assicurati che siano descrittivi.
- La versione è centralizzata in `src/universal_iiif_core/__init__.py`.

## 🧑‍💻 Coding Expectations

- **Complexity (C901)**: Ogni funzione o metodo deve restare sotto la soglia 10. Spezzetta in helper chiari con responsabilità singole e testabili se la logica cresce.
- **Code Style**: Usa `pathlib.Path` per i percorsi, evita API legacy (`os.path`, moduli rimossi) a meno che non sia giustificato e approvato. Favorisci funzioni pure e separa effetti collaterali in helper dedicati.
- **Ruff & Tooling**: Esegui `ruff check . --select C901` e `ruff format .` prima di committare; qualsiasi failure di complessità va corretto o giustificato nel PR.
- **Design moderno**: Prediligi tipizzazione esplicita, data classes/`attrs` quando gestisci strutture dati, e `async` solo dove necessario. Fornisci docstring tipo Google/NumPy per API pubbliche.
- **Examples**:
  - Breaking up complex work:
    ```python
    def download_manifest(manifest_url: str) -> DownloadResult:
        manifest = fetch_manifest(manifest_url)
        return handle_download(manifest)

    def handle_download(manifest: Manifest) -> DownloadResult:
        # helper anticipa le eccezioni e tiene il body concentrato
        ...
    ```
  - Evitare funzioni con troppi branch: converte in piccoli step sequenziali chiaramente nominati (e.g. `validate_manifest`, `resolve_storage_path`).
