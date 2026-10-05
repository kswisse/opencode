import pytest

from solar_ephemeris.physics.bodies import Body, BodyRegistry, UnknownBodyError


def test_resolve_preserves_caller_order():
    reg = BodyRegistry.default()
    got = reg.resolve(["Moon", "Sun", "Earth"])
    assert tuple(b.name for b in got) == ("Moon", "Sun", "Earth")
    assert got[0].gm < got[1].gm  # Moon GM < Sun GM, order not sorted


def test_resolve_unknown_body_raises():
    reg = BodyRegistry.default()
    with pytest.raises(UnknownBodyError):
        reg.resolve(["Sun", "PlanetNine"])


def test_resolve_duplicate_raises():
    reg = BodyRegistry.default()
    with pytest.raises(ValueError):
        reg.resolve(["Sun", "Earth", "Sun"])


def test_custom_registry_needs_no_defaults():
    reg = BodyRegistry(gm_map={"StarA": 1.0e17, "StarB": 2.0e16})
    got = reg.resolve(["StarB", "StarA"])
    assert [b.gm for b in got] == [2.0e16, 1.0e17]
    with pytest.raises(UnknownBodyError):
        reg.get("Sun")


def test_default_registry_contains_major_bodies():
    reg = BodyRegistry.default()
    for name in ("Sun", "Earth", "Moon"):
        assert name in reg
        assert reg.get(name).gm > 0.0
        assert len(reg.get(name).source) > 10  # provenance carried through


def test_register_rejects_duplicates():
    reg = BodyRegistry()
    reg.register("X", 1.0)
    with pytest.raises(ValueError):
        reg.register("X", 2.0)


def test_body_rejects_nonpositive_gm():
    with pytest.raises(ValueError):
        Body(name="Bad", gm=0.0)
    with pytest.raises(ValueError):
        Body(name="Bad", gm=-1.0)


def test_empty_name_rejected():
    with pytest.raises(ValueError):
        Body(name="", gm=1.0)
