# Contributing to Zink

Thanks for helping improve Zink. Please follow the [code of conduct](CODE_OF_CONDUCT.md).

## Development setup

Use Python 3.11 or newer. From a clone of this repository:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[cpu,server,test]'
python -m pip install build ruff sphinx sphinx-rtd-theme
```

On Windows, activate the virtual environment with `.venv\Scripts\activate`.
The CPU extra installs GLiNER and ONNX Runtime. The first inference downloads
the default model (approximately 2 GB) when it is missing from the local
cache. The integration tests need that model. To run them offline, initialize
it first while online with `python -c 'import zink; zink.redact("Alice is here.")'`.

## Checks

```bash
python -m ruff check .
python -m pytest -m "not integration"
python -m pytest -m integration
python -m pytest -m "not integration" --cov=zink --cov-report=term-missing
python -m sphinx -b html -W --keep-going docs/source docs/build/html
python -m build
```

The first pytest command runs the deterministic unit, API, and example tests
without downloading a model. The second runs the real-model CPU tests.
Both run on pull requests. When changing behavior, add a test covering the
use case. When changing the public API, update its docstring and any affected
tutorial or README example.

## Proposing a change

Open an issue describing a bug or proposed feature, including a minimal
reproduction for bugs. Avoid posting real sensitive text or mapping files.
Submit a focused pull request and explain the change and checks run. We
welcome documentation, tests and code contributions.
