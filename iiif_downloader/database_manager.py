import sqlite3
from pathlib import Path

import fitz  # PyMuPDF


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

        # Table for snippets (image crops)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manuscript_id TEXT,
                page_index INTEGER,
                label TEXT,
                tags TEXT,  -- Comma-separated tags
                coordinates TEXT,  -- Saved as JSON string "[x0, y0, x1, y1]"
                image_path TEXT,  -- Path to saved crop image
                image_data BLOB,  -- Optional: raw image bytes
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (manuscript_id) REFERENCES manuscripts (id)
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
        manuscript_id: str,
        page_index: int,
        label: str,
        coordinates: list,
        image_bytes: bytes,
        tags: str = "",
        image_path: str = None,
    ):
        """
        Saves the snippet to the database.

        Args:
            manuscript_id: ID of the manuscript
            page_index: Page number (0-indexed)
            label: Description/label for the snippet
            coordinates: List of [x0, y0, x1, y1]
            image_bytes: Raw PNG image bytes
            tags: Comma-separated tags
            image_path: Optional path to saved image file
        """
        import json

        self.register_manuscript(manuscript_id)

        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO snippets (manuscript_id, page_index, label, tags, coordinates, image_path, image_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (manuscript_id, page_index, label, tags, json.dumps(coordinates), image_path, image_bytes),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_snippets(self, manuscript_id: str, page_index: int = None):
        """
        Retrieve snippets for a manuscript, optionally filtered by page.

        Args:
            manuscript_id: ID of the manuscript
            page_index: Optional page number to filter (0-indexed)

        Returns:
            List of snippet dictionaries
        """
        import json

        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            if page_index is not None:
                cursor.execute(
                    """
                    SELECT id, manuscript_id, page_index, label, tags, coordinates, 
                           image_path, created_at
                    FROM snippets
                    WHERE manuscript_id = ? AND page_index = ?
                    ORDER BY created_at DESC
                """,
                    (manuscript_id, page_index),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, manuscript_id, page_index, label, tags, coordinates, 
                           image_path, created_at
                    FROM snippets
                    WHERE manuscript_id = ?
                    ORDER BY page_index, created_at DESC
                """,
                    (manuscript_id,),
                )

            rows = cursor.fetchall()
            snippets = []
            for row in rows:
                snippets.append(
                    {
                        "id": row[0],
                        "manuscript_id": row[1],
                        "page_index": row[2],
                        "label": row[3],
                        "tags": row[4],
                        "coordinates": json.loads(row[5]) if row[5] else [],
                        "image_path": row[6],
                        "created_at": row[7],
                    }
                )
            return snippets
        finally:
            conn.close()

    def delete_snippet(self, snippet_id: int):
        """Delete a snippet by ID."""
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM snippets WHERE id = ?", (snippet_id,))
            conn.commit()
        finally:
            conn.close()
