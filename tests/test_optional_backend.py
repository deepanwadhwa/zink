"""Check import behavior without downloading or initializing real models."""

import subprocess
import sys

import pytest


@pytest.mark.parametrize("missing", ["gliner", "onnxruntime"])
def test_missing_backend_warns_and_inference_fails(missing):
    script = f"import sys; sys.modules[{missing!r}] = None\n" + '''
import sys
import warnings
with warnings.catch_warnings(record=True) as captured:
    warnings.simplefilter("always")
    import zink
assert any("zink[cpu]" in str(w.message) for w in captured)
assert zink.prep("Alice", ["Alice"]) == "*Alice*"
try:
    zink.redact("Alice", categories=("person",))
except ImportError as error:
    assert "zink[cpu]" in str(error)
else:
    raise AssertionError("Inference should require a backend")
'''
    subprocess.run([sys.executable, "-c", script], check=True)


def test_present_backend_does_not_emit_missing_dependency_warning():
    script = '''
import sys
import types
import warnings
gliner = types.ModuleType("gliner")
class GLiNER:
    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        return cls()
gliner.GLiNER = GLiNER
sys.modules["gliner"] = gliner
sys.modules["onnxruntime"] = types.ModuleType("onnxruntime")
with warnings.catch_warnings(record=True) as captured:
    warnings.simplefilter("always")
    import zink
assert not any("Zink inference dependencies" in str(w.message) for w in captured)
'''
    subprocess.run([sys.executable, "-c", script], check=True)
