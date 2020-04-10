# -- Path setup --------------------------------------------------------------

import os
import sys

from setuptools_scm import get_version
from setuptools_scm.version import ScmVersion, guess_next_dev_version

sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------

project = 'Motor-ODM'
copyright = '2020, Kim Wittenburg'
author = 'Kim Wittenburg'


def format_version(v: ScmVersion):
    version_string: str = guess_next_dev_version(v)
    components = version_string.split('.')
    return '.'.join(components[0:2])


version = get_version(root='..', relative_to=__file__, version_scheme=format_version, local_scheme='no-local-version')
release = get_version(root='..', relative_to=__file__, local_scheme="no-local-version")

# -- General configuration ---------------------------------------------------

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx']

exclude_patterns = ['build', 'Thumbs.db', '.DS_Store']

warning_is_error = True

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
extensions.append("sphinx_rtd_theme")

html_static_path = ['static']

intersphinx_mapping = {
    'pymongo': ('https://pymongo.readthedocs.io/en/stable/', None),
    'py': ('https://docs.python.org/3/', None),
}
