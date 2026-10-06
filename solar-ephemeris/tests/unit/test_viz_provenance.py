"""U4 - provenance sidecar + deterministic render foundation.

Requirements: R6, R7, R8, R10, R11, R13, R15; KTD7, KTD9.

Gate A split (R29/KTD11): every case that needs rcParams, savefig or
matplotlib artists calls ``pytest.importorskip("matplotlib")`` INSIDE the
test; sidecar-JSON, hash, units, role-table, limits and caption cases run
without matplotlib. All file output goes to pytest ``tmp_path`` - never the
repo ``figures/`` or ``results/`` trees (KTD9).

The R6 key list is HARDCODED here (test-side authority) rather than imported
from the implementation, so dropping a key from the module turns this red.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pytest

from solar_ephemeris.ephemeris.units import KM_TO_M
from solar_ephemeris.physics.constants import AU_M
from solar_ephemeris.visualization.gaps import GAP_KEYS, DataGapError, make_gap
from solar_ephemeris.visualization.provenance import (
    build_caption,
    build_sidecar,
    figure_data_hash,
    sidecar_path_for,
    write_figure,
    write_sidecar,
)
from solar_ephemeris.visualization import style, units
from solar_ephemeris.visualization.style import RC_PARAMS, truthful_limits

#: R6 figure-level keys - sidecar always carries these, verbatim list.
R6_FIGURE_KEYS = (
    "figure_id",
    "figure_data_hash",
    "source",
    "gaps",
    "style_version",
    "frame",
    "origin",
    "time_scale",
    "units",
    "software_version",
    "matplotlib_version",
    "generated_at",
)

#: R6 record-level keys - top level for single-record figures, one entry per
#: record inside sources[] for multi-record figures.
R6_RECORD_KEYS = (
    "experiment_id",
    "configuration_hash",
    "output_hash",
    "bodies",
    "epoch",
    "duration",
    "integrator",
    "timestep",
    "reference_dataset",
    "reference_kernel",
)


def _arrays(seed: float = 0.0) -> dict[str, np.ndarray]:
    """Deterministic finite series used as "the arrays being plotted"."""
    t = np.arange(6, dtype=np.float64) + seed
    return {
        "times": t,
        "positions": np.stack([np.sin(t), np.cos(t), 0.1 * t], axis=1),
        "velocities": np.stack([np.cos(t), -np.sin(t), np.full(6, 0.2)], axis=1),
    }


def _record(experiment_id: str = "X/full", **over) -> dict:
    record = {
        "experiment_id": experiment_id,
        "configuration_hash": "cfg-" + experiment_id,
        "output_hash": "0" * 64,
        "bodies": ["Sun", "Earth"],
        "epoch": 2451545.0,
        "duration": 4.0,
        "integrator": "rk4",
        "timestep": 1.0,
        "reference_dataset": "JPL DE440 (de440s.bsp live)",
        "reference_kernel": "kernels/de440s.bsp",
        "kernel_sha256": "ab" * 32,
        "run_label": "not an R6 key - must not be extracted",
    }
    record.update(over)
    return record


def _sidecar(**over):
    kwargs = dict(
        figure_id="fig-01",
        source="stored",
        frame="SSB-ICRS",
        origin="SSB(0)",
        time_scale="TDB",
        units="m, m/s, s",
        arrays=_arrays(),
        records=_record(),
    )
    kwargs.update(over)
    return build_sidecar(**kwargs)


def _plt():
    mpl = pytest.importorskip("matplotlib")
    mpl.use("Agg", force=True)
    import matplotlib.pyplot as plt

    return plt


# ---------------------------------------------------------------------------
# R11 - units helpers, position and velocity constants tested SEPARATELY,
# read from the source-constant modules (no retyped literals, R10).
# ---------------------------------------------------------------------------


def test_position_constant_m_au_round_trips_from_source_module() -> None:
    assert units.AU_M == AU_M  # viz reuses physics.constants.AU_M, not a retype
    assert float(units.m_to_au(AU_M)) == 1.0
    assert float(units.au_to_m(1.0)) == AU_M
    values = np.array([0.0, AU_M, 2.0 * AU_M])
    assert np.allclose(units.au_to_m(units.m_to_au(values)), values)


def test_velocity_constant_ms_kms_round_trips_from_source_module() -> None:
    assert units.KM_TO_M == KM_TO_M  # viz reuses ephemeris.units.KM_TO_M
    assert float(units.ms_to_kms(KM_TO_M)) == 1.0
    assert float(units.kms_to_ms(1.0)) == KM_TO_M
    values = np.array([0.0, 1.0, 30.0])
    assert np.allclose(units.ms_to_kms(units.kms_to_ms(values)), values)


# ---------------------------------------------------------------------------
# R8 - figure_data_hash: same construction as output_hash (name + shape +
# bytes), proved by recomputing the construction independently in-test.
# ---------------------------------------------------------------------------


def _independent_output_hash_construction(times, positions, velocities) -> str:
    """Local reimplementation of experiments/_common.output_hash: SHA-256
    over name + shape + float64 bytes per array, fixed order. (src code must
    not import experiments - equality of approach is proved here instead.)"""
    h = hashlib.sha256()
    for name, arr in (("times", times), ("positions", positions), ("velocities", velocities)):
        a = np.ascontiguousarray(arr, dtype=np.float64)
        h.update(name.encode("ascii"))
        h.update(str(a.shape).encode("ascii"))
        h.update(a.tobytes())
    return h.hexdigest()


def test_figure_data_hash_matches_independent_output_hash_construction() -> None:
    a = _arrays()
    assert figure_data_hash(a) == _independent_output_hash_construction(
        a["times"], a["positions"], a["velocities"]
    )


def test_figure_data_hash_same_arrays_equal_different_arrays_differ() -> None:
    a, b = _arrays(), _arrays()
    assert figure_data_hash(a) == figure_data_hash(b)
    c = _arrays(seed=1.0)
    assert figure_data_hash(a) != figure_data_hash(c)


# ---------------------------------------------------------------------------
# R6 - sidecar key contract (single-record and multi-record variants)
# ---------------------------------------------------------------------------


def test_single_record_sidecar_carries_all_r6_keys_directly() -> None:
    record = _record()
    sc = _sidecar(records=record, projection="XY of SSB-ICRS")

    for key in R6_FIGURE_KEYS:
        assert key in sc, f"missing figure-level R6 key: {key}"
    for key in R6_RECORD_KEYS:
        assert key in sc, f"missing record-level R6 key: {key}"
        assert sc[key] == record[key]
    assert sc["kernel_sha256"] == record["kernel_sha256"]
    assert "sources" not in sc
    assert "run_label" not in sc, "non-R6 record keys must not leak onto the sidecar"
    assert sc["source"] in ("stored", "derived", "aggregate")
    assert sc["style_version"] == style.STYLE_VERSION
    assert sc["gaps"] == []


def test_multi_record_sidecar_moves_record_keys_into_sources() -> None:
    rec_a, rec_b = _record("A/one"), _record("B/two")
    sc = _sidecar(records=[rec_a, rec_b], source="aggregate", figure_id="fig-10")

    for key in R6_FIGURE_KEYS:
        assert key in sc, f"missing figure-level R6 key: {key}"
    assert "experiment_id" not in sc, "record keys must not sit at top level"
    assert "output_hash" not in sc
    assert isinstance(sc["sources"], list) and len(sc["sources"]) == 2
    for entry, rec in zip(sc["sources"], (rec_a, rec_b)):
        for key in R6_RECORD_KEYS:
            assert entry[key] == rec[key], f"source entry missing {key}"
        assert "run_label" not in entry


# ---------------------------------------------------------------------------
# R7 / KTD9 - atomic sidecar write: sort_keys, allow_nan, temp->replace,
# parent dirs created, non-finite payload rejected without a file.
# ---------------------------------------------------------------------------


def test_write_sidecar_valid_payload_sorted_atomic_no_temp_leftover(tmp_path: Path) -> None:
    path = tmp_path / "does" / "not" / "exist" / "fig-01.json"  # nonexistent dir edge
    payload = {"b": 2, "a": 1.0, "figure_id": "fig-01", "gaps": []}

    out = write_sidecar(path, payload)

    assert out == path and path.is_file()
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    assert list(data) == sorted(data), "write_record semantics: sort_keys=True"
    assert "NaN" not in text and "Infinity" not in text
    json.dumps(data, allow_nan=False)  # valid sidecar: allow_nan=False never raises
    assert not path.with_name(path.name + ".tmp").exists()


def test_write_sidecar_nonfinite_payload_is_data_gap_and_writes_nothing(tmp_path: Path) -> None:
    path = tmp_path / "fig-01.json"
    with pytest.raises(DataGapError) as exc:
        write_sidecar(path, {"figure_id": "fig-01", "figure_data_hash": float("nan")})
    assert not path.exists()
    gap = exc.value.gaps[0]
    assert set(gap) == set(GAP_KEYS)
    assert "fig-01.json" in gap["name"]


def test_gaps_nonempty_are_carried_into_sidecar(tmp_path: Path) -> None:
    gap = make_gap(
        "comparison payload",
        reason="missing",
        detail="record has no comparison key",
        source_path="results/experiment_X/experiment_record.json",
    )
    sc = _sidecar(gaps=[gap], source="derived")
    path = write_sidecar(tmp_path / "fig-07.json", sc)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["gaps"] == [gap]
    assert set(data["gaps"][0]) == set(GAP_KEYS)
    assert data["gaps"][0]["reason"] == "missing"


# ---------------------------------------------------------------------------
# KTD9 ordering - non-finite series rejected BEFORE any PNG exists
# ---------------------------------------------------------------------------


def test_build_sidecar_rejects_nonfinite_series(tmp_path: Path) -> None:
    bad = {"positions": np.array([1.0, np.nan, 3.0])}
    with pytest.raises(DataGapError) as exc:
        _sidecar(arrays=bad)
    gap = exc.value.gaps[0]
    assert set(gap) == set(GAP_KEYS)
    assert "positions" in gap["detail"]
    assert list(tmp_path.iterdir()) == []


def test_write_figure_rejects_nonfinite_before_png_write(tmp_path: Path) -> None:
    plt = _plt()
    out = tmp_path / "figures"
    out.mkdir()
    fig, ax = plt.subplots()
    try:
        ax.plot([0.0, 1.0], [1.0, 2.0])
        sidecar = _sidecar()  # valid sidecar built from finite arrays
        bad_arrays = {"positions": np.array([1.0, np.inf])}
        with pytest.raises(DataGapError) as exc:
            write_figure(
                fig, png_path=out / "fig-01.png", sidecar=sidecar, arrays=bad_arrays
            )
        assert "positions" in exc.value.gaps[0]["detail"]
        assert list(out.iterdir()) == [], "no orphan PNG, no temp file"
    finally:
        plt.close(fig)


def test_write_figure_rejects_png_under_results_tree(tmp_path: Path) -> None:
    class _NeverTouched:
        def savefig(self, *_args, **_kwargs) -> None:
            raise AssertionError("figure touched before path contract check")

    out = tmp_path / "figures_out"
    out.mkdir()
    with pytest.raises(ValueError, match="results"):
        write_figure(
            _NeverTouched(),
            png_path=out / "results" / "fig-01.png",
            sidecar={"figure_id": "fig-01"},
            arrays={},
        )
    assert list(out.iterdir()) == []


# ---------------------------------------------------------------------------
# Happy render path (matplotlib): sidecar written next to PNG, hash stable,
# PNG sha256 recorded as auxiliary info only (R8), deterministic overwrite.
# ---------------------------------------------------------------------------


def test_render_twice_same_arrays_same_figure_data_hash(tmp_path: Path) -> None:
    plt = _plt()
    arrays = _arrays()
    hashes: list[str] = []
    png_shas: list[str] = []
    for name in ("first", "second"):
        out = tmp_path / name
        fig, ax = plt.subplots()
        try:
            ax.plot(arrays["times"], arrays["positions"][:, 0])
            sidecar = _sidecar(figure_id="fig-determinism", source="derived")
            png_path, sc_path = write_figure(
                fig, png_path=out / "fig.png", sidecar=sidecar, arrays=arrays
            )
        finally:
            plt.close(fig)
        assert png_path.is_file() and sc_path.is_file()
        assert sc_path == sidecar_path_for(png_path) == png_path.with_suffix(".json")
        data = json.loads(sc_path.read_text(encoding="utf-8"))
        hashes.append(data["figure_data_hash"])
        png_shas.append(data["png_sha256"])
        # identity is the array hash; PNG sha256 is auxiliary information only
        assert data["figure_data_hash"] == figure_data_hash(arrays)
        assert len(data["png_sha256"]) == 64

    assert hashes[0] == hashes[1], f"figure_data_hash unstable: {hashes}"
    print(f"figure_data_hash={hashes[0]}")
    print(f"png_sha256 first={png_shas[0]} second={png_shas[1]}")
    # PNG bytes may legitimately differ between renders - NOT asserted equal.


def test_overwrite_same_figure_id_is_deterministic_two_files_only(tmp_path: Path) -> None:
    plt = _plt()
    out = tmp_path / "figures"
    arrays = _arrays()
    for _ in range(2):
        fig, ax = plt.subplots()
        try:
            ax.plot(arrays["times"], arrays["velocities"][:, 0])
            write_figure(
                fig,
                png_path=out / "fig-13.png",
                sidecar=_sidecar(figure_id="fig-13", source="stored"),
                arrays=arrays,
            )
        finally:
            plt.close(fig)
    files = sorted(p.name for p in out.iterdir())
    assert files == ["fig-13.json", "fig-13.png"], f"stray temp/extra files: {files}"
    data = json.loads((out / "fig-13.json").read_text(encoding="utf-8"))
    assert data["figure_id"] == "fig-13"


def test_overwrite_final_png_rename_failure_restores_original_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plt = _plt()
    out = tmp_path / "figures"
    old_arrays, new_arrays = _arrays(), _arrays(seed=3.0)
    png = out / "fig-14.png"
    fig, ax = plt.subplots()
    try:
        ax.plot(old_arrays["times"], old_arrays["positions"][:, 0])
        write_figure(
            fig,
            png_path=png,
            sidecar=_sidecar(figure_id="fig-14", source="stored"),
            arrays=old_arrays,
        )
    finally:
        plt.close(fig)
    sc_path = sidecar_path_for(png)
    original_sidecar = sc_path.read_bytes()
    original_png = png.read_bytes()

    real_replace = os.replace

    def _png_rename_locked(src, dst):
        if Path(dst) == png:
            raise PermissionError("simulated: target PNG locked")
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", _png_rename_locked)
    fig, ax = plt.subplots()
    try:
        ax.plot(new_arrays["times"], new_arrays["positions"][:, 0])
        with pytest.raises(PermissionError, match="locked"):
            write_figure(
                fig,
                png_path=png,
                sidecar=_sidecar(
                    figure_id="fig-14", source="stored", arrays=new_arrays
                ),
                arrays=new_arrays,
            )
    finally:
        plt.close(fig)

    files = sorted(p.name for p in out.iterdir())
    assert files == ["fig-14.json", "fig-14.png"], f"stray temp/extra files: {files}"
    assert sc_path.read_bytes() == original_sidecar, "original sidecar must be intact"
    data = json.loads(sc_path.read_text(encoding="utf-8"))
    assert data["figure_data_hash"] == figure_data_hash(old_arrays)
    assert data["figure_data_hash"] != figure_data_hash(new_arrays)
    assert png.read_bytes() == original_png, "PNG must still be the old render"


# ---------------------------------------------------------------------------
# R13 - truthful axis limits: never cut data or baseline
# ---------------------------------------------------------------------------


def test_truthful_limits_contain_signal_and_baseline() -> None:
    signal = np.array([5.0, 7.5, 10.0])
    lo, hi = truthful_limits(signal, include_zero=True)
    assert lo <= signal.min() and hi >= signal.max()
    assert lo <= 0.0, "baseline y=0 must stay inside the limits"

    a = np.array([-3.0, -1.0])
    b = np.array([2.0, 4.0])
    lo2, hi2 = truthful_limits(a, b, pad=0.1)
    assert lo2 <= a.min() and lo2 <= b.min()
    assert hi2 >= a.max() and hi2 >= b.max()
    assert lo2 < min(a.min(), b.min()) and hi2 > max(a.max(), b.max())


# ---------------------------------------------------------------------------
# R15 - frozen five-role table, grayscale-distinguishable without color
# ---------------------------------------------------------------------------


def test_role_table_frozen_five_roles_with_unique_shape_pairs() -> None:
    assert set(style.ROLES) == {"model", "reference", "error", "control", "signal"}
    pairs = [
        (spec["linestyle"], spec["marker"]) for spec in style.ROLES.values()
    ]
    assert len(set(pairs)) == 5, f"roles collide in grayscale: {pairs}"
    assert style.STYLE_VERSION


def test_signal_role_distinguishable_on_grayscale_artist_props() -> None:
    plt = _plt()
    fig, ax = plt.subplots()
    try:
        lines = [
            ax.plot([0, 1], [0, 1], label=role, **style.role_style(role))[0]
            for role in style.ROLES
        ]
    finally:
        plt.close(fig)
    specs = [(line.get_linestyle(), line.get_marker()) for line in lines]
    assert len(set(specs)) == 5, f"grayscale collision: {specs}"
    signal_idx = list(style.ROLES).index("signal")
    sig_linestyle, sig_marker = specs[signal_idx]
    assert sig_linestyle == ":", f"signal must be dotted, got {sig_linestyle!r}"
    assert sig_marker == "x", f"signal must be x-crossed, got {sig_marker!r}"
    # deliberately NOT checking RGB: grayscale distinction is path/marker only


# ---------------------------------------------------------------------------
# KTD7 - one pinned style module: rcParams/DPI/font fixed in one place
# ---------------------------------------------------------------------------


def test_style_context_pins_rc_params_in_one_place() -> None:
    mpl = pytest.importorskip("matplotlib")
    mpl.use("Agg", force=True)
    with style.style_context():
        assert mpl.rcParams["savefig.dpi"] == RC_PARAMS["savefig.dpi"]
        assert mpl.rcParams["figure.dpi"] == RC_PARAMS["figure.dpi"]
        assert tuple(mpl.rcParams["figure.figsize"]) == tuple(RC_PARAMS["figure.figsize"])
        assert mpl.rcParams["font.size"] == RC_PARAMS["font.size"]


# ---------------------------------------------------------------------------
# R6/R13 - caption carries the provenance tokens
# ---------------------------------------------------------------------------


def test_caption_contains_provenance_tokens() -> None:
    sc = _sidecar(projection="XY of SSB-ICRS")
    caption = sc["caption"]
    assert caption == build_caption(sc)
    assert sc["figure_id"] in caption
    assert f"source={sc['source']}" in caption
    assert f"frame={sc['frame']}" in caption
    assert f"origin={sc['origin']}" in caption
    assert f"time_scale={sc['time_scale']}" in caption
    assert f"units={sc['units']}" in caption
    assert "projection=XY of SSB-ICRS" in caption
    assert f"data={sc['figure_data_hash'][:12]}" in caption
    assert "gaps=0" in caption


def test_caption_counts_nonempty_gaps() -> None:
    gap = make_gap(
        "reference series",
        reason="coverage",
        detail="epoch beyond fixture coverage",
        source_path="kernels/fixture.npz",
    )
    sc = _sidecar(gaps=[gap])
    assert "gaps=1" in sc["caption"]


# ---------------------------------------------------------------------------
# Failure modes of the helpers themselves (frozen table / contracts)
# ---------------------------------------------------------------------------


def test_helper_guards_reject_bad_inputs() -> None:
    with pytest.raises(ValueError, match="unknown style role"):
        style.role_style("trendline")
    with pytest.raises(ValueError, match="source"):
        _sidecar(source="invented")
    with pytest.raises(ValueError, match="no finite values"):
        truthful_limits(np.array([np.nan, np.inf]))
    with pytest.raises(ValueError, match="position unit"):
        units.position_label("furlong")


def test_extra_keys_merge_after_records_and_win_on_shared_keys() -> None:
    record = _record(reference_kernel="from-record.bsp")
    sc = _sidecar(
        records=record,
        extra={
            "reference_provider": "fixture",
            "reference_kernel": "from-identity.bsp",
            "coverage": {"intervals": [[0.0, 1.0]]},
        },
    )
    assert sc["reference_provider"] == "fixture"
    assert sc["coverage"] == {"intervals": [[0.0, 1.0]]}
    # identity extra wins over record extraction on the shared key
    assert sc["reference_kernel"] == "from-identity.bsp"
    assert sc["caption"] == build_caption(sc)
