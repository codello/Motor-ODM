import pytest

from motor_odm import Document


def test_document():
    class Test(Document):
        class Mongo:
            collection = "test"

        field: str

    Test(field="")


def test_document_without_mongo_class():
    with pytest.raises(TypeError):

        class Test(Document):
            field: str


def test_abstract_document():
    class Abstract(Document, abstract=True):
        field: str

    with pytest.raises(TypeError):
        Abstract()


def test_abstract_document_with_collection():
    with pytest.raises(TypeError):

        class Abstract(Document, abstract=True):
            class Mongo:
                collection = "test"

            field: str


def test_abstract_subclass():
    class Abstract(Document, abstract=True):
        field: str

    class SubAbstract(Abstract, abstract=True):
        field2: str

    with pytest.raises(TypeError):
        Abstract()
    with pytest.raises(TypeError):
        SubAbstract()


def test_abstract_with_concrete_subclass():
    class Abstract(Document, abstract=True):
        field: str

    class Concrete(Abstract):
        class Mongo:
            collection = "concrete"

        field2: str

    with pytest.raises(TypeError):
        Abstract()

    Concrete(field="F", field2="G")


def test_mongo_without_id():
    class Test(Document):
        class Mongo:
            collection = "test"

        field: str

    test = Test(field="test")
    mongo = test.mongo()
    assert "id" not in mongo
    assert "_id" not in mongo
