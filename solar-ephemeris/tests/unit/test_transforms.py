"""Translation-only transforms (requirement 8, R8): exactness, COM=0, offsets.

Windows in these tests are measured-first: values were read from the
identity-verified recorded fixture (2026-10-03) before the bound was written.
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from solar_ephemeris.ephemeris.fixture_backend import FixtureReference
from solar_ephemeris.frames.transforms import barycentre, recenter_ssb_to_model
from solar_ephemeris.physics.constants import GM_EARTH, GM_MOON, GM_SUN

JD_J2000 = 2451545.0


@pytest.fixture(scope="module")
def fixture() -> FixtureReference:
    return FixtureReference()


def _states(fixture: FixtureReference, bodies: list[str], et: float):
    states = [fixture.state_at(body=b, et=et) for b in bodies]
    pos = np.array([s.position_m for s in states])
    vel = np.array([s.velocity_ms for s in states])
    gm = np.array([{"Sun": GM_SUN, "Earth": GM_EARTH, "Moon": GM_MOON}[b] for b in bodies])
    return pos, vel, gm


def test_barycentre_exact_hand_case() -> None:
    # Hand values: gm=[1,3] → r_cm = (1*0 + 3*4)/4 = 3 exactly.
    gm = np.array([1.0, 3.0])
    pos = np.array([[0.0, 0.0, 0.0], [4.0, 0.0, 0.0]])
    vel = np.array([[1.0, 2.0, 3.0], [5.0, 6.0, 7.0]])
    r, v = barycentre(gm, pos, vel)
    assert np.array_equal(r, np.array([3.0, 0.0, 0.0]))  # bit-exact
    assert np.array_equal(v, np.array([4.0, 5.0, 6.0]))  # simple mean, exact


def test_barycentre_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError, match="equal shapes"):
        barycentre(np.array([1.0]), np.zeros((1, 3)), np.zeros((2, 3)))
    with pytest.raises(ValueError, match="body count"):
        barycentre(np.array([1.0]), np.zeros((2, 3)), np.zeros((2, 3)))
    with pytest.raises(ValueError, match=r"\(N, 3\)"):
        barycentre(np.array([1.0, 2.0]), np.zeros((2, 2)), np.zeros((2, 2)))
    with pytest.raises(ValueError, match="positive"):
        barycentre(np.array([1.0, -2.0]), np.zeros((2, 3)), np.zeros((2, 3)))


def test_recenter_is_exact_translation_small_integers() -> None:
    gm = np.array([1.0, 1.0])
    pos = np.array([[10.0, 0.0, 0.0], [20.0, 0.0, 0.0]])
    vel = np.array([[1.0, 0.0, 0.0], [3.0, 0.0, 0.0]])
    pos_rel, vel_rel, r_origin, v_origin = recenter_ssb_to_model(
        pos, vel, gm, ["Earth", "Earth"]
    )
    assert np.array_equal(r_origin, np.array([15.0, 0.0, 0.0]))
    assert np.array_equal(pos_rel, np.array([[-5.0, 0.0, 0.0], [5.0, 0.0, 0.0]]))
    assert np.array_equal(vel_rel, np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]))


def test_api_exposes_no_rotation() -> None:
    # R8: translation-only by construction — no rotation/orientation/Yaw
    # parameter exists anywhere in the transform API.
    for fn in (barycentre, recenter_ssb_to_model):
        for name in inspect.signature(fn).parameters:
            lowered = name.lower()
            assert "rot" not in lowered and "quat" not in lowered and "yaw" not in lowered


def test_relative_vectors_preserved_no_rotation() -> None:
    # A rotation would change inter-body vectors; a translation must not.
    rng = np.random.default_rng(42)
    gm = np.array([GM_SUN, GM_EARTH, GM_MOON])
    pos = rng.normal(scale=1e11, size=(3, 3))
    vel = rng.normal(scale=1e4, size=(3, 3))
    rel, _, _, _ = recenter_ssb_to_model(pos, vel, gm, ["Sun", "Earth", "Moon"])
    for i in range(3):
        for j in range(3):
            assert np.allclose(rel[i] - rel[j], pos[i] - pos[j], rtol=1e-12, atol=1e-3)


def test_inputs_not_mutated() -> None:
    gm = np.array([GM_SUN, GM_EARTH])
    pos = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    vel = np.array([[7.0, 8.0, 9.0], [10.0, 11.0, 12.0]])
    pos0, vel0 = pos.copy(), vel.copy()
    recenter_ssb_to_model(pos, vel, gm, ["Sun", "Earth"])
    assert np.array_equal(pos, pos0) and np.array_equal(vel, vel0)


def test_body_count_diagnostics_names_the_bodies(fixture: FixtureReference) -> None:
    pos, vel, _ = _states(fixture, ["Sun", "Earth"], 0.0)
    with pytest.raises(ValueError, match="model_bodies"):
        recenter_ssb_to_model(pos, vel, np.array([GM_SUN]), ["Sun"])


def test_com_zero_invariant_after_recenter(fixture: FixtureReference) -> None:
    # Σ GM_k r'_k ≡ 0 (the defining property of the model origin).
    bodies = ["Sun", "Earth", "Moon"]
    pos, vel, gm = _states(fixture, bodies, 0.0)
    pos_rel, vel_rel, _, _ = recenter_ssb_to_model(pos, vel, gm, bodies)
    r_eff = (gm[:, None] * pos_rel).sum(axis=0) / gm.sum()
    v_eff = (gm[:, None] * vel_rel).sum(axis=0) / gm.sum()
    # Measured 2026-10-03 at et=0: |r_eff| = 3.36e-8 m, |v_eff| = 2.78e-15
    # m/s (float round-off only); bounds carry ~6 decades of headroom.
    assert np.linalg.norm(r_eff) < 1e-2, f"COM drift {np.linalg.norm(r_eff)} m"
    assert np.linalg.norm(v_eff) < 1e-10, f"COM velocity drift {np.linalg.norm(v_eff)}"


def test_sun_earth_model_origin_offset_from_ssb(fixture: FixtureReference) -> None:
    # The model origin (Sun–Earth barycentre) sits far from SSB — the offset
    # the translation layer exists to correct. Measured at et=0: 1.1470e9 m.
    bodies = ["Sun", "Earth"]
    for et in (0.0, 86400.0):
        pos, vel, gm = _states(fixture, bodies, et)
        _, _, r_origin, _ = recenter_ssb_to_model(pos, vel, gm, bodies)
        offset = float(np.linalg.norm(r_origin))
        assert 5e8 <= offset <= 2e9, f"offset {offset} m outside [5e8, 2e9] at et={et}"


def test_se_vs_sem_origin_delta_quantified(fixture: FixtureReference) -> None:
    # Splitting Earth/Moon as separate bodies moves the model origin by
    # ~5426 m (Moon's GM at 1.47e11 m from SSB). Window from measurement at
    # et=0: 5426.39 m; variation over a lunar month ≈ ±14 m.
    pos_se, vel_se, gm_se = _states(fixture, ["Sun", "Earth"], 0.0)
    pos_sem, vel_sem, gm_sem = _states(fixture, ["Sun", "Earth", "Moon"], 0.0)
    _, _, r_se, _ = recenter_ssb_to_model(pos_se, vel_se, gm_se, ["Sun", "Earth"])
    _, _, r_sem, _ = recenter_ssb_to_model(
        pos_sem, vel_sem, gm_sem, ["Sun", "Earth", "Moon"]
    )
    delta = float(np.linalg.norm(r_sem - r_se))
    assert 4000.0 <= delta <= 7000.0, f"origin delta {delta} m outside [4000, 7000]"
