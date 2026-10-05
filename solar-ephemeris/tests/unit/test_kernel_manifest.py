"""Kernel identity manifest: pinned values + verification failures.

The manifest defines which binary IS the reference (requirement 1). Tests
cover: exact pinned values (NAIF MD5, pinned SHA-256, measured coverage,
spkobj body list), hash verification against a temp file, and the
no-silent-substitution guards (de441/de442 filenames and reference names
rejected at construction).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from solar_ephemeris.ephemeris.kernel_manifest import (
    DE440_KERNEL_FILENAMES,
    DE440S_MANIFEST,
    KERNEL_DIR_ENV,
    KernelManifest,
    default_kernel_path,
    verify_kernel,
)
from solar_ephemeris.ephemeris.types import KernelIntegrityError


def test_pinned_manifest_values() -> None:
    m = DE440S_MANIFEST
    assert m.reference_name == "JPL DE440"
    assert m.filename == "de440s.bsp"
    assert m.size_bytes == 32_726_016
    # NAIF-published MD5 (aa_checksums.txt), verified on retrieval 2026-10-03.
    assert m.md5 == "3917ee56769db332790c751e2168843d"
    assert m.sha256 == (
        "c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2"
    )
    assert "naif.jpl.nasa.gov" in m.url
    assert m.retrieval_date == "2026-10-03"
    # Measured spkcov window == NAIF aa_summaries.txt (1849-12-26 → 2150-01-22).
    assert m.coverage_et == (-4_734_072_000.0, 4_735_368_000.0)
    assert m.body_ids == (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 199, 299, 301, 399)
    assert "10.3847/1538-3881/abd414" in m.source_citation


def test_verify_accepts_matching_file(tmp_path: Path) -> None:
    import hashlib

    payload = b"reference-kernel-stand-in" * 1000
    kernel = tmp_path / "de440s.bsp"
    kernel.write_bytes(payload)
    manifest = KernelManifest(
        filename="de440s.bsp",
        url="https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp",
        size_bytes=len(payload),
        md5=hashlib.md5(payload).hexdigest(),
        sha256=hashlib.sha256(payload).hexdigest(),
        retrieval_date="2026-10-03",
        reference_name="JPL DE440",
        reference_version="test",
        source_citation="test",
        coverage_et=(-4_734_072_000.0, 4_735_368_000.0),
        body_ids=(10, 399),
    )
    verify_kernel(kernel, manifest)  # no exception = pass


def test_verify_missing_file_reports_retrieval_url(tmp_path: Path) -> None:
    with pytest.raises(KernelIntegrityError) as exc:
        verify_kernel(tmp_path / "de440s.bsp", DE440S_MANIFEST)
    assert DE440S_MANIFEST.url in str(exc.value)
    assert "not found" in str(exc.value)


def test_verify_size_mismatch_first(tmp_path: Path) -> None:
    kernel = tmp_path / "de440s.bsp"
    kernel.write_bytes(b"x" * 100)
    manifest = KernelManifest(
        filename="de440s.bsp",
        url=DE440S_MANIFEST.url,
        size_bytes=999,  # differs from 100-byte file
        md5="0" * 32,
        sha256="0" * 64,
        retrieval_date="2026-10-03",
        reference_name="JPL DE440",
        reference_version="test",
        source_citation="test",
        coverage_et=(-1.0, 1.0),
        body_ids=(10,),
    )
    with pytest.raises(KernelIntegrityError) as exc:
        verify_kernel(kernel, manifest)
    assert "size mismatch" in str(exc.value)


def test_verify_same_size_tamper_fails_md5(tmp_path: Path) -> None:
    import hashlib

    payload = bytearray(b"original-bytes-for-tamper-test" * 50)
    kernel = tmp_path / "de440s.bsp"
    kernel.write_bytes(bytes(payload))
    manifest = KernelManifest(
        filename="de440s.bsp",
        url=DE440S_MANIFEST.url,
        size_bytes=len(payload),
        md5=hashlib.md5(payload).hexdigest(),
        sha256=hashlib.sha256(payload).hexdigest(),
        retrieval_date="2026-10-03",
        reference_name="JPL DE440",
        reference_version="test",
        source_citation="test",
        coverage_et=(-1.0, 1.0),
        body_ids=(10,),
    )
    payload[0] ^= 0xFF  # flip one byte: size unchanged, hashes change
    kernel.write_bytes(bytes(payload))
    with pytest.raises(KernelIntegrityError) as exc:
        verify_kernel(kernel, manifest)
    assert "MD5 mismatch" in str(exc.value)


def test_verify_wrong_pinned_sha256_fails(tmp_path: Path) -> None:
    import hashlib

    payload = b"content"
    kernel = tmp_path / "de440s.bsp"
    kernel.write_bytes(payload)
    manifest = KernelManifest(
        filename="de440s.bsp",
        url=DE440S_MANIFEST.url,
        size_bytes=len(payload),
        md5=hashlib.md5(payload).hexdigest(),
        sha256="a" * 64,  # pinned value deliberately wrong
        retrieval_date="2026-10-03",
        reference_name="JPL DE440",
        reference_version="test",
        source_citation="test",
        coverage_et=(-1.0, 1.0),
        body_ids=(10,),
    )
    with pytest.raises(KernelIntegrityError) as exc:
        verify_kernel(kernel, manifest)
    assert "SHA-256 mismatch" in str(exc.value)


def test_de442_filename_rejected_no_substitution() -> None:
    with pytest.raises(ValueError, match="substitution"):
        KernelManifest(
            filename="de442s.bsp",
            url=DE440S_MANIFEST.url,
            size_bytes=1,
            md5="0" * 32,
            sha256="0" * 64,
            retrieval_date="2026-10-03",
            reference_name="JPL DE440",
            reference_version="test",
            source_citation="test",
            coverage_et=(-1.0, 1.0),
            body_ids=(10,),
        )
    assert DE440_KERNEL_FILENAMES == ("de440s.bsp", "de440.bsp")


def test_non_de440_reference_name_rejected() -> None:
    with pytest.raises(ValueError, match="reference_name"):
        KernelManifest(
            filename="de440s.bsp",
            url=DE440S_MANIFEST.url,
            size_bytes=1,
            md5="0" * 32,
            sha256="0" * 64,
            retrieval_date="2026-10-03",
            reference_name="JPL DE441",
            reference_version="test",
            source_citation="test",
            coverage_et=(-1.0, 1.0),
            body_ids=(10,),
        )


@pytest.mark.parametrize("field,value", [("md5", "0" * 31), ("sha256", "z" * 64)])
def test_malformed_hash_rejected(field: str, value: str) -> None:
    kwargs: dict = dict(
        filename="de440s.bsp",
        url=DE440S_MANIFEST.url,
        size_bytes=1,
        md5="0" * 32,
        sha256="0" * 64,
        retrieval_date="2026-10-03",
        reference_name="JPL DE440",
        reference_version="test",
        source_citation="test",
        coverage_et=(-1.0, 1.0),
        body_ids=(10,),
    )
    kwargs[field] = value
    with pytest.raises(ValueError, match=field):
        KernelManifest(**kwargs)


def test_default_kernel_path_uses_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(KERNEL_DIR_ENV, r"D:\data\kernels")
    assert default_kernel_path() == Path(r"D:\data\kernels") / "de440s.bsp"
    monkeypatch.delenv(KERNEL_DIR_ENV)
    assert default_kernel_path() == Path("kernels") / "de440s.bsp"
