import os
import streamlit as st
import time
from PIL import Image as PILImage

from iiif_downloader.pdf_utils import load_pdf_page, generate_pdf_from_images
from iiif_downloader.ui.components import interactive_viewer
from iiif_downloader.ui.state import get_storage, get_model_manager
from iiif_downloader.ui.styling import render_gallery_card
from iiif_downloader.ocr.processor import OCRProcessor, KRAKEN_AVAILABLE
from iiif_downloader.jobs import job_manager
from iiif_downloader.config import config
from iiif_downloader.logger import get_logger

logger = get_logger(__name__)

def render_studio_page():
    storage = get_storage()
    docs = storage.list_documents()
    
    if not docs:
        st.title("🏛️ Studio")
        st.info("Nessun documento scaricato. Vai alla sezione 'Discovery' per iniziare.")
        return

    # --- SIDEBAR: SELECTION ---
    st.sidebar.subheader("Selezione Documento")
    
    # Check for override navigation from Search
    default_idx = 0
    if "studio_doc_id" in st.session_state and st.session_state["studio_doc_id"]:
        for i, d in enumerate(docs):
            if d["id"] == st.session_state["studio_doc_id"]:
                default_idx = i
                break
        # Clear override
        st.session_state["studio_doc_id"] = None
        
    doc_labels = [f"{d['library']} / {d['id']}" for d in docs]
    selected_label = st.sidebar.selectbox("Manoscritto", doc_labels, index=default_idx)
    selected_doc = next(d for d in docs if f"{d['library']} / {d['id']}" == selected_label)
    
    doc_id, library = selected_doc["id"], selected_doc["library"]
    paths = storage.get_document_paths(doc_id, library)
    doc_id, library = selected_doc["id"], selected_doc["library"]
    paths = storage.get_document_paths(doc_id, library)
    
    # --- METADATA PANEL ---
    stats = storage.load_image_stats(doc_id, library)
    with st.sidebar.expander("ℹ️ Dettagli Tecnici", expanded=False):
        if stats:
            pages_s = stats.get("pages", [])
            if pages_s:
                avg_w = sum(p["width"] for p in pages_s) // len(pages_s)
                avg_h = sum(p["height"] for p in pages_s) // len(pages_s)
                total_mb = sum(p["size_bytes"] for p in pages_s) / (1024*1024)
                st.write(f"**Risoluzione Media**: {avg_w}x{avg_h} px")
                st.write(f"**Peso Totale**: {total_mb:.1f} MB")
                st.write(f"**Pagine**: {len(pages_s)}")
        
        meta = storage.load_metadata(doc_id, library)
        if meta:
            st.markdown("### 📜 Dati Manifesto")
            st.write(f"**Titolo**: {meta.get('label', 'Senza Titolo')}")
            st.write(f"**Descrizione**: {meta.get('description', '-')}")
            st.write(f"**Attribuzione**: {meta.get('attribution', '-')}")
            st.write(f"**Licenza**: {meta.get('license', '-')}")
            
            if 'metadata' in meta and isinstance(meta['metadata'], list):
                st.markdown("---")
                for entry in meta['metadata']:
                    # Handle different IIIF metadata formats
                    label = entry.get('label')
                    val = entry.get('value')
                    
                    # Some manifests invoke lists for labels/values
                    if isinstance(label, list): label = label[0] if label else "Info"
                    if isinstance(label, dict): label = list(label.values())[0] # simple fallback
                    
                    if isinstance(val, list): val = ", ".join([str(v) for v in val])
                    if isinstance(val, dict): val = list(val.values())[0]

                    st.write(f"**{label}**: {val}")
            
            st.caption(f"Scaricato il: {meta.get('download_date')}")
            st.caption(f"Manifest: {meta.get('manifest_url')}")
    active_job = job_manager.list_jobs(active_only=True)
    if active_job:
        for jid, job in active_job.items():
            st.sidebar.info(f"⚙️ {job['message']} ({int(job['progress']*100)}%)")
    
    # --- EXPORT ACTIONS ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Esportazione")
    if st.sidebar.button("📄 Crea PDF Completo", use_container_width=True):
         with st.spinner("Generazione PDF in corso..."):
             # Gather all images
             pages_dir = paths["pages"]
             if os.path.exists(pages_dir):
                 imgs = sorted([os.path.join(pages_dir, f) for f in os.listdir(pages_dir) if f.endswith(".jpg")])
                 if imgs:
                     pdf_out = os.path.join(paths["root"], f"{doc_id}.pdf")
                     success, msg = generate_pdf_from_images(imgs, pdf_out)
                     if success:
                         st.toast("PDF Creato!", icon="✅")
                         st.sidebar.success(f"PDF salvato in: {pdf_out}")
                     else:
                         st.sidebar.error(msg)
                 else:
                     st.sidebar.error("Nessuna immagine trovata.")
             else:
                 st.sidebar.error("Directory pagine non trovata.")

    # --- OCR CONTROLS ---
    st.sidebar.markdown("---")
    ocr_engine, current_model = render_ocr_controls(doc_id, library)
    
    # --- MAIN CANVAS ---
    render_main_canvas(doc_id, library, paths, stats, ocr_engine, current_model)

def render_ocr_controls(doc_id, library):
    st.sidebar.subheader("Strumenti OCR")
    
    storage = get_storage()
    manager = get_model_manager()
    default_engine = config.get("defaults", "preferred_ocr_engine", "openai")
    
    ocr_engine = st.sidebar.selectbox("Motore", ["openai", "kraken", "anthropic", "google", "huggingface"], index=["openai", "kraken", "anthropic", "google", "huggingface"].index(default_engine) if default_engine in ["openai", "kraken", "anthropic", "google", "huggingface"] else 0)
    
    current_model = None
    if ocr_engine == "kraken":
        installed = manager.list_installed_models()
        if not installed:
            st.sidebar.warning("Nessun modello Kraken installato.")
        else:
            current_model = st.sidebar.selectbox("Modello HTR", installed)
    elif ocr_engine == "openai":
        current_model = st.sidebar.selectbox("Modello", ["gpt-5", "gpt-5.2", "o3", "o4-mini", "gpt-5,-mini"], index=0)
    
    # API Keys are loaded from env, but user can override in session (not impl for now to keep clean)
    
    if st.sidebar.button("📚 OCR Intero Manoscritto (Background)", use_container_width=True):
        # Check if any pages exist
        full_data = storage.load_transcription(doc_id, None, library)
        has_data = full_data and len(full_data.get("pages", [])) > 0
        
        if has_data:
            st.session_state["confirm_ocr_batch"] = True
        else:
            # Trigger directly
            job_id = job_manager.submit_job(
                task_func=run_ocr_batch_task,
                kwargs={"doc_id": doc_id, "library": library, "engine": ocr_engine, "model": current_model},
                job_type="ocr_batch"
            )
            st.toast(f"Job avviato! ID: {job_id}", icon="⚙️")

    if st.session_state.get("confirm_ocr_batch"):
        st.sidebar.warning("⚠️ Ci sono trascrizioni esistenti! Sovrascrivere TUTTO?", icon="🔥")
        c1, c2 = st.sidebar.columns(2)
        if c1.button("Sì, Esegui", use_container_width=True, type="primary"):
             job_id = job_manager.submit_job(
                task_func=run_ocr_batch_task,
                kwargs={"doc_id": doc_id, "library": library, "engine": ocr_engine, "model": current_model},
                job_type="ocr_batch"
            )
             st.toast(f"Job avviato! ID: {job_id}", icon="⚙️")
             st.session_state["confirm_ocr_batch"] = False
        if c2.button("Annulla", use_container_width=True):
            st.session_state["confirm_ocr_batch"] = False
            st.rerun()

    return ocr_engine, current_model

def render_main_canvas(doc_id, library, paths, stats=None, ocr_engine="openai", current_model="gpt-5"):
    st.title(f"🏛️ {doc_id}")
    
    storage = get_storage()
    meta = storage.load_metadata(doc_id, library)
    
    # Robust Page Counting
    # 1. Try metadata
    # 2. Try counting files in 'pages' dir
    total_pages = 100 # Safe default
    if meta and meta.get("pages"):
        total_pages = int(meta.get("pages"))
    else:
        # Fallback: Count files
        pages_dir = paths["pages"]
        if os.path.exists(pages_dir):
            files = [f for f in os.listdir(pages_dir) if f.endswith(".jpg")]
            if files:
                total_pages = len(files)
    
    # Ensure at least 1 page to avoid slider errors
    total_pages = max(1, total_pages)
    
    # --- PAGE NAVIGATION ---
    if "current_page" not in st.session_state: st.session_state["current_page"] = 1
    # Check for page override
    if "studio_page" in st.session_state and st.session_state["studio_page"]:
        st.session_state["current_page"] = st.session_state["studio_page"]
        st.session_state["studio_page"] = None # Clear

    c1, c2, c3 = st.columns([1, 8, 1])
    if c1.button("◀", use_container_width=True): 
        st.session_state["current_page"] = max(1, st.session_state["current_page"] - 1)
        st.rerun()
    
    page = c2.slider("Page", 1, total_pages, value=st.session_state["current_page"], label_visibility="collapsed")
    if page != st.session_state["current_page"]:
        st.session_state["current_page"] = page
        st.rerun()
        
    if c3.button("▶", use_container_width=True):
        st.session_state["current_page"] = min(total_pages, st.session_state["current_page"] + 1)
        st.rerun()

    # --- CONTENT AREA ---
    col_img, col_txt = st.columns([1, 1])
    
    current_p = st.session_state["current_page"]
    
    with col_img:
        st.markdown(f"### Scansione ({current_p}/{total_pages})")
        page_img_path = os.path.join(paths["root"], "pages", f"pag_{current_p-1:04d}.jpg")
        
        # Fallback to pdf load if jpg not found (legacy support)
        img_obj = None
        if os.path.exists(page_img_path):
            img_obj = PILImage.open(page_img_path)
        elif os.path.exists(paths["pdf"]):
            img_obj = load_pdf_page(paths["pdf"], current_p)
            
        if img_obj:
            interactive_viewer(img_obj, zoom_percent=100)
            
            # Show specific page details
            p_stat = None
            if stats:
                p_stat = next((p for p in stats.get("pages", []) if p.get("page_index") == current_p-1), None)
            
            # Fallback for on-the-fly calc
            if not p_stat and img_obj:
                w, h = img_obj.size
                file_size = 0
                if os.path.exists(page_img_path):
                   file_size = os.path.getsize(page_img_path)
                
                p_stat = {
                    "width": w, 
                    "height": h, 
                    "size_bytes": file_size, 
                    "resolution_category": "Web"
                }

            if p_stat:
                mb_size = p_stat['size_bytes'] / (1024*1024)
                st.caption(f"📏 {p_stat['width']}x{p_stat['height']} px | 💾 {mb_size:.2f} MB | {p_stat.get('resolution_category', 'N/A')}")
        else:
            st.error("Immagine non trovata.")

    with col_txt:
        # Load Transcription
        # Load Transcription
        trans = storage.load_transcription(doc_id, current_p, library)
        
        st.markdown(f"### Trascrizione")
        
        # Confirmation Dialog (Inline)
        if st.session_state.get("confirm_ocr_sync") == st.session_state.get("current_page", 1):
             st.warning("⚠️ Testo esistente! Sovrascrivere?", icon="⚠️")
             c1, c2 = st.columns(2)
             if c1.button("Sì, Sovrascrivi", use_container_width=True, type="primary"):
                 page_idx = st.session_state["confirm_ocr_sync"]
                 run_ocr_sync(doc_id, library, page_idx, ocr_engine, current_model)
                 st.session_state["confirm_ocr_sync"] = None
             if c2.button("No, Annulla", use_container_width=True):
                 st.session_state["confirm_ocr_sync"] = None
                 st.rerun()

        # Prepare initial values
        initial_text = ""
        current_status = "draft"
        is_manual = False
        original_ocr = None
        
        if trans:
            initial_text = trans.get("full_text", "")
            current_status = trans.get("status", "draft")
            is_manual = trans.get("is_manual", False)
            original_ocr = trans.get("original_ocr_text")
        
        # --- EDITOR CONTROLS ---
        # We use session state to track dirty status if possible, 
        # but Streamlit re-runs on every interaction, so we rely on comparing text.
        
        edit_key = f"trans_editor_{doc_id}_{current_p}"
        
        # Text Area with on_change is tricky, so we just check value on button press 
        # or use a form. Using a form prevents "dirty" detection live easily without rerun.
        # Let's use a standard area and check logic on button.
        
        text_val = st.text_area(
            "Editor", 
            value=initial_text, 
            height=700, 
            key=edit_key,
            label_visibility="collapsed"
        )
        
        # Toolbar
        # Row 1: Save | Verify | OCR | Revert
        t_c1, t_c2, t_c3, t_c4 = st.columns([2, 2, 2, 1])
        
        # Dirty Check
        is_dirty = text_val != initial_text
        
        with t_c1:
            if st.button("💾 Salva", use_container_width=True, type="primary" if is_dirty else "secondary"):
                new_data = {
                    "full_text": text_val,
                    "engine": trans.get("engine", "manual") if trans else "manual",
                    "is_manual": True,
                    "status": current_status,
                    "average_confidence": 1.0
                }
                storage.save_transcription(doc_id, current_p, new_data, library)
                st.toast("✅ Modifiche salvate!", icon="💾")
                time.sleep(0.5)
                st.rerun()

        with t_c2:
            # Verified Toggle
            is_verified = current_status == "verified"
            btn_label = "✅ Verificato" if is_verified else "⚪ Da Verificare"
            if st.button(btn_label, use_container_width=True):
                new_status = "draft" if is_verified else "verified"
                data_to_save = trans if trans else {"full_text": "", "lines": [], "engine": "manual"}
                data_to_save["status"] = new_status
                data_to_save["is_manual"] = True 
                storage.save_transcription(doc_id, current_p, data_to_save, library)
                st.rerun()
                
        with t_c3:
            # OCR Button
            if st.button(f"⚡ {ocr_engine}", use_container_width=True, help="Esegui OCR su questa pagina"):
                 page_idx = st.session_state.get("current_page", 1)
                 existing = storage.load_transcription(doc_id, page_idx, library)
                 if existing:
                     st.session_state["confirm_ocr_sync"] = page_idx
                 else:
                     run_ocr_sync(doc_id, library, page_idx, ocr_engine, current_model)

        with t_c4:
            # Revert Button
            if is_manual and original_ocr:
                if st.button("↩", use_container_width=True, help="Revert all'OCR originale"):
                    revert_data = {
                        "full_text": original_ocr,
                        "engine": trans.get("original_engine", "unknown"),
                        "is_manual": False, 
                        "status": "draft",
                        "average_confidence": 0.0
                    }
                    storage.save_transcription(doc_id, current_p, revert_data, library)
                    st.toast("Revert completato!", icon="↩")
                    st.rerun()

        # Confirmation Dialog (Inline below toolbar)
        if st.session_state.get("confirm_ocr_sync") == st.session_state.get("current_page", 1):
             st.warning("⚠️ Testo esistente! Sovrascrivere?", icon="⚠️")
             c1, c2 = st.columns(2)
             if c1.button("Sì, Sovrascrivi", use_container_width=True, type="primary"):
                 page_idx = st.session_state["confirm_ocr_sync"]
                 run_ocr_sync(doc_id, library, page_idx, ocr_engine, current_model)
                 st.session_state["confirm_ocr_sync"] = None
             if c2.button("No, Annulla", use_container_width=True):
                 st.session_state["confirm_ocr_sync"] = None
                 st.rerun()

        # Metadata Footer
        if trans:
            st.caption(f"Engine: {trans.get('engine')} | Conf: {trans.get('average_confidence', 'N/A')} | 🕒 {trans.get('timestamp', '-')}")
            if is_manual:
                st.caption("✍️ Modificato Manualmente")
        else:
            st.info("Nessuna trascrizione (scrivi e salva per creare).")

def run_ocr_sync(doc_id, library, page_idx, engine, model):
    storage = get_storage()
    paths = storage.get_document_paths(doc_id, library)
    page_img_path = os.path.join(paths["root"], "pages", f"pag_{page_idx-1:04d}.jpg")
    
    if not os.path.exists(page_img_path):
        st.error("Immagine non trovata, impossibile eseguire OCR.")
        return

    img = PILImage.open(page_img_path)
    
    with st.spinner(f"Elaborazione OCR ({engine})..."):
        proc = OCRProcessor(
            model_path=get_model_manager().get_model_path(model) if engine == "kraken" else None,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        res = proc.process_page(img, engine=engine, model=model)
        
        if not res.get("error"):
            storage.save_transcription(doc_id, page_idx, res, library)
            st.toast("OCR Completato!", icon="✅")
            st.rerun()
        else:
            st.error(f"Errore: {res.get('error')}")

def run_ocr_batch_task(doc_id, library, engine, model, progress_callback=None):
    """Background task function."""
    storage = get_storage() # New instance safely
    paths = storage.get_document_paths(doc_id, library)
    pages_dir = os.path.join(paths["root"], "pages")
    
    # List all pages
    files = sorted([f for f in os.listdir(pages_dir) if f.endswith(".jpg")])
    total = len(files)
    
    proc = OCRProcessor(
        model_path=get_model_manager().get_model_path(model) if engine == "kraken" else None,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    
    for i, f in enumerate(files):
        # Extract page number from filename pag_0000.jpg -> 1
        try:
            p_idx = int(f.split("_")[1].split(".")[0]) + 1
        except:
            continue
            
        # Check if already exists? Maybe skip options in future.
        
        img_path = os.path.join(pages_dir, f)
        img = PILImage.open(img_path)
        
        res = proc.process_page(img, engine=engine, model=model)
        
        if not res.get("error"):
            # We need to use storage instance from main thread? 
            # SQLite is thread-safe for file access usually, but let's be careful.
            # Using simple JSON storage from the original class shouldn't lock hard.
            storage.save_transcription(doc_id, p_idx, res, library)
        
        if progress_callback:
            progress_callback(i+1, total)
            
    return f"Processed {total} pages."
