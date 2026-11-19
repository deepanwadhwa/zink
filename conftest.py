"""Keep feature tests independent of users' mappings and pipeline caches."""

import importlib
from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def isolate_zink_state(tmp_path, monkeypatch):
    """Restore singleton state and redirect persistent data for each test."""
    api = importlib.import_module("zink.zink")
    pipeline = importlib.import_module("zink.pipeline")
    paths = importlib.import_module("zink.utils.paths")
    mapping = importlib.import_module("zink.replacer.json_mapping")
    path = str(tmp_path / "mapping.json")
    for module in (api, pipeline, paths):
        monkeypatch.setattr(module, "get_default_mapping_path", lambda: path)
    monkeypatch.setattr(api, "_global_instance", pipeline.Pseudonymizer())
    pipeline.Pseudonymizer._cached_single_pass_extraction.cache_clear()
    mapping.load_mapping.cache_clear()
    yield
    pipeline.Pseudonymizer._cached_single_pass_extraction.cache_clear()
    mapping.load_mapping.cache_clear()


@pytest.fixture
def fake_extractor(monkeypatch):
    """Install a deterministic predictor without altering integration tests."""
    api = importlib.import_module("zink.zink")
    from zink.pipeline import Pseudonymizer

    def install(predict):
        extractor = SimpleNamespace(
            predict=lambda text, labels=None: predict(text, labels),
            predict2=lambda text, labels=None: predict(text, labels),
        )
        instance = Pseudonymizer(extractor=extractor)
        monkeypatch.setattr(api, "_global_instance", instance)
        return instance

    return install
