"""
Sphinx configuration for Global Exchange docs (minimal MVP).
"""
from __future__ import annotations

import os
import sys

# Add project root to path so autodoc can import modules if needed
sys.path.insert(0, os.path.abspath(".."))  # docs/ -> project root is one level up
sys.path.insert(0, os.path.abspath("../../"))  # docs/source -> project root

# Best-effort Django setup for autodoc (kept optional)
try:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "global_exchange.settings")
    import django  # type: ignore

    django.setup()
except Exception:
    # Building basic docs should not fail if Django isn't configured
    pass

# -- Project information -----------------------------------------------------

project = "Global Exchange"
author = "Global Exchange Team"
release = "0.1.0"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # Google/Numpy-style docstrings
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []

# Cross-project references
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    # Django object inventory; safe to leave even if offline
    "django": ("https://docs.djangoproject.com/en/stable/", None),
}

# -- Options for HTML output -------------------------------------------------

html_theme = "alabaster"
html_static_path = ["_static"]

