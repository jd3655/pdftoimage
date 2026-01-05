import importlib
import sys
import types

import pytest


@pytest.fixture
def mp(monkeypatch):
    """Load markitdown_processing with a stubbed processing module."""
    processing_stub = types.ModuleType("processing")
    processing_stub.MAX_TOTAL_FILES = 500
    monkeypatch.setitem(sys.modules, "processing", processing_stub)
    sys.modules.pop("markitdown_processing", None)
    module = importlib.import_module("markitdown_processing")
    try:
        yield module
    finally:
        sys.modules.pop("markitdown_processing", None)


class DummyMarkItDownNoEnablePlugins:
    def __init__(self, **kwargs):
        if "enable_plugins" in kwargs:
            raise TypeError("MarkItDown.__init__() got an unexpected keyword argument 'enable_plugins'")
        self.kwargs = kwargs


class DummyMarkItDownAlwaysTypeError:
    def __init__(self, **kwargs):
        raise TypeError("Some other init error")


def test_create_markitdown_instance_falls_back_without_plugins(monkeypatch, mp):
    monkeypatch.setattr(mp, "_load_markitdown", lambda: DummyMarkItDownNoEnablePlugins)
    options = mp.MarkItDownOptions(enable_plugins=True)

    instance = mp._create_markitdown_instance(options)

    assert isinstance(instance, DummyMarkItDownNoEnablePlugins)
    assert "enable_plugins" not in instance.kwargs


def test_create_markitdown_instance_raises_other_typeerror(monkeypatch, mp):
    monkeypatch.setattr(mp, "_load_markitdown", lambda: DummyMarkItDownAlwaysTypeError)
    options = mp.MarkItDownOptions()

    with pytest.raises(mp.MarkItDownError):
        mp._create_markitdown_instance(options)
