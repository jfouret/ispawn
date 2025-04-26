# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ispawn'
copyright = '2025, jfouret'
author = 'jfouret'

version = '0.2.14'
release = '0.2.14'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Add the project root directory to the Python path so Sphinx can find the module
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx_click',
]

templates_path = ['_templates']
exclude_patterns = []

language = 'en'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']

# -- PyData theme settings ---------------------------------------------------
html_theme_options = {
    # Navigation bar
    "logo": {
        "text": project,
    },
    "use_edit_page_button": False,
    "show_prev_next": True,
    "navbar_start": ["navbar-logo"],
    "navbar_center": ["navbar-nav"],
    "navbar_end": ["version-switcher", "navbar-icon-links"],
    
    # Version switcher
    "switcher": {
        "json_url": "/switcher.json",  # Root URL of the GitHub Pages site
        "version_match": version,
    },
    
    # Theme options
    "show_toc_level": 2,
    "navigation_depth": 4,
    "collapse_navigation": True,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/jfouret/ispawn",
            "icon": "fab fa-github-square",
            "type": "fontawesome",
        },
    ],
}
