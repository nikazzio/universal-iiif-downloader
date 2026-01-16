from pathlib import Path
from pdf2image import convert_from_path, convert_from_bytes
import logging
from pathlib import Path
from pdf2image import convert_from_path, convert_from_bytes
from PIL import Image as PILImage
import logging

logger = logging.getLogger(__name__)

def load_pdf_page(pdf_source, page_idx, dpi=300):
    """
    Load a single page from a PDF source (Path or bytes) and convert to a PIL Image.
    Returns (Image, error_message).
    """
    try:
        if isinstance(pdf_source, (str, Path)):
            pages = convert_from_path(pdf_source, first_page=page_idx, last_page=page_idx, dpi=dpi)
        else:
            pages = convert_from_bytes(pdf_source, first_page=page_idx, last_page=page_idx, dpi=dpi)
        
        if not pages:
            return None, f"Pagina {page_idx} non trovata nel PDF."
        
        return pages[0], None
    except Exception as e:
        logger.error(f"Error loading PDF page: {e}")
        return None, str(e)

def generate_pdf_from_images(image_paths, output_path):
    """
    Combine a list of image paths into a single PDF.
    """
    try:
        images = []
        for p in image_paths:
            if Path(p).exists():
                img = PILImage.open(p)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                images.append(img)
        
        if images:
            images[0].save(output_path, save_all=True, append_images=images[1:])
            return True, f"PDF creato con successo: {output_path}"
        else:
            return False, "Nessuna immagine valida trovata."
    except Exception as e:
        logger.error(f"Error creating PDF: {e}")
        return False, str(e)
