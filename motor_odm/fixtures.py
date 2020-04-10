from typing import Any

from .document import Document
from .helpers import monkey_patch


def patch_fastapi() -> None:
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
