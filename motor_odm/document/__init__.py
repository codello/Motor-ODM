"""This package contains classes and functions to work with MongoDB documents."""

from .base import MongoDocument  # noqa: F401
from .document import Document  # noqa: F401
from .view import ComputedDocument  # noqa: F401

__all__ = ["MongoDocument", "Document", "ComputedDocument"]
