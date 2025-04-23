# conf.py

import os
import sys
import toml  # Import the toml library
from datetime import datetime
# -- Path setup --------------------------------------------------------------
# Point Sphinx to the project root directory to find the source code
sys.path.insert(0, os.path.abspath('../..')) # Go up two levels from source/ to project root

# -- Project information -----------------------------------------------------
# Load project metadata from pyproject.toml
def get_project_meta():
    """Reads project metadata from pyproject.toml"""
    pyproject_path = os.path.abspath('../../pyproject.toml')
    if os.path.exists(pyproject_path):
        with open(pyproject_path, 'r') as f:
            data = toml.load(f)
        # Check both potential locations for project metadata
        if 'project' in data:
            return data['project']
        elif 'tool' in data and 'poetry' in data['tool']: # Support poetry too if used
            return data['tool']['poetry']
    return {} # Return empty dict if file not found or no metadata

project_meta = get_project_meta()

project = project_meta.get('name', 'ascii_colors')
author = ", ".join([a.get('name', '') for a in project_meta.get('authors', [{'name': 'Unknown'}])]) # Handle author format
release = project_meta.get('version', '0.0.0') # Get version from pyproject.toml
copyright = f'{datetime.now().year}, {author}' # Dynamic copyright year

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',      # Include documentation from docstrings
    'sphinx.ext.napoleon',     # Support Google and NumPy style docstrings
    'sphinx.ext.viewcode',     # Add links to highlighted source code
    'sphinx.ext.intersphinx',  # Link to other projects' documentation (e.g., Python)
    'sphinx.ext.githubpages',  # Helps with GitHub Pages deployment (_static path etc.)
    'sphinx_autobuild',        # For auto-reloading local builds
    'sphinx_copybutton',
    'myst_parser'
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# Use the Furo theme
html_theme = 'furo'
html_static_path = ['_static']
# html_logo = "_static/logo.png"  # Optional: Add a logo file here
# html_favicon = "_static/favicon.ico" # Optional: Add a favicon

# Theme options are theme-specific
html_theme_options = {
    "source_repository": "https://github.com/ParisNeo/ascii_colors/",
    "source_branch": "main", # Or your primary branch name
    "source_directory": "docs/source/",
}

# -- Intersphinx configuration ---------------------------------------------
# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

# -- Autodoc configuration -------------------------------------------------
autodoc_member_order = 'bysource' # Order members by source code order
autodoc_default_options = {
    'members': True,
    'undoc-members': True, # Include members without docstrings (use with caution)
    'show-inheritance': True,
}
# Optional: Tell autodoc to mock imports if some heavy dependencies aren't needed for docs build
# autodoc_mock_imports = ["dependency1", "dependency2"]