"""
Image Viewer Component with Adjustments and Cropping
Handles the left column of the Studio page: image display, adjustments, and cropping.
"""

import os
from pathlib import Path
from typing import Optional, Tuple

import streamlit as st
from PIL import Image as PILImage

from iiif_downloader.config_manager import get_config_manager
from iiif_downloader.database_manager import VaultManager
from iiif_downloader.pdf_utils import load_pdf_page
from iiif_downloader.ui.components.viewer import interactive_viewer
from iiif_downloader.ui.notifications import toast

from .image_processing import ImageProcessor
from .studio_state import StudioState


def render_image_viewer(
    doc_id: str, library: str, paths: dict, current_page: int, stats: dict = None
) -> Tuple[Optional[PILImage.Image], dict]:
    """
    Render the image viewer with adjustments and cropping tools.

    Args:
        doc_id: Document ID
        library: Library name
        paths: Dictionary with paths (scans, pdf, root, etc.)
        current_page: Current page number (1-indexed)
        stats: Optional statistics dictionary

    Returns:
        Tuple of (original_image, page_stats)
    """

    # Load the original image
    page_img_path = Path(paths["scans"]) / f"pag_{current_page - 1:04d}.jpg"
    img_obj = None
    pdf_error = None

    if page_img_path.exists():
        img_obj = ImageProcessor.load_image(page_img_path)
    elif Path(paths.get("pdf", "")).exists():
        pdf_dpi = int(get_config_manager().get_setting("pdf.viewer_dpi", 150))
        img_obj, pdf_error = load_pdf_page(paths["pdf"], current_page, dpi=pdf_dpi, return_error=True)
        if pdf_error:
            st.warning(pdf_error)

    # Calculate page statistics
    p_stat = None
    if img_obj and stats:
        p_stat = next((p for p in stats.get("pages", []) if p.get("page_index") == current_page - 1), None)

    if not p_stat and img_obj:
        w, h = img_obj.size
        file_size = page_img_path.stat().st_size if page_img_path.exists() else 0
        p_stat = {"width": w, "height": h, "size_bytes": file_size}

    # Header with stats
    stats_str = ""
    if p_stat:
        mb_size = p_stat["size_bytes"] / (1024 * 1024)
        stats_str = f"<span style='color: #888; font-size: 0.9rem; margin-left: 15px;'>📏 {p_stat['width']}×{p_stat['height']} px | 💾 {mb_size:.2f} MB</span>"

    st.markdown(
        f"### Scansione {stats_str}",
        unsafe_allow_html=True,
    )

    if not img_obj:
        st.error("❌ Immagine non trovata.")
        return None, p_stat or {}

    # Get current adjustments
    adjustments = StudioState.get_image_adjustments(doc_id, current_page)

    # Apply adjustments
    display_img = ImageProcessor.apply_adjustments(
        img_obj.copy(), brightness=adjustments["brightness"], contrast=adjustments["contrast"]
    )

    # Check if in crop mode
    crop_mode = StudioState.get(StudioState.CROP_MODE, False)

    if crop_mode:
        _render_crop_interface(display_img, doc_id, library, current_page, paths)
    else:
        # Normal viewer
        interactive_viewer(display_img, zoom_percent=100)

    # Toolbar compatta con icone
    tool_col1, tool_col2, tool_col3 = st.columns([1, 1, 3])
    
    with tool_col1:
        with st.popover("🎨 Regolazioni"):
            _render_image_adjustments(doc_id, current_page, adjustments)
    
    with tool_col2:
        with st.popover("✂️ Ritaglio"):
            _render_crop_tools(doc_id, current_page, crop_mode)

    return img_obj, p_stat or {}


def _render_image_adjustments(doc_id: str, current_page: int, current_adjustments: dict):
    """Render sliders for brightness and contrast adjustments."""

    col1, col2 = st.columns(2)

    with col1:
        brightness = st.slider(
            "☀️ Luminosità",
            min_value=0.0,
            max_value=2.0,
            value=current_adjustments["brightness"],
            step=0.1,
            key=f"brightness_{doc_id}_{current_page}",
            help="Regola la luminosità dell'immagine",
        )

    with col2:
        contrast = st.slider(
            "🎭 Contrasto",
            min_value=0.0,
            max_value=2.0,
            value=current_adjustments["contrast"],
            step=0.1,
            key=f"contrast_{doc_id}_{current_page}",
            help="Regola il contrasto dell'immagine",
        )

    # Save adjustments to state
    StudioState.set_image_adjustments(doc_id, current_page, brightness, contrast)

    # Reset button
    if st.button("🔄 Ripristina Valori Originali", use_container_width=True):
        StudioState.reset_image_adjustments(doc_id, current_page)
        st.rerun()

    st.caption("💡 Le regolazioni sono applicate solo alla visualizzazione e non modificano l'immagine originale.")


def _render_crop_tools(doc_id: str, current_page: int, crop_mode: bool):
    """Render cropping tools interface."""

    if not crop_mode:
        if st.button("✂️ Attiva Modalità Ritaglio", use_container_width=True, type="primary"):
            StudioState.set(StudioState.CROP_MODE, True)
            st.rerun()
        st.caption("Attiva la modalità ritaglio per selezionare un'area dell'immagine e salvarla.")
    else:
        if st.button("❌ Disattiva Modalità Ritaglio", use_container_width=True):
            StudioState.set(StudioState.CROP_MODE, False)
            st.rerun()
        st.info("🔧 Modalità ritaglio attiva. Seleziona un'area nell'immagine sopra.")

        # Show saved crops for this page
        _render_saved_crops(doc_id, current_page)


def _render_crop_interface(display_img: PILImage.Image, doc_id: str, library: str, current_page: int, paths: dict):
    """Render the cropping interface using streamlit-cropper."""

    try:
        from streamlit_cropper import st_cropper

        # Cropper component
        cropped_img = st_cropper(
            display_img,
            realtime_update=True,
            box_color="#FF4B4B",
            aspect_ratio=None,  # Free aspect ratio
            key=f"cropper_{doc_id}_{current_page}",
        )

        # Crop save interface
        st.markdown("---")

        col1, col2 = st.columns([3, 1])

        with col1:
            crop_label = st.text_input(
                "📝 Etichetta",
                placeholder="Es: Iniziale decorata, Nota marginale...",
                key=f"crop_label_{doc_id}_{current_page}",
            )

        crop_tags = st.text_input(
            "🏷️ Tags (separati da virgola)",
            placeholder="Es: decorazione, miniatura, rubrica",
            key=f"crop_tags_{doc_id}_{current_page}",
        )

        with col2:
            if st.button("💾 Salva Ritaglio", use_container_width=True, type="primary"):
                if not crop_label.strip():
                    st.error("Inserisci un'etichetta per il ritaglio!")
                else:
                    _save_crop(cropped_img, doc_id, library, current_page, crop_label, crop_tags, paths)

    except ImportError:
        st.error("📦 streamlit-cropper non installato. Installa con: `pip install streamlit-cropper`")
        st.info("Per ora puoi usare le altre funzionalità dello Studio.")


def _save_crop(
    cropped_img: PILImage.Image, doc_id: str, library: str, current_page: int, label: str, tags: str, paths: dict
):
    """Save a cropped image to the database and disk."""

    try:
        # Create crops directory
        crops_dir = Path(paths["root"]) / "crops"
        crops_dir.mkdir(exist_ok=True)

        # Generate filename
        timestamp = st.session_state.get("_last_crop_id", 0) + 1
        st.session_state["_last_crop_id"] = timestamp

        crop_filename = f"crop_p{current_page:04d}_{timestamp:04d}.png"
        crop_path = crops_dir / crop_filename

        # Save image to disk
        cropped_img.save(str(crop_path), "PNG")

        # Convert to bytes for database
        img_bytes = ImageProcessor.save_crop_to_bytes(cropped_img)

        # Get crop coordinates (if available from cropper state)
        # For now, we'll use placeholder coordinates
        coordinates = [0, 0, cropped_img.width, cropped_img.height]

        # Save to database
        vault = VaultManager()
        snippet_id = vault.save_snippet(
            manuscript_id=doc_id,
            page_index=current_page - 1,  # 0-indexed in DB
            label=label,
            coordinates=coordinates,
            image_bytes=img_bytes,
            tags=tags.strip(),
            image_path=str(crop_path),
        )

        toast(f"✅ Ritaglio salvato! ID: {snippet_id}", icon="💾")
        st.success(f"Ritaglio salvato: {crop_path.name}")

        # Clear form inputs
        st.session_state[f"crop_label_{doc_id}_{current_page}"] = ""
        st.session_state[f"crop_tags_{doc_id}_{current_page}"] = ""

    except Exception as e:
        st.error(f"Errore nel salvataggio: {e}")


def _render_saved_crops(doc_id: str, current_page: int):
    """Display saved crops for the current page."""

    try:
        vault = VaultManager()
        snippets = vault.get_snippets(doc_id, page_index=current_page - 1)

        if not snippets:
            st.caption("Nessun ritaglio salvato per questa pagina.")
            return

        st.markdown(f"**Ritagli Salvati ({len(snippets)})**")

        for snippet in snippets:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    st.markdown(f"**{snippet['label']}**")
                    if snippet["tags"]:
                        tags_display = " · ".join([f"#{t.strip()}" for t in snippet["tags"].split(",")])
                        st.caption(tags_display)

                with col2:
                    st.caption(f"🕒 {snippet['created_at']}")

                with col3:
                    if st.button("🗑️", key=f"del_crop_{snippet['id']}", help="Elimina ritaglio"):
                        vault.delete_snippet(snippet["id"])
                        # Delete file if exists
                        if snippet["image_path"] and os.path.exists(snippet["image_path"]):
                            try:
                                os.remove(snippet["image_path"])
                            except:
                                pass
                        toast("Ritaglio eliminato", icon="🗑️")
                        st.rerun()

                st.divider()

    except Exception as e:
        st.error(f"Errore caricamento ritagli: {e}")
