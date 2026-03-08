"""Security tests for scan optimization symlink path traversal vulnerabilities."""

import json

import pytest
from PIL import Image

from universal_iiif_core.config_manager import get_config_manager
from universal_iiif_core.services.scan_optimize import optimize_local_scans
from universal_iiif_core.services.storage.vault_manager import VaultManager


@pytest.fixture
def setup_doc_structure(tmp_path):
    """Setup a valid document structure for testing."""
    cm = get_config_manager()
    old_downloads = cm.get_downloads_dir()

    downloads = tmp_path / "downloads"
    downloads.mkdir(exist_ok=True)
    cm.set_downloads_dir(str(downloads))

    library = "TestLibrary"
    doc_id = "TestDoc"
    doc_root = downloads / library / doc_id
    scans_dir = doc_root / "scans"
    data_dir = doc_root / "data"
    thumb_dir = data_dir / "thumbnails"

    scans_dir.mkdir(parents=True)
    data_dir.mkdir(parents=True)
    thumb_dir.mkdir(parents=True)

    # Create a valid scan image
    Image.new("RGB", (800, 1200), (255, 255, 255)).save(scans_dir / "pag_0000.jpg", format="JPEG", quality=95)

    # Create manifest
    manifest = {"items": [{"id": "https://example.org/canvas/1"}]}
    (data_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    # Register in vault
    VaultManager().upsert_manuscript(
        doc_id, library=library, local_path=str(doc_root), status="saved", asset_state="saved"
    )

    yield {
        "downloads": downloads,
        "doc_root": doc_root,
        "scans_dir": scans_dir,
        "data_dir": data_dir,
        "thumb_dir": thumb_dir,
        "library": library,
        "doc_id": doc_id,
    }

    cm.set_downloads_dir(str(old_downloads))


def test_optimize_rejects_symlink_scan_to_external_file(setup_doc_structure, tmp_path):
    """Optimization must not follow symlinks pointing outside downloads directory."""
    ctx = setup_doc_structure
    scans_dir = ctx["scans_dir"]

    # Create a sensitive file outside downloads
    external_dir = tmp_path / "external"
    external_dir.mkdir()
    sensitive_file = external_dir / "sensitive.jpg"
    Image.new("RGB", (100, 100), (255, 0, 0)).save(sensitive_file, format="JPEG")
    original_content = sensitive_file.read_bytes()

    # Create symlink in scans directory pointing to external file
    symlink_scan = scans_dir / "pag_0001.jpg"
    symlink_scan.symlink_to(sensitive_file)

    # Run optimization
    result = optimize_local_scans(ctx["doc_id"], ctx["library"])

    # Verify the external file was NOT modified
    assert sensitive_file.read_bytes() == original_content, "External file should not be modified"

    # Verify optimization completed (for legitimate file pag_0000.jpg)
    assert "meta" in result
    assert result["meta"]["optimized_pages"] >= 0


def test_optimize_rejects_symlink_scans_dir_to_external_dir(setup_doc_structure, tmp_path):
    """Optimization must not follow a symlinked scans directory."""
    ctx = setup_doc_structure
    scans_dir = ctx["scans_dir"]

    # Create external directory with files
    external_dir = tmp_path / "external_scans"
    external_dir.mkdir()
    external_file = external_dir / "pag_0001.jpg"
    Image.new("RGB", (100, 100), (255, 0, 0)).save(external_file, format="JPEG")
    original_content = external_file.read_bytes()

    # Remove real scans dir and create symlink to external dir
    for f in scans_dir.glob("*"):
        f.unlink()
    scans_dir.rmdir()
    scans_dir.symlink_to(external_dir)

    # Run optimization - should fail validation or skip external files
    optimize_local_scans(ctx["doc_id"], ctx["library"])

    # Verify external files were NOT modified
    assert external_file.read_bytes() == original_content, "External file should not be modified"


def test_optimize_rejects_symlink_thumbnail_dir_to_external_dir(setup_doc_structure, tmp_path):
    """Thumbnail cleanup must not follow symlinks pointing outside downloads."""
    ctx = setup_doc_structure
    thumb_dir = ctx["thumb_dir"]

    # Create external directory with files
    external_dir = tmp_path / "external_thumbs"
    external_dir.mkdir()
    external_thumb = external_dir / "thumb_001.jpg"
    Image.new("RGB", (50, 50), (0, 255, 0)).save(external_thumb, format="JPEG")

    # Remove real thumb dir and create symlink to external dir
    for f in thumb_dir.glob("*"):
        f.unlink()
    thumb_dir.rmdir()
    thumb_dir.symlink_to(external_dir)

    # Run optimization
    optimize_local_scans(ctx["doc_id"], ctx["library"])

    # Verify external thumbnail was NOT deleted
    assert external_thumb.exists(), "External thumbnail should not be deleted"


def test_optimize_rejects_symlink_individual_thumbnail(setup_doc_structure, tmp_path):
    """Thumbnail cleanup must not delete symlinked thumbnails pointing outside downloads."""
    ctx = setup_doc_structure
    thumb_dir = ctx["thumb_dir"]

    # Create external file
    external_dir = tmp_path / "external"
    external_dir.mkdir()
    external_file = external_dir / "important.jpg"
    Image.new("RGB", (50, 50), (0, 0, 255)).save(external_file, format="JPEG")

    # Create symlink in thumbnail dir
    symlink_thumb = thumb_dir / "thumb_external.jpg"
    symlink_thumb.symlink_to(external_file)

    # Run optimization
    optimize_local_scans(ctx["doc_id"], ctx["library"])

    # Verify external file was NOT deleted
    assert external_file.exists(), "External file should not be deleted via symlink"


def test_optimize_allows_legitimate_files_after_symlink_rejection(setup_doc_structure):
    """After rejecting symlinks, legitimate files should still be processed."""
    ctx = setup_doc_structure
    scans_dir = ctx["scans_dir"]

    # Add another legitimate scan
    legit_scan = scans_dir / "pag_0002.jpg"
    Image.new("RGB", (800, 1200), (255, 255, 255)).save(legit_scan, format="JPEG", quality=95)

    # Run optimization
    result = optimize_local_scans(ctx["doc_id"], ctx["library"])

    # Should have processed at least the legitimate files
    assert "meta" in result
    assert result["meta"]["optimized_pages"] >= 1, "Should optimize legitimate scans"
    assert result["meta"].get("errors", 0) == 0, "Should not have errors for legitimate files"
