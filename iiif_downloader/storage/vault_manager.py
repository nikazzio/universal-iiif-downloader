import sqlite3
from pathlib import Path

import fitz  # PyMuPDF

from iiif_downloader.logger import get_logger

logger = get_logger(__name__)


class VaultManager:
    def __init__(self, db_path: str = "data/vault.db"):
        self.db_path = Path(db_path)
        self._ensure_db_dir()
        self._init_db()

    def _ensure_db_dir(self):
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()

        # Table for manuscripts (simple reference)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS manuscripts (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table for snippets (image crops) - NUOVA VERSIONE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ms_name TEXT NOT NULL,
                page_num INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                category TEXT,
                transcription TEXT,
                notes TEXT,
                coords_json TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def register_manuscript(self, manuscript_id: str, title: str = None):
        """Ensures manuscript exists in DB."""
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT OR IGNORE INTO manuscripts (id, title) VALUES (?, ?)", (manuscript_id, title))
            conn.commit()
        finally:
            conn.close()

    def extract_image_snippet(self, image_path: str, coordinates: tuple) -> bytes:
        """
        Extracts a crop from an image using PyMuPDF (fitz).
        coordinates: (x0, y0, x1, y1) relative to the original image size.
        """
        try:
            # We assume image_path is a valid image file.
            # PyMuPDF can open images as simple documents.
            with fitz.open(image_path) as doc:
                page = doc.load_page(0)  # Images are 1-page documents
                rect = fitz.Rect(coordinates)

                # Pixmap of the cropped area
                pix = page.get_pixmap(clip=rect)

                # Convert to PNG bytes
                return pix.tobytes("png")
        except Exception as e:
            print(f"Error extracting snippet with fitz: {e}")
            return None

    def save_snippet(
        self,
        ms_name: str,
        page_num: int,
        image_path: str,
        category: str = None,
        transcription: str = None,
        notes: str = None,
        coords: list = None,
    ):
        """
        Saves the snippet to the database.

        Args:
            ms_name: Nome del manoscritto
            page_num: Numero pagina (1-indexed)
            image_path: Path del file immagine salvato
            category: Categoria (Capolettera, Glossa, etc)
            transcription: Trascrizione rapida
            notes: Note/commenti
            coords: Coordinate [x, y, width, height]
        """
        import json

        logger.debug(f"💾 SAVE_SNIPPET - ms_name='{ms_name}', page_num={page_num}, category='{category}'")

        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            coords_json = json.dumps(coords) if coords else None
            cursor.execute(
                """
                INSERT INTO snippets (ms_name, page_num, image_path, category, transcription, notes, coords_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (ms_name, page_num, image_path, category, transcription, notes, coords_json),
            )
            conn.commit()
            snippet_id = cursor.lastrowid
            logger.info(f"✅ Snippet ID {snippet_id} salvato: {category} - p.{page_num}")
            
            return snippet_id
        finally:
            conn.close()

    def get_snippets(self, ms_name: str, page_num: int = None):
        """
        Retrieve snippets for a manuscript, optionally filtered by page.

        Args:
            ms_name: Nome del manoscritto
            page_num: Numero pagina opzionale (1-indexed)

        Returns:
            List of snippet dictionaries
        """
        import json

        logger.debug(f"🔍 GET_SNIPPETS - ms_name='{ms_name}', page_num={page_num}")

        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            if page_num is not None:
                query = """
                    SELECT id, ms_name, page_num, image_path, category, transcription, 
                           notes, coords_json, timestamp
                    FROM snippets
                    WHERE ms_name = ? AND page_num = ?
                    ORDER BY timestamp DESC
                """
                params = (ms_name, page_num)
                cursor.execute(query, params)
            else:
                query = """
                    SELECT id, ms_name, page_num, image_path, category, transcription, 
                           notes, coords_json, timestamp
                    FROM snippets
                    WHERE ms_name = ?
                    ORDER BY page_num, timestamp DESC
                """
                params = (ms_name,)
                cursor.execute(query, params)

            rows = cursor.fetchall()
            logger.debug(f"Query eseguita: trovati {len(rows)} snippet")
            snippets = []
            for row in rows:
                snippets.append(
                    {
                        "id": row[0],
                        "ms_name": row[1],
                        "page_num": row[2],
                        "image_path": row[3],
                        "category": row[4],
                        "transcription": row[5],
                        "notes": row[6],
                        "coords_json": json.loads(row[7]) if row[7] else None,
                        "timestamp": row[8],
                    }
                )
            return snippets
        finally:
            conn.close()

    def delete_snippet(self, snippet_id: int):
        """Delete a snippet by ID and remove the physical file."""
        import os
        
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            # Get image path before deleting
            cursor.execute("SELECT image_path FROM snippets WHERE id = ?", (snippet_id,))
            result = cursor.fetchone()
            
            if result and result[0]:
                image_path = Path(result[0])
                if image_path.exists():
                    os.remove(image_path)
            
            # Delete from DB
            cursor.execute("DELETE FROM snippets WHERE id = ?", (snippet_id,))
            conn.commit()
        finally:
            conn.close()
