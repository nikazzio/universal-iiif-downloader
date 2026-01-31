"""Helper utilities for discovery route handlers.

These keep the request handlers small and focused so ruff's
complexity checks remain satisfied.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import unquote

from universal_iiif_core.config_manager import get_config_manager
from universal_iiif_core.jobs import job_manager
from universal_iiif_core.logger import get_logger
from universal_iiif_core.logic.downloader import IIIFDownloader
from universal_iiif_core.resolvers.parsers import IIIFManifestParser
from universal_iiif_core.services.storage.vault_manager import VaultManager
from universal_iiif_core.utils import generate_folder_name, generate_job_id, get_json

logger = get_logger(__name__)


def analyze_manifest(manifest_url: str) -> dict[str, Any]:
    """Download and extract simple preview data from a manifest URL.

    Returns a dict with keys: label, description, pages.
    Raises exceptions on network / parsing errors so callers can handle them.
    """
    manifest_data = get_json(manifest_url)
    if not manifest_data:
        raise ValueError("Manifest vuoto o irraggiungibile")

    # Usa il parser centralizzato per metadati robusti
    parser = IIIFManifestParser()
    result = parser.parse_manifest(manifest_data, manifest_url=manifest_url)

    # Calcolo pagine manuale se il parser non lo espone direttamente
    # (IIIF v2 sequences o IIIF v3 items)
    canvases = []
    if "sequences" in manifest_data:
        seq = manifest_data["sequences"][0] if manifest_data["sequences"] else {}
        canvases = seq.get("canvases", [])
    elif "items" in manifest_data:
        canvases = manifest_data["items"]

    return {
        "label": result.get("title", "Senza Titolo"),
        "description": result.get("description", ""),
        "pages": len(canvases),
        "thumbnail": result.get("thumbnail"),
    }


def start_downloader_thread(manifest_url: str, doc_id: str, library: str) -> str:
    """Start a background IIIF download and persist progress into the DB.

    The function returns a stable download_id (HASH) which can be used by the UI
    to poll the `download_jobs` table without encoding issues.
    """
    manifest_url = unquote(manifest_url)
    doc_id = unquote(doc_id)
    library = unquote(library)

    # 1. GENERA ID ROBUSTO (Hash) per evitare 404 sulle API
    job_id = generate_job_id(library, manifest_url)

    # 2. GENERA NOME CARTELLA PULITO per il filesystem
    folder_name = generate_folder_name(library, doc_id)

    logger.info(f"Starting Download: JobID={job_id} | Folder='{folder_name}'")

    job_manager.submit_job(
        _download_task,
        kwargs={
            "manifest_url": manifest_url,
            "doc_id": doc_id,
            "library": library,
            "db_job_id": job_id,  # Chiave per API/DB
            "folder_name": folder_name,  # Nome cartella fisica
        },
        job_type="download",
    )

    return job_id


def _download_task(progress_callback=None, should_cancel=None, **kwargs):
    """Worker function executed in thread."""
    manifest_url = str(kwargs.get("manifest_url") or "")
    doc_id = str(kwargs.get("doc_id") or "")
    library = str(kwargs.get("library") or "")
    db_job_id = str(kwargs.get("db_job_id") or "")
    folder_name = kwargs.get("folder_name")

    # Thread-local DB manager for safety
    vault = VaultManager()

    # Register the job in DB using the SAFE ID
    vault.create_download_job(db_job_id, doc_id, library, manifest_url)

    # Track last seen values for more informative error reporting
    last = {"current": 0, "total": 0}

    def db_progress_hook(current: int, total: int):
        """Update DB only when values change to reduce write load."""
        if current != last["current"] or total != last["total"]:
            # Usa db_job_id (hash), non l'URL grezzo
            vault.update_download_job(job_id=db_job_id, current=current, total=total, status="running")
            last["current"] = current
            last["total"] = total

        # Call the memory-based job manager callback if provided
        if progress_callback:
            progress_callback(current, total)

    try:
        # Explicitly use configured downloads dir
        cm = get_config_manager()
        downloads_dir = cm.get_downloads_dir()

        downloader = IIIFDownloader(
            manifest_url,
            output_dir=downloads_dir,
            library=library,
            output_folder_name=folder_name,
            progress_callback=db_progress_hook,
            job_id=db_job_id,
        )

        # Pass DB hook and cancellation checker to the runtime `run` call
        downloader.run(should_cancel=should_cancel)

        # Mark completed
        vault.update_download_job(job_id=db_job_id, current=last["current"], total=last["total"], status="completed")

        # Register manuscript in the main table
        # Ora usiamo il titolo estratto dal manifest reale
        vault.upsert_manuscript(doc_id, library=library, title=downloader.label, local_path=str(downloader.doc_dir))

    except Exception as exc:  # pragma: no cover - runtime safety
        logger.error(f"Download failed for {doc_id}: {exc}", exc_info=True)
        vault.update_download_job(
            job_id=db_job_id, current=last["current"], total=last["total"], status="error", error=str(exc)
        )
