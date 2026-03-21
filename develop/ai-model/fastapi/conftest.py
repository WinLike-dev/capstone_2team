"""Root conftest.py — project-wide test fixtures and sys.modules stubs.

sentence_transformers is listed in requirements.txt but is a large optional
dependency not installed in the CI/test environment. We stub it here so that
any module that imports it at module level (app/core/lifespan.py) does not
raise ModuleNotFoundError during test collection.
"""
import sys
import types
from unittest.mock import MagicMock

# Stub sentence_transformers before any test module is collected.
if "sentence_transformers" not in sys.modules:
    _st_stub = types.ModuleType("sentence_transformers")
    _st_stub.SentenceTransformer = MagicMock()  # type: ignore[attr-defined]
    sys.modules["sentence_transformers"] = _st_stub
