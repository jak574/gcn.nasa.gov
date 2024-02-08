# Copyright © 2023 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.

<<<<<<< HEAD
<<<<<<< HEAD:python/tests/across/test_env.py
from env import feature, get_features
=======

from env import feature, get_features  # type: ignore
>>>>>>> 7536c64 (Update unit tests.):python/tests/test_env.py
=======
from env import feature, get_features
>>>>>>> ab92ec3 (Revert change)


def test_features_undefined(monkeypatch):
    monkeypatch.delenv("GCN_FEATURES", raising=False)
    assert len(get_features()) == 0
    assert not feature("FOO")


def test_features_empty_string(monkeypatch):
    monkeypatch.setenv("GCN_FEATURES", "")
    assert len(get_features()) == 0
    assert not feature("FOO")


def test_features(monkeypatch):
    monkeypatch.setenv("GCN_FEATURES", ",,FOO,,bar,")
    assert len(get_features()) == 2
    assert feature("foo")
    assert feature("BAR")
    assert not feature("BAT")
