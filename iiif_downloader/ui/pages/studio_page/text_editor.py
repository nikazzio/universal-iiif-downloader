"""
Transcription Editor Component
Handles the right column of the Studio page: text editing, OCR, and history.
"""

import html
import time

import streamlit as st
from bs4 import BeautifulSoup
from streamlit_quill import st_quill

from pathlib import Path

from iiif_downloader.logger import get_logger
from iiif_downloader.ui.notifications import toast
from iiif_downloader.ui.state import get_storage

logger = get_logger(__name__)

from .ocr_utils import run_ocr_sync
from .studio_state import StudioState


def render_transcription_editor(
    doc_id: str, library: str, current_page: int, ocr_engine: str, current_model: str, paths: dict = None, total_pages: int = 1
) -> tuple:
    """
    Render the transcription editor with all controls.

    Args:
        doc_id: Document ID
        library: Library name
        current_page: Current page number (1-indexed)
        ocr_engine: OCR engine name
        current_model: OCR model name
        paths: Document paths dictionary

    Returns:
        Tuple of (transcription_data, current_text_value)
    """

    storage = get_storage()
    trans = storage.load_transcription(doc_id, current_page, library)
    initial_text = trans.get("full_text", "") if trans else ""
    current_status = trans.get("status", "draft") if trans else "draft"
    is_manual = trans.get("is_manual", False) if trans else False

    # NAVIGAZIONE CONSOLIDATA (Top-Right) con Timeline integrata
    _render_consolidated_navigation(doc_id, current_page, total_pages)

    # CSS injection per editor Quill (eseguito una volta sola)
    st.markdown("""
        <style>
        /* Editor Quill container */
        .ql-container {
            height: calc(100% - 42px) !important;
            overflow-y: auto !important;
            border: none !important;
        }
        .ql-editor {
            height: 100% !important;
            min-height: 650px !important;
        }
        .ql-toolbar {
            border-bottom: 1px solid #ddd !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # TAB SYSTEM: Trascrizione, Cronologia, Snippet, Info
    tabs = st.tabs(["📝 Trascrizione", "📜 Cronologia", "✂️ Snippet", "ℹ️ Info Manoscritto"])
    
    # TAB 1: TRASCRIZIONE
    with tabs[0]:
        _render_transcription_tab(doc_id, library, current_page, trans, current_status, ocr_engine, current_model, storage)
    
    # TAB 2: CRONOLOGIA
    with tabs[1]:
        render_history_sidebar(doc_id, library, current_page, current_data=trans, current_text="")
    
    # TAB 3: SNIPPET (ritagli della pagina)
    with tabs[2]:
        _render_snippets_tab(doc_id, current_page)
    
    # TAB 4: INFO MANOSCRITTO
    with tabs[3]:
        _render_manuscript_info(doc_id, library)
    
    return trans, ""  # Return empty text for now


def _render_transcription_tab(
    doc_id: str, library: str, current_page: int, trans: dict, current_status: str, 
    ocr_engine: str, current_model: str, storage
) -> str:
    """Render the main transcription editor tab."""
    
    if not trans:
        st.caption("Nessuna trascrizione. Scrivi e salva per creare.")

    # Handle OCR triggers
    _handle_ocr_triggers(doc_id, library, current_page, ocr_engine, current_model, storage)

    # Editor key
    edit_key = StudioState.get_editor_key(doc_id, current_page)

    # Check for pending updates (from history restore or OCR)
    pending_text = StudioState.get_pending_update(doc_id, current_page)
    
    # Prepare rich text content
    rich_content = trans.get("rich_text", "") if trans else ""

    # Fallback: convert plain text to HTML
    if not rich_content:
        # Use pending text if available, otherwise use full_text from trans
        text_to_convert = pending_text if pending_text else (trans.get("full_text", "") if trans else "")
        if text_to_convert:
            rich_content = "".join(f"<p>{html.escape(line)}</p>" for line in text_to_convert.splitlines() if line.strip())
    
    # FORM per isolare l'editor e impedire che INVIO triggeri la navigazione
    with st.form(key=f"transcription_form_{doc_id}_{current_page}", clear_on_submit=False):
        text_val = st_quill(
            value=rich_content,
            key=edit_key,
            html=True,
            preserve_whitespace=True,
            placeholder="Scrivi qui la tua trascrizione...",
            toolbar=[
                ["bold", "italic", "underline", "strike"],
                [{"list": "ordered"}, {"list": "bullet"}],
                [{"script": "sub"}, {"script": "super"}],
                [{"indent": "-1"}, {"indent": "+1"}],
                [{"header": [1, 2, 3, False]}],
                [{"color": []}, {"background": []}],
                [{"align": []}],
                ["clean"],
            ],
        )
        
        # Pulsante Salva dentro il form (submit)
        save_btn = st.form_submit_button(
            "💾 Salva",
            use_container_width=True,
            type="primary",
        )
        
        if save_btn:
            _save_transcription(text_val, doc_id, library, current_page, trans, current_status, storage)

    # Pulsanti Verifica e OCR FUORI dal form (come bottoni indipendenti)
    btn_col2, btn_col3 = st.columns(2)

    with btn_col2:
        _render_verification_button(doc_id, library, current_page, current_status, trans, storage)

    with btn_col3:
        _render_ocr_button(doc_id, library, current_page, ocr_engine, storage)

    # Metadata
    if trans:
        is_manual = trans.get("is_manual", False)
        engine = trans.get('engine', 'N/A')
        conf = trans.get('average_confidence', 'N/A')
        timestamp = trans.get('timestamp', '-')
        
        meta_parts = [f"Engine: {engine}", f"Conf: {conf}", f"🕒 {timestamp}"]
        if is_manual:
            meta_parts.append("✍️ Modificato Manualmente")
        
        st.caption(" | ".join(meta_parts))
    
    return text_val


def _render_snippets_tab(doc_id: str, current_page: int):
    """Render the snippets tab showing image crops for current page."""
    
    logger.debug(f"Render tab snippet - doc={doc_id}, page={current_page}")
    
    try:
        from iiif_downloader.storage import VaultManager
        
        vault = VaultManager()
        snippets = vault.get_snippets(doc_id, page_num=current_page)
        
        if not snippets:
            logger.debug(f"Nessuno snippet trovato per {doc_id} pagina {current_page}")
            st.info("📭 Nessun snippet salvato per questa pagina.")
            st.caption("✂️ Usa il pulsante 'Taglia' nella toolbar dell'immagine per creare snippet.")
            return
        
        st.markdown(f"### 🖼️ Galleria Snippet ({len(snippets)})")
        st.caption(f"Pagina {current_page} - {doc_id}")
        st.markdown("---")
        
        # Container scrollabile per molti snippet
        st.markdown("""
            <style>
            .snippet-container {
                max-height: 600px;
                overflow-y: auto;
                padding-right: 10px;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Wrapper scrollabile
        with st.container():
            st.markdown('<div class="snippet-container">', unsafe_allow_html=True)
            
            # Mostra ogni snippet
            for snippet in snippets:
                with st.container():
                    # Colonne per layout
                    img_col, info_col = st.columns([1, 2])
                    
                    with img_col:
                        # Mostra miniatura
                        img_path = Path(snippet['image_path'])
                        
                        if img_path.exists():
                            st.image(snippet['image_path'], width="stretch")
                        else:
                            st.warning("⚠️ File non trovato")
                            logger.warning(f"File snippet non trovato: {img_path}")
                    
                    with info_col:
                        # Tag categoria
                        category_colors = {
                            "Capolettera": "#FF6B6B",
                            "Glossa": "#4ECDC4",
                            "Abbreviazione": "#95E1D3",
                            "Dubbio": "#FFE66D",
                            "Illustrazione": "#A8E6CF",
                            "Decorazione": "#FF8B94",
                            "Nota Marginale": "#C7CEEA",
                            "Altro": "#B0B0B0",
                        }
                        
                        cat_color = category_colors.get(snippet.get('category'), "#999")
                        st.markdown(
                            f"<span style='background: {cat_color}; padding: 4px 12px; border-radius: 12px; color: white; font-weight: bold; font-size: 0.85rem;'>{snippet.get('category', 'N/A')}</span>",
                            unsafe_allow_html=True
                        )
                        
                        st.caption(f"🕖 {snippet['timestamp']}")
                        
                        # Espandi per vedere dettagli
                        with st.expander("🔍 Espandi dettagli"):
                            if snippet.get('transcription'):
                                st.markdown(f"**✍️ Trascrizione:**")
                                st.text(snippet['transcription'])
                            
                            if snippet.get('notes'):
                                st.markdown(f"**📝 Note:**")
                                st.text_area(
                                    "Note",
                                    value=snippet['notes'],
                                    disabled=True,
                                    key=f"notes_view_{snippet['id']}",
                                    label_visibility="collapsed",
                                    height=100,
                                )
                            
                            if snippet.get('coords_json'):
                                coords = snippet['coords_json']
                                st.caption(f"📐 Dimensioni: {coords[2]}x{coords[3]} px")
                        
                        # Pulsante elimina
                        if st.button("🗑️ Elimina", key=f"del_snippet_{snippet['id']}", type="secondary"):
                            vault.delete_snippet(snippet['id'])
                            toast("✅ Snippet eliminato!", icon="🗑️")
                            st.rerun()
                    
                    st.markdown("<hr style='margin: 1rem 0; opacity: 0.2;'>", unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ Errore nel caricamento snippet: {e}")


def _handle_ocr_triggers(doc_id, library, current_page, ocr_engine, current_model, storage):
    """Handle OCR confirmation and execution triggers."""

    # Confirmation dialog
    if StudioState.get(StudioState.CONFIRM_OCR_SYNC) == current_page:
        st.warning("⚠️ Testo esistente! Sovrascrivere?", icon="⚠️")
        c1, c2 = st.columns(2)
        if c1.button("Sì, Sovrascrivi", width="stretch", type="primary"):
            StudioState.set(StudioState.TRIGGER_OCR_SYNC, current_page)
            StudioState.set(StudioState.CONFIRM_OCR_SYNC, None)
            st.rerun()
        if c2.button("No, Annulla", width="stretch"):
            StudioState.set(StudioState.CONFIRM_OCR_SYNC, None)
            st.rerun()

    # Execute OCR
    if StudioState.get(StudioState.TRIGGER_OCR_SYNC) == current_page:
        run_ocr_sync(doc_id, library, current_page, ocr_engine, current_model)
        StudioState.set(StudioState.TRIGGER_OCR_SYNC, None)
        st.rerun()


def _save_transcription(text_val, doc_id, library, current_page, trans, current_status, storage):
    """Save transcription to storage."""

    # Convert HTML to plain text
    soup = BeautifulSoup(text_val, "html.parser")
    clean_text = soup.get_text("\n")

    new_data = {
        "full_text": clean_text,
        "rich_text": text_val,
        "engine": trans.get("engine", "manual") if trans else "manual",
        "is_manual": True,
        "status": current_status,
        "average_confidence": 1.0,
    }
    storage.save_transcription(doc_id, current_page, new_data, library)

    # Feedback senza rerun completo
    toast("✅ Modifiche salvate!", icon="💾")
    # Non facciamo più rerun per migliorare UX


def _render_verification_button(doc_id, library, current_page, current_status, trans, storage):
    """Render the verification toggle button."""

    is_verified = current_status == "verified"
    btn_label = "⚪ Segna come da Verificare" if is_verified else "✅ Segna come Verificato"

    if st.button(btn_label, width="stretch", key=f"btn_verify_{current_page}"):
        new_status = "draft" if is_verified else "verified"
        data_to_save = trans if trans else {"full_text": "", "lines": [], "engine": "manual"}

        # Save snapshot to history
        storage.save_history(doc_id, current_page, data_to_save, library)

        data_to_save["status"] = new_status
        data_to_save["is_manual"] = True
        storage.save_transcription(doc_id, current_page, data_to_save, library)
        st.rerun()


def _render_ocr_button(doc_id, library, current_page, ocr_engine, storage):
    """Render the OCR execution button."""

    if st.button(
        f"🤖 Nuova Chiamata {ocr_engine}",
        width="stretch",
        key=f"btn_ocr_{current_page}",
    ):
        existing = storage.load_transcription(doc_id, current_page, library)
        if existing:
            StudioState.set(StudioState.CONFIRM_OCR_SYNC, current_page)
        else:
            StudioState.set(StudioState.TRIGGER_OCR_SYNC, current_page)
        st.rerun()


def render_history_sidebar(doc_id, library, current_page, current_data=None, current_text=""):
    """Render the history list in a vertical side column."""

    storage = get_storage()
    
    history = storage.load_history(doc_id, current_page, library)
    
    if not history:
        st.info("📭 Nessuna versione salvata")
        return
    
    # Header compatto con count
    col1, col2 = st.columns([2, 1])
    with col1:
        st.caption(f"**{len(history)} versioni**")
    with col2:
        if st.button("🗑️", key=f"clear_{current_page}", help="Svuota cronologia", width="stretch"):
            if st.session_state.get(f"confirm_clear_{current_page}"):
                storage.clear_history(doc_id, current_page, library)
                del st.session_state[f"confirm_clear_{current_page}"]
                st.rerun()
            else:
                st.session_state[f"confirm_clear_{current_page}"] = True
                st.rerun()
    
    if st.session_state.get(f"confirm_clear_{current_page}"):
        st.warning("⚠️ Conferma eliminazione")
        if st.button("Annulla", key=f"cancel_{current_page}", width="stretch"):
            del st.session_state[f"confirm_clear_{current_page}"]
            st.rerun()
    
    st.divider()

    edit_key = StudioState.get_editor_key(doc_id, current_page)

    # Versioni in container scrollabile
    for i in range(len(history)):
        idx = len(history) - 1 - i
        entry = history[idx]
        prev_entry = history[idx - 1] if idx > 0 else None

        _render_history_entry(
            entry,
            prev_entry,
            idx,
            i,
            len(history),
            doc_id,
            library,
            current_page,
            current_data,
            current_text,
            edit_key,
            storage,
        )


def _render_history_entry(
    entry,
    prev_entry,
    idx,
    i,
    total_entries,
    doc_id,
    library,
    current_page,
    current_data,
    current_text,
    edit_key,
    storage,
):
    """Render a single history entry."""

    ts = entry.get("timestamp", "-").split(" ")[1]  # Time only
    full_ts = entry.get("timestamp", "-")
    eng = entry.get("engine", "manual")
    status = entry.get("status", "draft")
    chars = len(entry.get("full_text", ""))
    is_manual_entry = entry.get("is_manual", False)

    icon = "✍️" if is_manual_entry else "🤖"
    v_label = " 📌" if idx == 0 else ""

    diff = 0
    if prev_entry:
        diff = chars - len(prev_entry.get("full_text", ""))

    diff_str = f"{diff:+d}" if diff != 0 else "="
    diff_color = "#28a745" if diff > 0 else "#dc3545" if diff < 0 else "#6c757d"
    status_icon = " ✅" if status == "verified" else ""

    with st.container():
        # Header compatto: tempo + icone + chars in una riga
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(
                f"<div style='line-height:1.2;'>"
                f"<span style='font-weight:600; font-size:0.9rem;'>{ts}</span>"
                f"<span style='margin-left:4px;'>{icon}</span>"
                f"{v_label}{status_icon}"
                f"<br><span style='color:#666; font-size:0.75rem;'>{eng} • {chars} ch <span style='color:{diff_color}'>({diff_str})</span></span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with col2:
            if st.button(
                "↩",
                key=f"restore_side_{current_page}_{idx}",
                width="stretch",
                help=f"Ripristina",
            ):
                _restore_history_version(
                    entry, current_text, current_data, doc_id, library, current_page, edit_key, storage
                )

    if i < total_entries - 1:
        st.markdown("<hr style='margin: 0.2rem 0; opacity: 0.3;'>", unsafe_allow_html=True)


def _restore_history_version(entry, current_text, current_data, doc_id, library, current_page, edit_key, storage):
    """Restore a previous version from history."""

    # Save current state as backup
    if current_text:
        soup_snap = BeautifulSoup(current_text, "html.parser")
        snap_plain = soup_snap.get_text("\n")

        snap = {
            "full_text": snap_plain,
            "rich_text": current_text,
            "engine": current_data.get("engine", "manual") if current_data else "manual",
            "is_manual": True,
            "status": current_data.get("status", "draft") if current_data else "draft",
        }
        storage.save_history(doc_id, current_page, snap, library)

    # Restore selected version
    storage.save_transcription(doc_id, current_page, entry, library)

    # Clear editor state to force refresh
    StudioState.clear_editor_state(doc_id, current_page)

    # Update editor with restored content
    restored_rich = entry.get("rich_text")
    restored_plain = entry.get("full_text", "")

    if restored_rich:
        st.session_state[edit_key] = restored_rich
    else:
        st.session_state[edit_key] = restored_plain

    toast("Versione ripristinata!")
    st.rerun()


def _render_consolidated_navigation(doc_id: str, current_page: int, total_pages: int):
    """Render consolidated navigation with integrated timeline (Top-Right)."""
    
    # Header con indicazione pagina (allineato con "Scansione" a sinistra)
    progress_pct = int((current_page - 1) * 100 / max(total_pages - 1, 1))
    page_info = f"<span style='color: #888; font-size: 0.9rem; margin-left: 15px;'>📍 Pagina {current_page} di {total_pages} ({progress_pct}%)</span>"
    
    st.markdown(
        f"### Navigazione {page_info}",
        unsafe_allow_html=True,
    )
    
    # PREV/NEXT buttons con callback semplificato
    nav_btn_cols = st.columns([1, 1], gap="small")
    
    with nav_btn_cols[0]:
        if st.button(
            "◀ PREV", 
            width="stretch", 
            key="btn_prev_nav", 
            disabled=current_page <= 1,
            on_click=lambda: StudioState.set_current_page(doc_id, max(1, current_page - 1))
        ):
            pass  # L'azione è gestita dal callback on_click
    
    with nav_btn_cols[1]:
        if st.button(
            "NEXT ▶", 
            width="stretch", 
            key="btn_next_nav", 
            disabled=current_page >= total_pages,
            on_click=lambda: StudioState.set_current_page(doc_id, min(total_pages, current_page + 1))
        ):
            pass  # L'azione è gestita dal callback on_click
    
    # Timeline slider - usa solo key senza value per evitare conflitti
    # Il callback sincronizza page_{doc_id} quando lo slider cambia
    def sync_page_from_slider():
        """Sincronizza la pagina corrente quando lo slider viene mosso."""
        new_page = st.session_state.get(f"timeline_{doc_id}", current_page)
        page_key = StudioState.get_page_key(doc_id)
        st.session_state[page_key] = new_page
    
    # Inizializza il valore dello slider se non esiste
    slider_key = f"timeline_{doc_id}"
    if slider_key not in st.session_state:
        st.session_state[slider_key] = current_page
    
    st.slider(
        "Scorri Timeline",
        min_value=1,
        max_value=total_pages,
        key=slider_key,
        label_visibility="collapsed",
        help="Naviga rapidamente tra le pagine",
        on_change=sync_page_from_slider
    )


def _render_manuscript_info(doc_id: str, library: str):
    """Render manuscript metadata and details in Info tab."""
    
    storage = get_storage()
    meta = storage.load_metadata(doc_id, library)
    stats = storage.load_image_stats(doc_id, library)
    
    st.markdown("### 📜 Informazioni Manoscritto")
    
    if meta:
        st.markdown(f"**Titolo**: {meta.get('label', 'Senza Titolo')}")
        
        desc = meta.get("description", "-")
        st.markdown(f"**Descrizione**: {desc}")
        
        st.markdown(f"**Attribuzione**: {meta.get('attribution', '-')}")
        st.markdown(f"**Licenza**: {meta.get('license', '-')}")
        
        if "metadata" in meta and isinstance(meta["metadata"], list):
            st.markdown("---")
            st.markdown("#### 🏷️ Metadati Aggiuntivi")
            for item in meta["metadata"]:
                if isinstance(item, dict):
                    label = item.get("label", "Campo")
                    value = item.get("value", "-")
                    st.markdown(f"**{label}**: {value}")
    
    if stats:
        st.markdown("---")
        st.markdown("#### 📊 Statistiche Tecniche")
        
        pages_s = stats.get("pages", [])
        if pages_s:
            avg_w = sum(p["width"] for p in pages_s) // len(pages_s)
            avg_h = sum(p["height"] for p in pages_s) // len(pages_s)
            total_mb = sum(p["size_bytes"] for p in pages_s) / (1024 * 1024)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Pagine", len(pages_s))
            with col2:
                st.metric("Risoluzione", f"{avg_w}×{avg_h}")
            with col3:
                st.metric("Peso", f"{total_mb:.1f} MB")
