"""
This module contains patches for some frameworks to make Motor-ODM work as one would
expect. Expect some more or less ugly hacks here...

Note that all patches are applied automatically at **import time**.
"""

from typing import Any

from .document import Document
from .helpers import monkey_patch


def patch_fastapi() -> None:
    """
    Patches the `FastAPI <https://fastapi.tiangolo.com>`_ framework to support models
    based on Pydantic. By default FastAPI routes handle Pydantic models specially. This
    patch removes the special case for subclasses of :class:`Document
    <motor_odm.document.Document>`.
    """
    import fastapi  # noqa

    @monkey_patch(fastapi.routing)
    def _prepare_response_content(res: Any, *args: Any, **kwargs: Any) -> Any:
        if isinstance(res, Document):
            return res
        return _prepare_response_content.original(res, **kwargs)  # type: ignore


try:
    patch_fastapi()
except ImportError:
    pass
