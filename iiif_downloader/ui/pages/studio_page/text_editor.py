"""
Transcription Editor Component
Handles the right column of the Studio page: text editing, OCR, and history.
"""

import html
import time

import streamlit as st
from bs4 import BeautifulSoup
from streamlit_quill import st_quill

from iiif_downloader.ui.notifications import toast
from iiif_downloader.ui.state import get_storage

from .ocr_utils import run_ocr_sync
from .studio_state import StudioState


def render_transcription_editor(
    doc_id: str, library: str, current_page: int, ocr_engine: str, current_model: str
) -> tuple:
    """
    Render the transcription editor with all controls.

    Args:
        doc_id: Document ID
        library: Library name
        current_page: Current page number (1-indexed)
        ocr_engine: OCR engine name
        current_model: OCR model name

    Returns:
        Tuple of (transcription_data, current_text_value)
    """

    storage = get_storage()
    trans = storage.load_transcription(doc_id, current_page, library)
    initial_text = trans.get("full_text", "") if trans else ""
    current_status = trans.get("status", "draft") if trans else "draft"
    is_manual = trans.get("is_manual", False) if trans else False

    # TAB SYSTEM: Trascrizione, Cronologia, Snippet
    tabs = st.tabs(["📝 Trascrizione", "📜 Cronologia", "✂️ Snippet"])
    
    # TAB 1: TRASCRIZIONE
    with tabs[0]:
        _render_transcription_tab(doc_id, library, current_page, trans, current_status, ocr_engine, current_model, storage)
    
    # TAB 2: CRONOLOGIA
    with tabs[1]:
        render_history_sidebar(doc_id, library, current_page, current_data=trans, current_text="")
    
    # TAB 3: SNIPPET (ritagli della pagina)
    with tabs[2]:
        _render_snippets_tab(doc_id, current_page)
    
    return trans, ""  # Return empty text for now


def _render_transcription_tab(
    doc_id: str, library: str, current_page: int, trans: dict, current_status: str, 
    ocr_engine: str, current_model: str, storage
) -> str:
    """Render the main transcription editor tab."""
    
    initial_text = trans.get("full_text", "") if trans else ""
    is_manual = trans.get("is_manual", False) if trans else False
    
    # Verification badge
    v_badge = ""
    if current_status == "verified":
        v_badge = '<span style="background-color: #28a745; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; margin-left: 10px; vertical-align: middle;">VERIFICATO ✅</span>'
    
    if not trans:
        st.caption("Nessuna trascrizione. Scrivi e salva per creare.")

    # Handle OCR triggers
    _handle_ocr_triggers(doc_id, library, current_page, ocr_engine, current_model, storage)

    # Editor key
    edit_key = StudioState.get_editor_key(doc_id, current_page)

    # Check for pending updates (from history restore or OCR)
    pending_text = StudioState.get_pending_update(doc_id, current_page)
    if pending_text:
        initial_text = pending_text

    # Prepare rich text content
    rich_content = trans.get("rich_text", "") if trans else ""

    # Fallback: convert plain text to HTML
    if not rich_content and initial_text:
        rich_content = "".join(f"<p>{html.escape(line)}</p>" for line in initial_text.splitlines() if line.strip())

    # Rich text editor
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

    # Pulsantiera uniforme sotto l'editor
    btn_col1, btn_col2, btn_col3 = st.columns(3)

    with btn_col1:
        if st.button(
            "💾 Salva",
            use_container_width=True,
            type="primary",
            key=f"save_btn_{doc_id}_{current_page}",
        ):
            _save_transcription(text_val, doc_id, library, current_page, trans, current_status, storage)

    with btn_col2:
        _render_verification_button(doc_id, library, current_page, current_status, trans, storage)

    with btn_col3:
        _render_ocr_button(doc_id, library, current_page, ocr_engine, storage)
    
    # Indicatore modifiche non salvate
    if text_val != rich_content:
        st.caption("📝 _Modifiche non salvate_")

    # Metadata
    if trans:
        st.caption(
            f"Engine: {trans.get('engine')} | Conf: {trans.get('average_confidence', 'N/A')} | 🕒 {trans.get('timestamp', '-')}"
        )
        if is_manual:
            st.caption("✍️ Modificato Manualmente")
    
    return text_val


def _render_snippets_tab(doc_id: str, current_page: int):
    """Render the snippets tab showing image crops for current page."""
    
    try:
        from iiif_downloader.database_manager import VaultManager
        
        vault = VaultManager()
        snippets = vault.get_snippets(doc_id, page_index=current_page - 1)
        
        if not snippets:
            st.info("📭 Nessun ritaglio salvato per questa pagina.")
            st.caption("Usa gli strumenti di ritaglio nella colonna Scansione per creare snippet.")
            return
        
        st.markdown(f"**{len(snippets)} ritagli salvati**")
        st.markdown("---")
        
        for snippet in snippets:
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"**{snippet['label']}**")
                    if snippet['tags']:
                        tags_display = " · ".join([f"#{t.strip()}" for t in snippet['tags'].split(',')])
                        st.caption(tags_display)
                    st.caption(f"🕒 {snippet['created_at']}")
                
                with col2:
                    if st.button("🗑️", key=f"del_snip_{snippet['id']}", help="Elimina"):
                        vault.delete_snippet(snippet['id'])
                        # Delete file if exists
                        if snippet.get('image_path'):
                            import os
                            if os.path.exists(snippet['image_path']):
                                try:
                                    os.remove(snippet['image_path'])
                                except:
                                    pass
                        toast("Ritaglio eliminato", icon="🗑️")
                        st.rerun()
                
                # Show image if available
                if snippet.get('image_path'):
                    import os
                    from pathlib import Path
                    if os.path.exists(snippet['image_path']):
                        st.image(snippet['image_path'], use_container_width=True)
                
                st.markdown("---")
                
    except Exception as e:
        st.error(f"Errore caricamento snippet: {e}")


def _handle_ocr_triggers(doc_id, library, current_page, ocr_engine, current_model, storage):
    """Handle OCR confirmation and execution triggers."""

    # Confirmation dialog
    if StudioState.get(StudioState.CONFIRM_OCR_SYNC) == current_page:
        st.warning("⚠️ Testo esistente! Sovrascrivere?", icon="⚠️")
        c1, c2 = st.columns(2)
        if c1.button("Sì, Sovrascrivi", use_container_width=True, type="primary"):
            StudioState.set(StudioState.TRIGGER_OCR_SYNC, current_page)
            StudioState.set(StudioState.CONFIRM_OCR_SYNC, None)
            st.rerun()
        if c2.button("No, Annulla", use_container_width=True):
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

    toast("✅ Modifiche salvate!", icon="💾")
    time.sleep(0.5)
    st.rerun()


def _render_verification_button(doc_id, library, current_page, current_status, trans, storage):
    """Render the verification toggle button."""

    is_verified = current_status == "verified"
    btn_label = "⚪ Segna come da Verificare" if is_verified else "✅ Segna come Verificato"

    if st.button(btn_label, use_container_width=True, key=f"btn_verify_{current_page}"):
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
        use_container_width=True,
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
        if st.button("🗑️", key=f"clear_{current_page}", help="Svuota cronologia", use_container_width=True):
            if st.session_state.get(f"confirm_clear_{current_page}"):
                storage.clear_history(doc_id, current_page, library)
                del st.session_state[f"confirm_clear_{current_page}"]
                st.rerun()
            else:
                st.session_state[f"confirm_clear_{current_page}"] = True
                st.rerun()
    
    if st.session_state.get(f"confirm_clear_{current_page}"):
        st.warning("⚠️ Conferma eliminazione")
        if st.button("Annulla", key=f"cancel_{current_page}", use_container_width=True):
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
                use_container_width=True,
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
