import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import loop


def test_atomic_write_leaves_no_tmp(tmp_path):
    p = tmp_path / "s.json"
    loop.atomic_write_json(str(p), {"turn": 0})
    assert json.loads(p.read_text(encoding="utf-8")) == {"turn": 0}
    assert not os.path.exists(str(p) + ".tmp")


def test_load_state_defaults_when_missing(tmp_path):
    st = loop.load_state(str(tmp_path))
    assert st["turn"] == 0 and st["done"] is False and st["status"] == "new"
