"""Preload the pinned NuNerZero ONNX assets used by Zink."""

from argparse import ArgumentParser
from pathlib import Path

from zink.extractor import DEFAULT_MODEL, DEFAULT_MODEL_REVISION


# Validate the inference assets after downloading the complete pinned snapshot.
# Recent Hub clients also verify published metadata files when loading offline.
_ONNX_ASSETS = (
    "added_tokens.json",
    "config.json",
    "gliner_config.json",
    "model.onnx",
    "special_tokens_map.json",
    "spm.model",
    "tokenizer.json",
    "tokenizer_config.json",
)


def main():
    """Print the cache key or download and verify the pinned model files."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache-key", action="store_true", help="Print the model cache key."
    )
    args = parser.parse_args()
    if args.cache_key:
        print(f"{DEFAULT_MODEL.replace('/', '--')}-{DEFAULT_MODEL_REVISION}")
        return

    from huggingface_hub import snapshot_download
    from huggingface_hub.constants import HF_HUB_OFFLINE

    model = Path(
        snapshot_download(
            repo_id=DEFAULT_MODEL,
            revision=DEFAULT_MODEL_REVISION,
            local_files_only=HF_HUB_OFFLINE,
        )
    )
    incomplete = [
        name
        for name in _ONNX_ASSETS
        if not (model / name).is_file() or not (model / name).stat().st_size
    ]
    if incomplete:
        raise SystemExit(
            f"Missing or empty ONNX assets in {model}: {', '.join(incomplete)}"
        )
    print(f"Prepared {DEFAULT_MODEL}@{DEFAULT_MODEL_REVISION} in {model}")


if __name__ == "__main__":
    main()
