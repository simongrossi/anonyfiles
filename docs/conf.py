# Configuration file for the Sphinx documentation builder.

import os
import sys

# Ajoute la racine du projet au path pour que Sphinx puisse trouver les modules Python
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------

project = 'Anonyfiles'
copyright = '2026, Simon Grossi'
author = 'Simon Grossi'
release = '0.1.0'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',   # Génère la doc à partir des docstrings
    'sphinx.ext.napoleon',  # Permet de comprendre les docstrings style Google
    'sphinx.ext.viewcode',  # Ajoute des liens vers le code source
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
language = 'fr'

# -- Options for HTML output -------------------------------------------------

html_theme = 'furo'
html_static_path = ['_static']
html_title = "Documentation Anonyfiles"