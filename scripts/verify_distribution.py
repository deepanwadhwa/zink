"""Smoke-test a Zink distribution installed with its server extra and httpx.

Run this script with the installed environment's Python and -I from a directory
outside the source checkout. Use --cpu with a populated model cache.
"""

import sys
import warnings
from argparse import ArgumentParser
from importlib.metadata import version
from importlib.util import find_spec
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


def predict(text, labels=None):
    """Supply synthetic detections for the installed-package smoke tests."""
    entities = []
    for original, label in (
        ("Alice", "person"),
        ("Bob", "person"),
        ("Testmobile", "car brand"),
    ):
        start = text.find(original)
        if start >= 0 and label in labels:
            entities.append(
                {
                    "text": original,
                    "label": label,
                    "start": start,
                    "end": start + len(original),
                    "score": 1.0,
                }
            )
    return sorted(entities, key=lambda entity: entity["start"])


def main():
    """Verify package metadata, resources, transformation and HTTP behavior."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Expected package version.")
    parser.add_argument(
        "--cpu", action="store_true", help="Also use the real CPU model."
    )
    args = parser.parse_args()

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        import zink

    installed = Path(zink.__file__).resolve()
    checkout = Path(__file__).resolve().parents[1]
    assert not installed.is_relative_to(checkout / "zink"), installed
    assert installed.is_relative_to(Path(sys.prefix).resolve()), installed
    assert version("zink") == zink.__version__ == args.version
    assert {"gliner", "onnxruntime"}.isdisjoint(sys.modules)
    if not all(find_spec(name) for name in ("gliner", "onnxruntime")):
        assert any("zink[cpu]" in str(warning.message) for warning in captured)
        try:
            zink.redact("Alice arrived.", categories=["person"])
        except ImportError as error:
            assert "zink[cpu]" in str(error)
        else:
            raise AssertionError(
                "Expected installation guidance for the missing CPU backend"
            )

    from fastapi.testclient import TestClient

    from zink.pipeline import Pseudonymizer
    from zink.replacer.json_mapping import load_mapping
    from zink.server import app

    extractor = SimpleNamespace(predict2=predict, predict=predict)
    protected = zink.prep("Alice met Bob.", ["Alice", "Alice met"])
    redacted = zink.redact(protected, ["person"], extractor=extractor)
    assert redacted.anonymized_text == "Alice met person_REDACTED."
    assert redacted.replacements[0].start == 10

    custom = zink.replace_with_my_data(
        "Alice met Bob.",
        ["person"],
        user_replacements={"person": ["Eve"]},
        extractor=extractor,
    )
    assert custom.anonymized_text == "Eve met Eve."
    assert custom.features["num_replacements"] == 2

    def predict_jordan(text, labels=None):
        return [
            {
                "text": "Jordan",
                "label": label,
                "start": start,
                "end": start + 6,
                "score": 1.0,
            }
            for start, label in ((0, "person"), (11, "location"))
        ]

    jordan_extractor = SimpleNamespace(predict2=predict_jordan, predict=predict_jordan)
    for replace in (zink.replace, zink.replace_with_my_data):
        for options, expected in (
            ({}, "Alice met Alice."),
            ({"consistency_scope": "text"}, "Alice met Alice."),
            ({"consistency_scope": "label"}, "Alice met Venice."),
            ({"ensure_consistency": False}, "Alice met Venice."),
        ):
            result = replace(
                "Jordan met Jordan.",
                categories=("person", "location"),
                user_replacements={"person": "Alice", "location": "Venice"},
                extractor=jordan_extractor,
                **options,
            )
            assert result.anonymized_text == expected, (
                replace.__name__,
                options,
                result,
            )

    bundled = set(load_mapping()["car brand"])
    fallback = zink.replace("Testmobile arrived.", ["car brand"], extractor=extractor)
    assert fallback.anonymized_text in {f"{name} arrived." for name in bundled}
    assert fallback.replacements[0]["source"] == "json"

    with patch("zink.zink._global_instance", Pseudonymizer(extractor=extractor)):
        with TestClient(app) as client:
            assert client.get("/health").json() == {
                "status": "ok",
                "version": args.version,
            }
            response = client.post(
                "/redact", json={"text": "Alice arrived.", "labels": ["person"]}
            )
            assert response.status_code == 200, response.text
            data = response.json()
            assert data["anonymized_text"] == "person_REDACTED arrived."
            assert data["replacements"][0]["original"] == "Alice"

    if args.cpu:
        result = zink.redact("Alice arrived.", categories=["person"])
        assert result.anonymized_text == "person_REDACTED arrived.", result

    print(f"Verified Zink {args.version} at {installed}")


if __name__ == "__main__":
    main()
