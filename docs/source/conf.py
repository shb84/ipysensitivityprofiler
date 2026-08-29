"""Sphinx configuration file."""

import re
from pathlib import Path

import tomllib

import ipysensitivityprofiler

SRC_DOCS = Path(__file__).parent
DOCS = SRC_DOCS.parent
ROOT = DOCS.parent
SRC = ROOT / "src"
PPT = ROOT / "pyproject.toml"
PPT_DATA = tomllib.loads(PPT.read_text(encoding="utf-8"))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = PPT_DATA["project"]["name"]
slug = re.sub(r"\W+", "-", project.lower())
authors = [author["name"] for author in PPT_DATA["project"]["authors"]]
release = ipysensitivityprofiler.__version__
copyright = "2024, Steven H. Berguin"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx_rtd_theme",
    "sphinx_copybutton",
    "sphinx_design",
]
templates_path = ["_templates"]
html_static_path = ["_static"]
master_doc = "index"
source_suffix = ".rst"
exclude_patterns = []

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
    "show-inheritance": True,
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "logo_only": False,
    "prev_next_buttons_location": "bottom",
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 2,
    "includehidden": True,
}
html_context = {
    "display_github": True,  # Integrate GitHub
    "github_user": "shb84",  # Username
    "github_repo": "ipysensitivityprofiler",  # Repo name
    "github_version": "main",  # Version
    "conf_py_path": "/docs/source/",  # Path in the checkout to the docs root
}
