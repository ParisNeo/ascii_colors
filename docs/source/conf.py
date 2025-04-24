# conf.py
# (Keep the previous version with Furo theme, extensions, etc.)

import os
import sys
import toml
from datetime import datetime

# -- Path setup --------------------------------------------------------------
sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------
def get_project_meta():
    pyproject_path = os.path.abspath('../../pyproject.toml')
    if os.path.exists(pyproject_path):
        with open(pyproject_path, 'r') as f:
            data = toml.load(f)
        if 'project' in data:
            return data['project']
        elif 'tool' in data and 'poetry' in data['tool']:
            return data['tool']['poetry']
    return {}

project_meta = get_project_meta()
project = project_meta.get('name', 'ascii_colors')
author = ", ".join([a.get('name', '') for a in project_meta.get('authors', [{'name': 'Unknown'}])])
release = project_meta.get('version', '0.0.0')
copyright = f'{datetime.now().year}, {author}'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',      # Support Google and NumPy style docstrings
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.githubpages',
    'sphinx_copybutton',        # Add copy buttons to code blocks
    'myst_parser',              # Allow Markdown files
    # 'sphinx_autobuild',       # Usually run from command line, not needed in conf
]

templates_path = ['_templates']
exclude_patterns = []
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown', # If using myst_parser for .md files
}

# -- Options for HTML output -------------------------------------------------
html_theme = 'furo' # Use the Furo theme
html_static_path = ['_static']
# html_logo = "_static/logo.png" # Optional: Add a logo file
# html_favicon = "_static/favicon.ico" # Optional: Add a favicon

# Furo theme options
html_theme_options = {
    "source_repository": "https://github.com/ParisNeo/ascii_colors/",
    "source_branch": "main",
    "source_directory": "docs/source/",
    "light_css_variables": {
        "color-brand-primary": "#3498db", # Example: A light blue primary color
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
    'undoc-members': False, # Usually better to document explicitly
    'show-inheritance': True,
}
# Ensure type hints are used
autodoc_typehints = "description" # Show type hints in the description
# autodoc_typehints_description_target = "all" # Or 'documented'

# -- Napoleon settings (for Google/NumPy docstrings) -------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False

# -- Myst Parser Settings ----------------------------------------------------
myst_enable_extensions = [
    "colon_fence", # Allow ```python blocks
    "smartquotes",
    "deflist",
]
myst_heading_anchors = 3 # Auto-generate anchors for headings up to level 3