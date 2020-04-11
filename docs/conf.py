# -- Path setup --------------------------------------------------------------

import os
import sys
from datetime import datetime

from pkg_resources import get_distribution

sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------

project = "Motor-ODM"
copyright = f"{datetime.now().year}, Kim Wittenburg"
author = "Kim Wittenburg"

release = get_distribution("motor_odm").version
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosummary",
    "sphinxcontrib.apidoc",
]

templates_path = ["templates"]

exclude_patterns = ["build", "Thumbs.db", ".DS_Store"]

warning_is_error = True

# -- Autodoc Options ---------------------------------------------------------

autodoc_member_order = "groupwise"

# -- APIDoc Options ----------------------------------------------------------

apidoc_module_dir = "../motor_odm"
apidoc_output_dir = "reference"
apidoc_separate_modules = True
apidoc_toc_file = False
apidoc_module_first = True
apidoc_extra_args = ["--templatedir", "templates"]

os.environ["SPHINX_APIDOC_OPTIONS"] = ",".join(
    ["members", "undoc-members", "show-inheritance"]
)
# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
extensions.append("sphinx_rtd_theme")

html_theme_options = {"collapse_navigation": False, "navigation_depth": 5}

# html_static_path = ["static"]

intersphinx_mapping = {
    "pymongo": ("https://pymongo.readthedocs.io/en/stable/", None),
    "py": ("https://docs.python.org/3/", None),
}
