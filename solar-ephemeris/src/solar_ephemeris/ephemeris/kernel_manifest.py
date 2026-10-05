"""Pinned identity of the one canonical reference kernel (requirement 1).

The manifest — not the download path, not the filename on disk — defines which
binary counts as "the DE440 reference". Every load verifies size + MD5 +
SHA-256 against these pinned values; any difference is treated as
modification/substitution (:class:`KernelIntegrityError`), including a
"helpful" upgrade to de441/de442 (R6): those filenames are rejected outright.

Checksum sources:
- MD5 ``3917ee56769db332790c751e2168843d`` — NAIF-published
  (``https://naif.jpl.nasa.gov/pub/naif/ftp/aa_checksums.txt``), verified on
  first retrieval 2026-10-03.
- SHA-256 ``c1c7feea...0a49f2`` — computed on that first verified retrieval
  and pinned here (repo stores metadata, not the 31 MB binary).

Coverage pin: ``spkcov`` on the verified file measured ET
[-4734072000.0, 4735368000.0] = JD [2396752.5, 2506352.5] =
1849-12-26 → 2150-01-22 at 0h TDB, equal to NAIF ``aa_summaries.txt``.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from solar_ephemeris.ephemeris.types import KernelIntegrityError

#: Only these two filenames are the DE440 solution; anything else on the NAIF
#: planets page (de441, de442, ...) is a different reference and is refused.
DE440_KERNEL_FILENAMES: Final[tuple[str, ...]] = ("de440s.bsp", "de440.bsp")

#: Environment variable overriding the kernel directory.
KERNEL_DIR_ENV: Final[str] = "SOLAR_EPHEMERIS_KERNEL_DIR"

_CHUNK: Final[int] = 1 << 20


@dataclass(frozen=True, slots=True)
class KernelManifest:
    """Identity + expected content of one reference kernel file."""

    filename: str
    url: str
    size_bytes: int
    md5: str  # NAIF-published (aa_checksums.txt)
    sha256: str  # pinned on first verified retrieval
    retrieval_date: str  # ISO-8601
    reference_name: str
    reference_version: str
    source_citation: str
    coverage_et: tuple[float, float]  # expected [start, end], TDB s past J2000
    body_ids: tuple[int, ...]  # expected spkobj result

    def __post_init__(self) -> None:
        if self.filename not in DE440_KERNEL_FILENAMES:
            raise ValueError(
                f"kernel filename {self.filename!r} is not a DE440 kernel "
                f"(allowed: {DE440_KERNEL_FILENAMES}); refusing silent reference "
                "substitution"
            )
        if self.reference_name != "JPL DE440":
            raise ValueError(
                f"reference_name must be 'JPL DE440', got {self.reference_name!r}"
            )
        if not self.url.startswith(("https://", "http://")):
            raise ValueError(f"url must be absolute, got {self.url!r}")
        if self.size_bytes <= 0:
            raise ValueError(f"size_bytes must be > 0, got {self.size_bytes!r}")
        for label, value, length in (("md5", self.md5, 32), ("sha256", self.sha256, 64)):
            if len(value) != length or any(c not in "0123456789abcdef" for c in value):
                raise ValueError(
                    f"{label} must be {length} lowercase hex chars, got {value!r}"
                )
        if not self.retrieval_date:
            raise ValueError("retrieval_date must be non-empty (ISO-8601)")
        lo, hi = self.coverage_et
        if not (lo < hi):
            raise ValueError(f"coverage_et must be (start < end), got {self.coverage_et!r}")
        if not self.body_ids:
            raise ValueError("body_ids must not be empty")


def _hash_file(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as fh:
        while chunk := fh.read(_CHUNK):
            h.update(chunk)
    return h.hexdigest()


def verify_kernel(path: Path | str, manifest: KernelManifest) -> None:
    """Verify ``path`` against the manifest: exists → size → md5 → sha256.

    Every failure raises :class:`KernelIntegrityError` with the reason and the
    retrieval URL — a missing kernel is an explicit failure with recovery
    instructions, never a skip.
    """
    p = Path(path)
    hint = f"download from {manifest.url} and verify against kernel_manifest.py"
    if not p.is_file():
        raise KernelIntegrityError(f"kernel file not found: {p} — {hint}")
    actual_size = p.stat().st_size
    if actual_size != manifest.size_bytes:
        raise KernelIntegrityError(
            f"kernel size mismatch for {p.name}: file={actual_size} B, "
            f"manifest={manifest.size_bytes} B — {hint}"
        )
    actual_md5 = _hash_file(p, "md5")
    if actual_md5 != manifest.md5:
        raise KernelIntegrityError(
            f"kernel MD5 mismatch for {p.name}: file={actual_md5}, "
            f"NAIF/manifest={manifest.md5} — {hint}"
        )
    actual_sha = _hash_file(p, "sha256")
    if actual_sha != manifest.sha256:
        raise KernelIntegrityError(
            f"kernel SHA-256 mismatch for {p.name}: file={actual_sha}, "
            f"pinned={manifest.sha256} — {hint}"
        )


def default_kernel_path(filename: str | None = None) -> Path:
    """Resolve the kernel path: ``$SOLAR_EPHEMERIS_KERNEL_DIR`` else ``./kernels``.

    Pure path resolution — file existence and identity are checked by
    :func:`verify_kernel`.
    """
    name = filename or DE440S_MANIFEST.filename
    override = os.environ.get(KERNEL_DIR_ENV)
    directory = Path(override) if override else Path("kernels")
    return directory / name


DE440S_MANIFEST: Final[KernelManifest] = KernelManifest(
    filename="de440s.bsp",
    url="https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp",
    size_bytes=32_726_016,
    md5="3917ee56769db332790c751e2168843d",
    sha256="c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2",
    retrieval_date="2026-10-03",
    reference_name="JPL DE440",
    reference_version="DE440, integrated 2020-06-25 (JPL de440_tech-comments.txt)",
    source_citation=(
        "NAIF generic SPK kernels (https://naif.jpl.nasa.gov/pub/naif/generic_kernels/"
        "spk/planets/); Park et al. (2021), AJ 161:105, "
        "DOI 10.3847/1538-3881/abd414"
    ),
    coverage_et=(-4_734_072_000.0, 4_735_368_000.0),
    body_ids=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 199, 299, 301, 399),
)
