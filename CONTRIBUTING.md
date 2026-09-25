# Contributing to Zink

Thanks for helping improve Zink. Please follow the [code of conduct](CODE_OF_CONDUCT.md).

## Development setup

Use Python 3.11 or newer. From a clone of this repository:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[cpu]'
python -m pip install pytest sphinx sphinx-rtd-theme
```

On Windows, activate the virtual environment with `.venv\Scripts\activate`.
The CPU extra installs GLiNER and ONNX Runtime. The first import downloads the
default model, so allow network access and enough disk space for it.

## Checks

```bash
pytest zink/tests
sphinx-build -b html -W --keep-going docs/source docs/build/html
```

Tests and documentation builds also run on pull requests. When changing
behavior, add a test covering the use case. When changing the public API,
update its docstring and the relevant tutorial or README example.

## Proposing a change

Open an issue describing a bug or proposed feature, including a minimal
reproduction for bugs. Avoid posting real sensitive text or mapping files.
Submit a focused pull request and explain the change and checks run. We
welcome documentation, tests and code contributions.
