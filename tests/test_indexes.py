import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import IndexModel

from motor_odm import Document

pytestmark = pytest.mark.asyncio


async def make_model(drop: bool = True, **kwargs):
    class User(Document):
        class Mongo:
            collection = "users"
            indexes = [IndexModel("name", **kwargs)]

    await User.ensure_indexes(drop=drop)
    return User


async def test_create_simple_indexes(db: AsyncIOMotorDatabase):
    class User(Document):
        class Mongo:
            collection = "users"
            indexes = [
                IndexModel("name"),
            ]

        name: str

    await User.ensure_indexes()
    assert len(await User.collection().index_information()) == 2


async def test_create_multiple_indexes(db: AsyncIOMotorDatabase):
    class User(Document):
        class Mongo:
            collection = "users"
            indexes = [IndexModel("name"), IndexModel("age")]

    await User.ensure_indexes()
    assert len(await User.collection().index_information()) == 3


async def test_add_index(db: AsyncIOMotorDatabase):
    await make_model()

    class User2(Document):
        class Mongo:
            collection = "users"
            indexes = [IndexModel("name"), IndexModel("age")]

    await User2.ensure_indexes()
    indexes = await User2.collection().index_information()
    assert len(indexes) == 3


async def test_modify_index(db: AsyncIOMotorDatabase):
    await make_model()
    User2 = await make_model(name="Extra", unique=True)
    indexes = await User2.collection().index_information()
    assert "Extra" in indexes
    assert indexes["Extra"]["unique"] is True


async def test_drop_index(db: AsyncIOMotorDatabase):
    class User(Document):
        class Mongo:
            collection = "users"
            indexes = [IndexModel("name"), IndexModel("age")]

    await User.ensure_indexes()
    await make_model()
    indexes = await User.collection().index_information()
    assert len(indexes) == 2


async def test_no_drop_index(db: AsyncIOMotorDatabase):
    class User(Document):
        class Mongo:
            collection = "users"
            indexes = [IndexModel("name"), IndexModel("age")]

    await User.ensure_indexes()
    await make_model(drop=False)
    indexes = await User.collection().index_information()
    assert len(indexes) == 3
