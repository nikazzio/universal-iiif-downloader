from pathlib import Path

from universal_iiif_core.logic import downloader_runtime


class _Logger:
    def debug(self, *_args, **_kwargs):
        return None


class _Vault:
    def __init__(self):
        self.calls: list[dict] = []

    def upsert_manuscript(self, _ms_id, **kwargs):
        self.calls.append(kwargs)


class _DummyDownloader:
    def __init__(self, root: Path, *, expected_total: int):
        self.scans_dir = root / "scans"
        self.temp_dir = root / "temp"
        self.pdf_dir = root / "pdf"
        self.scans_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.overwrite_existing_scans = False
        self.expected_total_canvases = expected_total
        self.total_canvases = expected_total
        self.ms_id = "DOC_STAGE"
        self.logger = _Logger()
        self.vault = _Vault()


def test_finalize_downloads_keeps_temp_files_when_incomplete(tmp_path):
    """Incomplete downloads must keep staged images in temp dir."""
    dummy = _DummyDownloader(tmp_path, expected_total=3)
    staged = dummy.temp_dir / "pag_0000.jpg"
    staged.write_bytes(b"temp-jpg")

    out = downloader_runtime._finalize_downloads(dummy, [str(staged)])
    assert out == []
    assert staged.exists()
    assert not (dummy.scans_dir / "pag_0000.jpg").exists()


def test_finalize_downloads_promotes_temp_files_when_complete(tmp_path):
    """Once all pages are present, staged files should move to scans and temp cleaned."""
    dummy = _DummyDownloader(tmp_path, expected_total=2)
    p0 = dummy.temp_dir / "pag_0000.jpg"
    p1 = dummy.temp_dir / "pag_0001.jpg"
    p0.write_bytes(b"temp-0")
    p1.write_bytes(b"temp-1")

    out = downloader_runtime._finalize_downloads(dummy, [str(p0), str(p1)])
    assert len(out) == 2
    assert (dummy.scans_dir / "pag_0000.jpg").exists()
    assert (dummy.scans_dir / "pag_0001.jpg").exists()
    assert not dummy.temp_dir.exists()


def test_sync_asset_state_counts_known_pages_from_scans_and_temp(tmp_path):
    """Asset sync should consider both scans and staged pages."""
    dummy = _DummyDownloader(tmp_path, expected_total=5)
    (dummy.scans_dir / "pag_0000.jpg").write_bytes(b"scan-0")
    (dummy.temp_dir / "pag_0001.jpg").write_bytes(b"temp-1")
    (dummy.temp_dir / "pag_0002.jpg").write_bytes(b"temp-2")

    downloader_runtime._sync_asset_state(dummy, total_expected=5)

    payload = dummy.vault.calls[-1]
    assert payload["asset_state"] == "partial"
    assert int(payload["downloaded_canvases"]) == 3
    assert payload["missing_pages_json"] == "[4, 5]"


def test_finalize_downloads_does_not_promote_unvalidated_temp_files(tmp_path):
    """Only files present in the validated list may be promoted into scans."""
    dummy = _DummyDownloader(tmp_path, expected_total=1)
    validated = dummy.temp_dir / "pag_0000.jpg"
    stale = dummy.temp_dir / "pag_0001.jpg"
    validated.write_bytes(b"ok")
    stale.write_bytes(b"stale")

    out = downloader_runtime._finalize_downloads(dummy, [str(validated)])
    assert len(out) == 1
    assert (dummy.scans_dir / "pag_0000.jpg").exists()
    assert not (dummy.scans_dir / "pag_0001.jpg").exists()


class _RunDummy:
    def __init__(self):
        self.progress_callback = None
        self.ocr_model = None
        self.finalize_calls: list[list[str]] = []
        self.clean_cache = False

    def extract_metadata(self):
        return None

    def get_canvases(self):
        return [{"id": "c1"}, {"id": "c2"}]

    def _build_canvas_plan(self, canvases, _target_pages):
        return set(), [(idx, canvas) for idx, canvas in enumerate(canvases)]

    def _mark_downloading_state(self, _total_pages):
        return None

    def _maybe_run_native_pdf(self, _native_pdf_url, _selected_pages, _progress_callback):
        return False

    def get_pdf_url(self):
        return None

    def _download_canvases(self, _canvas_plan, progress_callback=None, should_cancel=None, total_for_progress=0):
        _ = progress_callback
        _ = should_cancel
        _ = total_for_progress
        return (["staged/pag_0000.jpg", "staged/pag_0001.jpg"], [])

    def _store_page_stats(self, _page_stats):
        return None

    def _finalize_downloads(self, valid):
        self.finalize_calls.append(list(valid))
        return []

    def _should_create_pdf_from_images(self):
        return False

    def _sync_asset_state(self, _total_pages):
        return None


def test_run_calls_finalize_even_when_stop_requested_late():
    """Late stop requests must not skip finalization decision."""
    dummy = _RunDummy()
    downloader_runtime.run(dummy, should_cancel=lambda: True)
    assert dummy.finalize_calls == [["staged/pag_0000.jpg", "staged/pag_0001.jpg"]]
