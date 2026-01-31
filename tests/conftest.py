"""Test bootstrap.

Ensures the project root is importable and handles automatic DB cleanup.
"""

from __future__ import annotations

import contextlib
import logging
import sys
from pathlib import Path

import pytest

# Add SRC to path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SRC = ROOT / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from universal_iiif_core.services.storage.vault_manager import VaultManager


@pytest.fixture(autouse=True)
def _auto_cleanup_database():
    """Autouse fixture che intercetta la creazione di Job e Manoscritti.

    E li elimina dal DB alla fine di ogni test.
    """
    created_jobs = set()
    created_manuscripts = set()

    # 1. Monkeypatch create_download_job
    orig_create_job = VaultManager.create_download_job

    def _wrapped_create_job(self, job_id, *a, **kw):
        created_jobs.add(job_id)
        return orig_create_job(self, job_id, *a, **kw)

    VaultManager.create_download_job = _wrapped_create_job

    # 2. Monkeypatch upsert_manuscript (per pulire i manoscritti)
    orig_upsert_ms = VaultManager.upsert_manuscript

    def _wrapped_upsert_ms(self, manuscript_id, **kw):
        created_manuscripts.add(manuscript_id)
        return orig_upsert_ms(self, manuscript_id, **kw)

    VaultManager.upsert_manuscript = _wrapped_upsert_ms

    # Esegui il test
    yield

    # 3. Teardown: Pulizia
    try:
        vm = VaultManager()
        # Se stiamo usando un DB reale, procediamo alla pulizia
        # (Se il test usa un DB mockato, questo potrebbe fallire ma lo ignoriamo)
        conn = vm._get_conn()
        c = conn.cursor()

        # Elimina Jobs
        for jid in created_jobs:
            with contextlib.suppress(Exception):
                c.execute("DELETE FROM download_jobs WHERE job_id = ?", (jid,))

        # Elimina Manoscritti (e a cascata gli snippet se configurato, ma facciamolo a mano per sicurezza)
        for mid in created_manuscripts:
            with contextlib.suppress(Exception):
                # Pulizia Snippets collegati
                c.execute("DELETE FROM snippets WHERE manuscript_id = ?", (mid,))
                # Pulizia Manoscritto
                c.execute("DELETE FROM manuscripts WHERE id = ?", (mid,))

        conn.commit()
        conn.close()

    except Exception as exc:
        logging.debug("Teardown DB cleanup warning (ignored): %s", exc)
    finally:
        # Ripristina funzioni originali
        VaultManager.create_download_job = orig_create_job
        VaultManager.upsert_manuscript = orig_upsert_ms
