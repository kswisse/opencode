import numpy as np
import pytest

from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale
from solar_ephemeris.physics.state import State, StateMeta


def make_meta(**over) -> StateMeta:
    base = dict(
        frame=ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC,
        origin="barycenter(Sun, Earth)",
        epoch_jd=2451545.0,
        time_scale=TimeScale.TDB,
    )
    base.update(over)
    return StateMeta(**base)


def make_arrays(n: int = 2):
    pos = np.arange(n * 3, dtype=np.float64).reshape(n, 3)
    vel = np.linspace(0.0, 1.0, n * 3).reshape(n, 3)
    return pos, vel


def test_valid_state_basics():
    pos, vel = make_arrays(3)
    s = State(positions=pos, velocities=vel, body_names=("A", "B", "C"), meta=make_meta())
    assert s.n_bodies == 3
    assert s.positions.dtype == np.float64
    assert s.body_names == ("A", "B", "C")


@pytest.mark.parametrize(
    "shape",
    [(3,), (2, 4), (2, 3, 1)],
    ids=["1d", "4cols", "3d"],
)
def test_bad_shapes_rejected(shape):
    arr = np.zeros(shape)
    with pytest.raises(ValueError):
        State(
            positions=arr,
            velocities=np.zeros((2, 3)),
            body_names=("A", "B"),
            meta=make_meta(),
        )


def test_row_count_mismatch_rejected():
    with pytest.raises(ValueError):
        State(
            positions=np.zeros((3, 3)),
            velocities=np.zeros((2, 3)),
            body_names=("A", "B"),
            meta=make_meta(),
        )


def test_name_count_mismatch_rejected():
    with pytest.raises(ValueError):
        State(
            positions=np.zeros((2, 3)),
            velocities=np.zeros((2, 3)),
            body_names=("A",),
            meta=make_meta(),
        )


def test_nan_rejected():
    pos, vel = make_arrays()
    pos[0, 0] = np.nan
    with pytest.raises(ValueError):
        State(positions=pos, velocities=vel, body_names=("A", "B"), meta=make_meta())


def test_duplicate_names_rejected():
    pos, vel = make_arrays(2)
    with pytest.raises(ValueError):
        State(positions=pos, velocities=vel, body_names=("A", "A"), meta=make_meta())


def test_empty_names_rejected():
    pos, vel = make_arrays(1)
    with pytest.raises(ValueError):
        State(positions=pos, velocities=vel, body_names=(), meta=make_meta())


def test_integer_input_cast_to_float64():
    s = State(
        positions=[[0, 1, 2], [3, 4, 5]],
        velocities=[[0, 0, 0], [1, 1, 1]],
        body_names=("A", "B"),
        meta=make_meta(),
    )
    assert s.positions.dtype == np.float64
    assert s.velocities.dtype == np.float64


def test_copy_semantics_inputs_detached():
    pos, vel = make_arrays()
    s = State(positions=pos, velocities=vel, body_names=("A", "B"), meta=make_meta())
    pos[0, 0] = 1.0e9
    vel[1, 2] = -1.0e9
    assert s.positions[0, 0] != 1.0e9
    assert s.velocities[1, 2] != -1.0e9


def test_meta_requires_nonempty_origin():
    with pytest.raises(ValueError):
        make_meta(origin="")


def test_meta_rejects_non_si_units():
    with pytest.raises(ValueError):
        make_meta(length_unit="km")
    with pytest.raises(ValueError):
        make_meta(time_unit="day")
    with pytest.raises(ValueError):
        make_meta(gm_unit="km^3/s^2")


def test_meta_rejects_nonfinite_epoch():
    with pytest.raises(ValueError):
        make_meta(epoch_jd=np.inf)


def test_barycenter_helper():
    pos = np.array([[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]])
    vel = np.array([[0.0, 2.0, 0.0], [0.0, -2.0, 0.0]])
    s = State(positions=pos, velocities=vel, body_names=("A", "B"), meta=make_meta())
    r_cm, v_cm = s.barycenter(np.array([3.0, 1.0]))
    assert np.allclose(r_cm, [0.5, 0.0, 0.0])
    assert np.allclose(v_cm, [0.0, 1.0, 0.0])
    with pytest.raises(ValueError):
        s.barycenter(np.array([1.0]))
