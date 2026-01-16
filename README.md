# 📜 Universal IIIF Downloader & Studio (Professional)

Uno strumento **professionale** e modulare per scaricare e studiare manoscritti da qualsiasi biblioteca IIIF (Vaticana, Bodleian, Gallica, ecc.). 
Il sistema organizza automaticamente i download in una libreria strutturata e offre un'interfaccia di studio avanzata.

## 🚀 Funzionalità Principali

- **Architettura Modulare**: Codice pulito e separato (PDF, Storage, UI, OCR).
- **Storage Document-Centric**: Organizzazione automatica in `downloads/<ID_Manoscritto>/`.
- **Interactive Viewer 2.0**: Zoom 400%, Drag-to-Pan e interfaccia moderna.
- **Discovery & Search**: Cerca direttamente nei cataloghi di **Gallica** e **Oxford** o risolvi segnature **Vaticana**.
- **Multi-Engine OCR/HTR**: Integrazione con Claude 3.5, GPT-5, Hugging Face e Kraken.

## 📋 Requisiti

- **Python 3.10+**
- **Poppler**: `sudo apt-get install poppler-utils` (necessario per estrazione PDF)
- **Dipendenze**: `pip install -r requirements.txt`

## 💻 Utilizzo CLI (Command Line)

Lo script `main.py` è il motore principale. Può essere usato in modalità interattiva o con argomenti.

### Esempi di Comandi
```bash
# 1. Download semplice via URL
python3 main.py https://digi.vatlib.it/view/MSS_Urb.lat.1779

# 2. Download via Segnatura (Vaticana)
# Il sistema normalizza automaticamente spazi e maiuscole
python3 main.py "Urb. Lat. 1779"

# 3. Download con Batch OCR (modello TRIDIS su Hugging Face)
python3 main.py [URL] --ocr "magistermilitum/tridis_v2_HTR_historical_manuscripts"

# 4. Modalità Wizard (Interattiva)
# Basta lanciare lo script senza argomenti
python3 main.py
```

### Opzioni Principali
- `-o, --output`: Nome della cartella/PDF (auto-generato se omesso).
- `-w, --workers`: Numero di thread per il download (default: 4).
- `--prefer-images`: Forza il download delle immagini anche se esiste un PDF ufficiale.

## 🖥️ Universal IIIF Studio (Web UI)

L'interfaccia Streamlit per la ricerca, la visualizzazione e la trascrizione:

```bash
streamlit run app.py
```

### Funzioni dello Studio:
- **Scopri e Scarica**: Cerca nei cataloghi Gallica/Oxford o scarica via segnatura.
- **Trascrizione**: Esegui OCR pagina per pagina con i migliori modelli AI.
- **Ricerca Globale**: Cerca parole chiave in tutti i manoscritti già scaricati e trascritti.

## 📁 Struttura della Libreria

Ogni download crea una struttura pulita:
```text
downloads/
└── Urb.lat.1779/
    ├── Urb.lat.1779.pdf    # Il documento finale
    ├── metadata.json       # Metadati IIIF
    └── transcription.json  # Trascrizioni e coordinate OCR
```

---
*Ottimizzato per Digital Humanities e Paleografia.*
