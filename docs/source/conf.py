import os
import sys
import tomllib

# Get the absolute path to the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# Read version from pyproject.toml
pyproject_path = os.path.join(project_root, "pyproject.toml")
with open(pyproject_path, "rb") as f:
    pyproject_data = tomllib.load(f)

project = "ispawn"
copyright = "2025, jfouret"
author = "jfouret"

# Extract version from pyproject.toml
version = pyproject_data["project"]["version"]
release = version


sys.path.insert(0, os.path.abspath("../.."))

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx_click",
]

templates_path = ["_templates"]
exclude_patterns = []

language = "en"

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]

html_theme_options = {
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
        "json_url": "https://jfouret.github.io/ispawn/switcher.json",
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
