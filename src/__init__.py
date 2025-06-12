"""
src
This source code contains the building blocks for the IngestaDocumentalBC API interface.
Here offer the elements that are esencial for the main.py entry point.
"""

from .controllers import FastApiFramework, get_docs_uploaded_spec, post_documents_spec, dev_root_spec, pro_root_spec
from .utils import setup_logging
__all__ = [
    "FastApiFramework",
    "get_docs_uploaded_spec",
    "post_documents_spec",
    "dev_root_spec",
    "pro_root_spec",
    "setup_logging"
    ]
