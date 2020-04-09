from typing import Any

from funcy import monkey

from .document import Document

__all__ = []

try:
    import fastapi


    @monkey(fastapi.routing)
    def _prepare_response_content(res: Any, *args, **kwargs):
        if isinstance(res, Document):
            return res
        return _prepare_response_content.original(res, **kwargs)
except ImportError:
    pass
