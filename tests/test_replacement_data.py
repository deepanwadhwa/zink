import subprocess
import sys
from types import SimpleNamespace

import zink
from zink.replacer.json_mapping import load_mapping


def test_public_replacement_uses_bundled_fallback_when_enabled():
    original = "Prototype fastener"

    def replace(label, *, use_json_mapping):
        def extract(text, labels):
            assert text == original and labels == (label,)
            return [
                {
                    "start": 0,
                    "end": len(original),
                    "label": label,
                    "text": original,
                    "score": 0.95,
                }
            ]

        return zink.replace(
            original,
            categories=(label,),
            extractor=SimpleNamespace(predict2=extract),
            use_json_mapping=use_json_mapping,
        )

    known = replace("tool", use_json_mapping=True)
    assert known.anonymized_text in load_mapping()["tool"]
    assert known.anonymized_text != original
    assert known.replacements[0]["source"] == "json"

    unknown = replace("zz-custom-unmapped-label", use_json_mapping=True)
    assert unknown.anonymized_text == "[REDACTED]"
    assert unknown.replacements[0]["source"] == "json"

    disabled = replace("tool", use_json_mapping=False)
    assert disabled.anonymized_text == "[REDACTED]"
    assert disabled.replacements[0]["source"] == "default"


def test_import_and_bundled_fallback_create_no_cache_files(tmp_path):
    script = """
import sys
from pathlib import Path
from unittest.mock import patch

home = Path(sys.argv[1])
with patch.object(Path, 'home', return_value=home):
    import zink
    assert 'zink.data' not in sys.modules
    assert list(home.iterdir()) == []
    from zink.replacer.json_mapping import JsonMappingReplacementStrategy
    value = JsonMappingReplacementStrategy('tool').replace({'text': 'Prototype fastener'})
    assert value != 'Prototype fastener' and value != '[REDACTED]'
    assert list(home.iterdir()) == []
"""
    subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)], check=True, timeout=45
    )
