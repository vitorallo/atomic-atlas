"""PyRIT PromptTarget implementations for agentic entry vectors.

Targets are imported lazily via ``__getattr__`` so that importing
``atomic_atlas.targets`` does not require PyRIT to be installed. PyRIT becomes
required only when a target is actually instantiated (which happens via
``runner.run_atomic`` / ``atomic-atlas exec``).
"""

from __future__ import annotations

from .base import AtomicAtlasTarget, PYRIT_AVAILABLE, PyRITNotInstalledError, require_pyrit

__all__ = [
    "AtomicAtlasTarget",
    "PYRIT_AVAILABLE",
    "PyRITNotInstalledError",
    "require_pyrit",
    "RAGCorpusTarget",
    "MCPServerTarget",
    "ToolResponseTarget",
    "DocumentUploadTarget",
    "WebhookTarget",
]


_LAZY_TARGETS = {
    "RAGCorpusTarget": ("rag_corpus", "RAGCorpusTarget"),
    "MCPServerTarget": ("mcp_server", "MCPServerTarget"),
    "ToolResponseTarget": ("tool_response", "ToolResponseTarget"),
    "DocumentUploadTarget": ("document_upload", "DocumentUploadTarget"),
    "WebhookTarget": ("webhook", "WebhookTarget"),
}


def __getattr__(name: str):
    if name in _LAZY_TARGETS:
        module_name, class_name = _LAZY_TARGETS[name]
        from importlib import import_module
        module = import_module(f".{module_name}", __name__)
        return getattr(module, class_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
