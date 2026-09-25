"""Sphinx configuration for Zink."""

from importlib.metadata import version as package_version

project = "Zink"
copyright = "2025, Deepan Wadhwa"
author = "Deepan Wadhwa"
release = package_version("zink")

extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "sphinx.ext.viewcode"]
html_theme = "sphinx_rtd_theme"
language = "en"

# Documentation imports the base package only; model inference is not needed.
autodoc_mock_imports = ["gliner"]
