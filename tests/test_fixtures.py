import fastapi
from pydantic import BaseModel

from motor_odm import Document, fixtures  # noqa: F401,F403


def test_fastapi_fix():
    class SomeModel(BaseModel):
        pass

    class SomeDoc(Document):
        class Mongo:
            collection = "test"

    model = SomeModel()
    doc = SomeDoc()
    assert fastapi.routing._prepare_response_content(doc, exclude_unset=False) is doc
    assert fastapi.routing._prepare_response_content(model, exclude_unset=False) == {}
