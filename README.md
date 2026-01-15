# Universal IIIF Downloader

Uno strumento **universale** e modulare per scaricare manoscritti da qualsiasi biblioteca che supporti lo standard IIIF (Vaticana, Bodleian, Gallica, ecc.).

## 🚀 Funzionalità

- **Universalità**: Copia e incolla l'URL di un Manifest IIIF (o di un visualizzatore Vaticano) e lui scarica tutto.
- **Wizard Interattivo**: Se lanci lo script senza argomenti, ti guida passo passo.
- **Download Parallelo & Resume**: Veloce, robusto e capace di riprendere da dove si era interrotto.
- **PDF Nativo (Novità!)**: Se il manoscritto ha già un PDF ufficiale, lo scarica direttamente (molto più veloce).
- **PDF Ottimizzato**: Altrimenti usa `img2pdf` per creare PDF leggeri.
- **Metadati**: Scarica automaticamente le info del manoscritto.

## 📋 Requisiti

- Python 3.7+
- Pip

## 🛠️ Installazione

1. Clona il repository.
2. Crea un virtual environment (consigliato).
3. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Utilizzo

### Modalità "Magica" (Wizard)
Lancia semplicemente:
```bash
python3 main.py
```
Ti chiederà di incollare l'URL e sceglierà il nome migliore per te.

### Modalità Riga di Comando (CLI)

Per utenti esperti o script automatici:

```bash
python3 main.py [URL] [OPZIONI]
```

**Esempio Vaticano:**
```bash
python3 main.py https://digi.vatlib.it/view/MSS_Urb.lat.1779
```

**Esempio Bodleian Library (Oxford):**
```bash
# Con URL del viewer (consigliato)
python3 main.py https://digital.bodleian.ox.ac.uk/objects/080f88f5-7586-4b8a-8064-63ab3495393c/

# Oppure con URL del manifest diretto
python3 main.py https://iiif.bodleian.ox.ac.uk/iiif/manifest/080f88f5-7586-4b8a-8064-63ab3495393c.json
```

**Esempio Gallica (BnF - Francia):**
```bash
# Con ARK del viewer
python3 main.py https://gallica.bnf.fr/ark:/12148/bpt6k9604118j

# Oppure con URL del manifest diretto
python3 main.py https://gallica.bnf.fr/iiif/ark:/12148/bpt6k9604118j/manifest.json
```

> **Nota per Gallica**: A volte Gallica blocca connessioni da server cloud. Se hai problemi, prova da un PC locale.

| Opzione | Descrizione |
|---|---|
| `-o`, `--output` | Nome specifico del PDF (default: automatico dal titolo) |
| `-w`, `--workers` | Thread simultanei (default: 4) |
| `--clean-cache` | Pulisce i file temporanei prima di iniziare |
| `--prefer-images` | Forza il download delle immagini anche se esiste un PDF ufficiale |

## 🏗️ Struttura del Progetto per Sviluppatori

Il progetto è modulare:
- `iiif_downloader/core.py`: Motore di download universale.
- `iiif_downloader/resolvers/`: Plugin per riconoscere diversi siti (Vaticano, Generic, ecc.).
- `main.py`: Punto di ingresso.
