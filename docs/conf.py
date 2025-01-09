import os
import sys
from datetime import datetime

# Add the path to your Centum package
sys.path.append(os.path.relpath('..'))
sys.path.insert(0, os.path.abspath('..'))
sys.path.append(os.path.relpath('../centum/'))
sys.path.insert(0, os.path.abspath('../centum/'))

# Project information
project = "Centum Documentation"
author = "Your Name"
copyright = f"{datetime.now().year}, Your Name"
release = "1.0.0"

extensions = [
    "sphinx.ext.autodoc",       # Enable autogeneration of docs from code
    "sphinx.ext.autosummary",   # Optional: Creates summary tables
    "sphinx.ext.napoleon",      # For Google/NumPy-style docstrings
    "sphinx.ext.viewcode",      # Optional: Adds links to source code
]

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "private-members": False,
    "show-inheritance": True,
}

autosummary_generate = True  # Automatically create summary .rst files

# HTML theme
#html_theme = "sphinx_rtd_theme"
#html_static_path = ["_static"]

# Sphinx project configuration
templates_path = ["_templates"]
exclude_patterns = ["_build", "**.ipynb_checkpoints"]
source_suffix = ['.rst', '.md']
source_encoding = "utf-8"
master_doc = "index"
pygments_style = "default"
add_function_parentheses = False
