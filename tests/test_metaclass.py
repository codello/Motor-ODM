import pytest

from motor_odm import Document


def test_create_valid_document():
    class Test(Document):
        class Mongo:
            collection = "test"

        field: str

    Test(field="")


def test_create_document_without_mongo_class():
    with pytest.raises(TypeError):

        class Test(Document):
            field: str


def test_mongo_without_id():
    class Test(Document):
        class Mongo:
            collection = "test"

        field: str

    test = Test(field="test")
    mongo = test.mongo()
    assert "id" not in mongo
    assert "_id" not in mongo
