import json

import pytest

from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale
from solar_ephemeris.simulation.configuration import SimulationConfig


def make(**over) -> SimulationConfig:
    base = dict(
        bodies=("Sun", "Earth"),
        integrator="verlet",
        dt=60.0,
        duration=86400.0,
        epoch_jd=2451545.0,
    )
    base.update(over)
    return SimulationConfig(**base)


def test_valid_config_accepted():
    c = make()
    assert c.bodies == ("Sun", "Earth")
    assert c.n_steps == 1440


def test_rejects_dt_nonpositive():
    with pytest.raises(ValueError):
        make(dt=0.0)
    with pytest.raises(ValueError):
        make(dt=-1.0)


def test_rejects_duration_shorter_than_dt():
    with pytest.raises(ValueError):
        make(dt=100.0, duration=50.0)


def test_rejects_empty_or_duplicate_bodies():
    with pytest.raises(ValueError):
        make(bodies=())
    with pytest.raises(ValueError):
        make(bodies=("Sun", "Earth", "Sun"))


def test_rejects_unknown_integrator():
    with pytest.raises(ValueError):
        make(integrator="euler")


def test_rejects_nonfinite_epoch():
    with pytest.raises(ValueError):
        make(epoch_jd=float("inf"))


def test_dict_round_trip():
    c = make(integrator="rk4", reference_dataset="DE440")
    again = SimulationConfig.from_dict(c.to_dict())
    assert again == c


def test_json_round_trip_is_lossless():
    c = make(integrator="rk4", frame=ReferenceFrame.SSB_ICRS, time_scale=TimeScale.TT)
    blob = json.dumps(json.loads(json.dumps(c.to_dict())))
    assert SimulationConfig.from_dict(json.loads(blob)) == c


def test_from_dict_rejects_unknown_keys():
    c = make()
    d = c.to_dict()
    d["timestep"] = 999.0  # common typo of `dt`
    with pytest.raises(ValueError):
        SimulationConfig.from_dict(d)


def test_enum_serializes_as_plain_string():
    d = make().to_dict()
    assert d["integrator"] == "verlet"
    assert d["time_scale"] == "TDB"
    assert d["frame"] == "active_bodies_barycentric"
    assert d["bodies"] == ["Sun", "Earth"]  # JSON-friendly list, not tuple


def test_identical_configs_share_hash():
    assert make() == make()
    assert make().config_hash() == make().config_hash()


def test_dt_change_changes_hash():
    assert make(dt=60.0).config_hash() != make(dt=120.0).config_hash()


def test_all_field_changes_change_hash_except_none():
    # every declared config field is physics/numerics relevant
    assert make(integrator="rk4").config_hash() != make().config_hash()
    assert make(bodies=("Sun", "Earth", "Moon")).config_hash() != make().config_hash()
    assert make(duration=172800.0).config_hash() != make().config_hash()
    assert make(epoch_jd=2451546.0).config_hash() != make().config_hash()
    assert make(time_scale=TimeScale.TT).config_hash() != make().config_hash()
    assert make(frame=ReferenceFrame.SSB_ICRS).config_hash() != make().config_hash()
    assert make(guard_m=2.0).config_hash() != make().config_hash()
