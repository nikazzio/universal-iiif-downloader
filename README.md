# 📜 Universal IIIF Downloader & Studio (v0.7.0)

Uno strumento **professionale** e modulare per scaricare, organizzare e studiare manoscritti digitali.
Combina un **Downloader Resiliente** (capace di aggirare blocchi WAF e assemblare immagini IIIF) con uno **Studio Digitale** basato su Web (FastHTML/HTMX) per l'analisi, la trascrizione assistita da AI e la gestione dei ritagli.

## 📚 Documentazione Ufficiale

- **[Guida Utente](docs/DOCUMENTAZIONE.md)**: Manuale completo su configurazione, utilizzo e funzionalità.
- **[Architettura](docs/ARCHITECTURE.md)**: Dettagli tecnici su Core, UI Layer, Resolvers e Flussi dati.
- **[Changelog](CHANGELOG.md)**: Storico delle versioni e delle modifiche.

> **Nuovo contributor?** Leggi prima `AGENTS.md` per capire coding guideline (Ruff C901), branch naming e la gestione dei dati di runtime.

---

## 🚀 Nuove Funzionalità (v0.7)

### 🛰️ Smart Discovery & "Golden Flow"

Il sistema ora decide autonomamente la strategia migliore per ottenere la massima qualità:

1. **Risoluzione Intelligente**: Incolla una segnatura sporca (es. `Urb. lat. 1779`) o un URL di Gallica/Oxford; il sistema normalizza l'input e trova il Manifest canonico.
2. **Golden Flow**:
   - Se esiste un **PDF Nativo**, lo scarica ed estrae le immagini ad alta risoluzione (HQ JPG) per lo studio.
   - Se non esiste, scarica le **Tile IIIF** e le assembla.
3. **Resilienza**: Il downloader imita un browser reale e gestisce compressioni avanzate (Brotli) per aggirare i blocchi IP delle biblioteche più severe (es. Gallica).

### 🏛️ Studio Digitale (FastHTML)

Un'interfaccia reattiva a pannelli, senza ricaricamenti pagina:

- **Viewer**: Mirador integrato con Deep Zoom configurato per analisi paleografica.
- **Visual Tab**: Filtri in tempo reale (Luminosità, Contrasto, Saturazione, Inversione) applicati via CSS.
- **Editor**: Trascrizione con Markdown, salvataggio con calcolo delle differenze (Diff) e cronologia versionata.
- **OCR Ibrido**: Esegui OCR su singola pagina usando **Kraken** (locale) o API Cloud (**GPT-4o, Claude 3.5, Google Vision**).

---

## 📋 Requisiti

- **Python 3.10+**
- Nessuna dipendenza di sistema complessa (usa librerie pure-python e `PyMuPDF`).

## 🔧 Installazione

```bash
# 1. Clona il repository
git clone [https://github.com/yourusername/universal-iiif.git](https://github.com/yourusername/universal-iiif.git)
cd universal-iiif

# 2. Crea ambiente virtuale
python3 -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# 3. Installa il pacchetto
pip install -e .

```
# (Opzionale) Dipendenze di sviluppo per test/linting
pip install -r requirements-dev.txt
```

### 🧹 Pulizia dei dati locali

- Prima di eseguire test completi o PR su nuovi resolver/storage, esegui `python scripts/clean_user_data.py --dry-run` per verificare cosa viene rimosso.
- Usa `python scripts/clean_user_data.py --yes` per cancellare i percorsi `downloads/`, `data/local/temp_images`, `data/local/logs` e ogni directory aggiuntiva dichiarata tramite `universal_iiif_core.config_manager`; aggiungi `--include-data-local` solo se ti serve rigenerare anche modelli/snippet.
- Se aggiungi nuove cartelle di runtime, aggiornane `.gitignore` e registra il percorso solo passando dalla `ConfigManager`, mai hardcodearle.
- Dopo la pulizia, esegui `pytest tests/`, `ruff check . --select C901` e `ruff format .` per restare allineato alle regole descritte in `AGENTS.md`.
