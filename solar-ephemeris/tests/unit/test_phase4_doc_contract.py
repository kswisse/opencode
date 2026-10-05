"""Hợp đồng tài liệu Phase 4: docs <-> manifest <-> record (kernel-free).

Checklist H + yêu cầu 19: mọi giá trị trích trong
``docs/methodology/phase4-jpl-validation.md`` phải khớp manifest và record
nghiệm thu, các chủ đề bắt buộc phải hiện diện, bản đồ yêu cầu 1-20 phải
đủ. Không đụng kernel, không import spiceypy.
"""

from __future__ import annotations

import json
from pathlib import Path

from solar_ephemeris.ephemeris.kernel_manifest import DE440S_MANIFEST

REPO = Path(__file__).resolve().parents[2]
DOC = REPO / "docs" / "methodology" / "phase4-jpl-validation.md"
UNITS_DOC = REPO / "docs" / "methodology" / "units-and-frames.md"
RECORD = REPO / "docs" / "methodology" / "phase4_comparison_record.json"

# Checklist H: đủ 17 mục (>=14 chủ đề bắt buộc của brief).
REQUIRED_HEADINGS = [
    "Vì sao DE440",
    "Nguồn (source)",
    "checksum",
    "Coverage",
    "Body IDs",
    "frame",
    "center",
    "time scale",
    "units",
    "transformations",
    "interpolation",
    "metrics",
    "uncertainty sources",
    "limitations",
    "reproducibility procedure",
    "requirement → test map",
]


def test_doc_exists_and_covers_all_required_topics():
    text = DOC.read_text(encoding="utf-8")
    missing = [h for h in REQUIRED_HEADINGS if h not in text]
    assert not missing, f"doc missing required topics: {missing}"


def test_doc_quotes_manifest_identity_values():
    text = DOC.read_text(encoding="utf-8")
    lo, hi = DE440S_MANIFEST.coverage_et
    for token in (
        DE440S_MANIFEST.filename,
        DE440S_MANIFEST.md5,
        DE440S_MANIFEST.sha256,
        str(DE440S_MANIFEST.size_bytes),
        str(lo),
        str(hi),
        DE440S_MANIFEST.reference_name,
    ):
        assert token in text, f"doc does not quote manifest value: {token!r}"


def test_requirement_to_test_map_covers_req_1_through_20():
    text = DOC.read_text(encoding="utf-8")
    for req in range(1, 21):
        assert f"| {req} |" in text, f"requirement row {req} missing from map"


def test_committed_record_matches_manifest():
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    ref = record["reference_metadata"]
    assert ref["reference_name"] == DE440S_MANIFEST.reference_name
    assert ref["reference_version"] == DE440S_MANIFEST.reference_version
    assert ref["kernel_filename"] == DE440S_MANIFEST.filename
    assert ref["kernel_md5"] == DE440S_MANIFEST.md5
    assert ref["kernel_sha256"] == DE440S_MANIFEST.sha256
    assert ref["size_bytes"] == DE440S_MANIFEST.size_bytes
    assert ref["retrieval_date"] == DE440S_MANIFEST.retrieval_date
    assert ref["body_ids"] == list(DE440S_MANIFEST.body_ids)
    assert ref["kernel_coverage"]["intervals"] == [list(DE440S_MANIFEST.coverage_et)]
    assert ref["source"].startswith(DE440S_MANIFEST.source_citation)
    assert ref["reference_frame"] == "J2000"
    assert ref["reference_center"] == 0
    assert ref["time_standard"].startswith("TDB")
    assert ref["native_position_unit"] == "km"
    assert ref["native_velocity_unit"] == "km/s"


def test_record_stats_are_the_values_quoted_in_doc():
    text = DOC.read_text(encoding="utf-8")
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    assert f"{record['position_stats']['max']:.2f}" in text
    assert f"{record['velocity_stats']['max']:.7f}" in text
    assert "5073209.53" in text        # Sun-Earth E_pos max (stage9)
    assert "62.578" in text            # measured interpolation bound (stage8)
    assert "121.80" in text            # Earth-Moon distance error max (stage10b)
    assert "phase4_comparison_record.json" in text


def test_doc_records_both_gates_with_zero_failures():
    text = DOC.read_text(encoding="utf-8")
    assert "324 passed" in text and "26 deselected" in text   # Gate A
    assert "26 passed" in text and "324 deselected" in text   # Gate B
    assert "0 failed, 0 skipped" in text


def test_units_doc_stale_phase1_2_claims_were_amended():
    text = UNITS_DOC.read_text(encoding="utf-8")
    assert "kích hoạt từ Phase 4" in text
    assert "recenter_ssb_to_model" in text
    assert "không hoạt động trong Phase 1–2" not in text
    assert "chưa được implement (Phase 4)" not in text
