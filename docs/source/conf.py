# conf.py
# Sphinx configuration for the ascii_colors project documentation.

import os
import sys
from datetime import datetime

import toml

# -- Path setup --------------------------------------------------------------
# Make the package importable so autodoc can introspect it from the repo root.
sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------
def get_project_meta():
    pyproject_path = os.path.abspath('../../pyproject.toml')
    if os.path.exists(pyproject_path):
        with open(pyproject_path, 'r') as f:
            data = toml.load(f)
        if 'project' in data:
            return data['project']
        if 'tool' in data and 'poetry' in data['tool']:
            return data['tool']['poetry']
    return {}

project_meta = get_project_meta()
project = project_meta.get('name', 'ascii_colors')
author = ", ".join(
    [a.get('name', '') for a in project_meta.get('authors', [{'name': 'Unknown'}])]
)
release = project_meta.get('version', '0.0.0')
copyright = f'{datetime.now().year}, {author}'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',       # Google / NumPy docstrings
    'sphinx.ext.viewcode',       # Link to highlighted source
    'sphinx.ext.intersphinx',    # Cross-reference stdlib docs
    'sphinx.ext.githubpages',    # Emit .nojekyll for GitHub Pages
    'sphinx_copybutton',         # Copy button on code blocks
    'myst_parser',               # Markdown support
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}
language = 'en'

# -- Options for HTML output -------------------------------------------------
html_theme = 'furo'
html_static_path = ['_static']
html_css_files = ['custom.css']
html_baseurl = 'https://parisneo.github.io/ascii_colors/'
html_title = f"{project} documentation"

html_theme_options = {
    "source_repository": "https://github.com/ParisNeo/ascii_colors/",
    "source_branch": "main",
    "source_directory": "docs/source/",
    "light_css_variables": {
        "color-brand-primary": "#3498db",
        "color-brand-content": "#2c3e50",
    },
    "dark_css_variables": {
        "color-brand-primary": "#3498db",
        "color-brand-content": "#ecf0f1",
    },
}

# -- Intersphinx configuration ---------------------------------------------
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

# -- Autodoc configuration -------------------------------------------------
autodoc_member_order = 'bysource'
autodoc_default_options = {
    'members': True,
    'undoc-members': False,
    'show-inheritance': True,
}
autodoc_typehints = "description"

# -- Napoleon settings -----------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False

# -- Myst Parser Settings --------------------------------------------------
myst_enable_extensions = [
    "colon_fence",
    "smartquotes",
    "deflist",
]
myst_heading_anchors = 3