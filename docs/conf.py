# conf.py for Sphinx Configuration

import os
import sys
import sphinx_gallery

# Add the current directory to the sys.path
sys.path.insert(0, os.path.abspath('.'))

# -- Project information -----------------------------------------------------
project = 'Centum'
author = 'Developers'
description = 'Documentation for the Centum package'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx_gallery.gen_gallery',  # Enable sphinx-gallery
]

# -- Sphinx-Gallery configuration -------------------------------------------
sphinx_gallery_conf = {
    'examples_dirs': '../examples',  # Adjust to where your example notebooks are located
    'gallery_dirs': '_gallery',   # The directory to save gallery content
    'download_all_examples': True,  # Enable downloading of all examples in the gallery
}

# -- Autosummary configuration ----------------------------------------------
autosummary_generate = True  # Automatically generate summary tables

# -- HTML output configuration ----------------------------------------------
html_theme = 'alabaster'
