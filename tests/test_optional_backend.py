"""Check optional inference and model initialization in fresh processes."""

import subprocess
import sys

import pytest


def _run(script, *args):
    subprocess.run([sys.executable, "-c", script, *args], check=True, timeout=45)


@pytest.mark.parametrize("missing", ["gliner", "onnxruntime"])
def test_missing_backend_warns_and_inference_fails(missing, tmp_path):
    _run(
        """
import sys
import types
import warnings
from pathlib import Path
from unittest.mock import patch

missing = sys.argv[1]
other = "onnxruntime" if missing == "gliner" else "gliner"
sys.modules[missing] = None
sys.modules[other] = types.ModuleType(other)

with patch.object(Path, "home", return_value=Path(sys.argv[2])):
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        import zink
    assert any(
        "zink[cpu]" in str(w.message) and "zink[gpu]" in str(w.message)
        for w in captured
    )
    assert zink.prep("Alice", ["Alice"]) == "*Alice*"
    assert Path(zink.where_mapping_file()).is_relative_to(sys.argv[2])
    for inference, kwargs in [
        (zink.redact, {}),
        (zink.replace, {}),
        (zink.replace_with_my_data, {"user_replacements": {"person": "Ana"}}),
    ]:
        try:
            inference("Alice", categories=("person",), **kwargs)
        except ImportError as error:
            assert "zink[cpu]" in str(error) and "zink[gpu]" in str(error)
        else:
            raise AssertionError(f"{inference.__name__} should require a backend")
""",
        missing,
        str(tmp_path),
    )


def test_installed_backend_is_not_imported_by_import_or_utilities(tmp_path):
    for module in ("gliner", "onnxruntime"):
        (tmp_path / f"{module}.py").write_text(
            f'raise AssertionError("Unexpected import of {module}")\n', encoding="utf-8"
        )
    _run(
        """
import sys
import warnings
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, sys.argv[1])
with patch.object(Path, "home", return_value=Path(sys.argv[1])):
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        import zink
    assert not any("Zink inference dependencies" in str(w.message) for w in captured)
    assert zink.prep("Alice", ["Alice"]) == "*Alice*"
    expected = Path(sys.argv[1]) / ".zink" / "mapping.json"
    assert Path(zink.where_mapping_file()) == expected
    expected.write_text("{}", encoding="utf-8")
    zink.refresh_mapping_file()
    assert not expected.exists()
    assert "gliner" not in sys.modules
    assert "onnxruntime" not in sys.modules
""",
        str(tmp_path),
    )


def test_first_inference_initializes_once_across_parallel_requests(tmp_path):
    _run(
        """
import sys
import types
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Event
from unittest.mock import patch

calls = []
loader_entered = Event()
both_requests_started = Barrier(2)
second_request_started = Event()

class GLiNER:
    @classmethod
    def from_pretrained(cls, model, **options):
        calls.append((model, options))
        loader_entered.set()
        assert second_request_started.wait(10)
        return cls()

    def predict_entities(self, text, labels, **_kwargs):
        if text.isspace():
            return []
        return [{"start": 0, "end": len(text), "text": text, "label": labels[0], "score": 1}]

gliner = types.ModuleType("gliner")
gliner.GLiNER = GLiNER
sys.modules["gliner"] = gliner
sys.modules["onnxruntime"] = types.ModuleType("onnxruntime")

with patch.object(Path, "home", return_value=Path(sys.argv[1])):
    import zink
    from zink.extractor import DEFAULT_MODEL, DEFAULT_MODEL_REVISION

    assert calls == []

    def redact(text):
        both_requests_started.wait(timeout=10)
        if text == "Bob":
            assert loader_entered.wait(10)
            second_request_started.set()
        return zink.redact(text, categories=("person",), use_cache=False)

    with ThreadPoolExecutor(max_workers=2) as executor:
        alice = executor.submit(redact, "Alice")
        bob = executor.submit(redact, "Bob")
        assert alice.result(15).replacements[0].original == "Alice"
        assert bob.result(15).replacements[0].original == "Bob"

    result = zink.replace_with_my_data(
        "Cara", categories=("person",), user_replacements={"person": "Ana"}
    )
    assert result.anonymized_text == "Ana"
    assert calls == [(
        DEFAULT_MODEL,
        {
            "revision": DEFAULT_MODEL_REVISION,
            "load_onnx_model": True,
            "load_tokenizer": True,
            "local_files_only": os.environ.get(
                "HF_HUB_OFFLINE", os.environ.get("TRANSFORMERS_OFFLINE", "")
            ).upper() in {"1", "ON", "YES", "TRUE"},
        },
    )]
""",
        str(tmp_path),
    )


def test_failed_model_load_can_retry_and_preserves_custom_revision(tmp_path):
    _run(
        """
import sys
import types
from pathlib import Path
from unittest.mock import patch

attempts = []

class GLiNER:
    @classmethod
    def from_pretrained(cls, model, **options):
        attempts.append((model, options["revision"]))
        if len(attempts) == 1:
            raise RuntimeError("model unavailable")
        return cls()

    def predict_entities(self, text, labels, **_kwargs):
        return []

gliner = types.ModuleType("gliner")
gliner.GLiNER = GLiNER
sys.modules["gliner"] = gliner
sys.modules["onnxruntime"] = types.ModuleType("onnxruntime")

with patch.object(Path, "home", return_value=Path(sys.argv[1])):
    from zink.extractor import EntityExtractor

    extractor = EntityExtractor("owner/custom-model", model_revision="release-1")
    assert extractor.predict2("Alice", labels=[]) == []
    assert attempts == []
    try:
        extractor.predict2("Alice")
    except RuntimeError as error:
        assert str(error) == "model unavailable"
    else:
        raise AssertionError("Model load error must be visible")
    assert extractor.predict2("Alice") == []
    assert extractor.predict2("Bob") == []
    assert attempts == [("owner/custom-model", "release-1")] * 2
""",
        str(tmp_path),
    )
