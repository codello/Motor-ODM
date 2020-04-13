import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from motor_odm import Document

pytestmark = pytest.mark.asyncio


def make_model():
    class User(Document):
        class Mongo:
            collection = "users"

        name: str

    return User


async def test_insert(db: AsyncIOMotorDatabase):
    User = make_model()
    user = User(name="Test")
    assert user.id is None
    result = await user.insert()
    db_data = [doc async for doc in db.users.find()]
    assert result is True
    assert len(db_data) == 1
    assert db_data[0]["name"] == "Test"
    assert user.id is not None


@pytest.mark.usefixtures("data")
async def test_insert_duplicate(db: AsyncIOMotorDatabase):
    User = make_model()
    user = await User.find_one({"name": "John"})
    user.name = "Johnny"
    result = await user.insert()
    assert result is False


async def test_insert_many(db: AsyncIOMotorDatabase):
    User = make_model()
    names = {"Test 1", "Test 2", "Test 3", "Test 4"}
    users = [User(name=name) for name in names]
    await User.insert_many(*users)
    db_data = [doc async for doc in db.users.find()]
    assert len(db_data) == 4
    assert set(data["name"] for data in db_data) == names
    assert all(user.id is not None for user in users)


@pytest.mark.usefixtures("data")
async def test_save():
    User = make_model()
    user = await User.find_one({"name": "John"})
    user.name = "Johnny"
    result = await user.save()
    assert result is True
    assert user.name == "Johnny"
    assert await User.count_documents() == 4


async def test_save_new(db: AsyncIOMotorDatabase):
    User = make_model()
    user = User(name="Johnny")
    assert await user.save() is True
    assert user.id is not None
    assert await User.count_documents() == 1


@pytest.mark.usefixtures("data")
async def test_update_existing():
    User = make_model()
    user = await User.find_one({"name": "John"})
    user.name = "Johnny"
    result = await user.save(upsert=False)
    assert result is True
    assert await User.count_documents() == 4


@pytest.mark.usefixtures("data")
async def test_upsert_new():
    User = make_model()
    user = User(name="Johnny")
    result = await user.save(upsert=False)
    assert result is False
    assert await User.count_documents() == 4


@pytest.mark.usefixtures("data")
async def test_reload():
    User = make_model()
    user = await User.find_one({"name": "John"})
    user.name = "Johnny"
    assert user.name == "Johnny"
    result = await user.reload()
    assert result is True
    assert user.name == "John"


@pytest.mark.usefixtures("data")
async def test_reload_deleted():
    User = make_model()
    user = await User.find_one_and_delete({"name": "John"})
    result = await user.reload()
    assert result is False


@pytest.mark.usefixtures("data")
async def test_delete_many():
    User = make_model()
    users = [user async for user in User.find({"admin": True})]
    result = await User.delete_many(*users)
    assert result == 2
    assert await User.count_documents() == 2
    assert await User.count_documents({"admin": True}) == 0


@pytest.mark.usefixtures("data")
async def test_find_all():
    User = make_model()
    users = [user async for user in User.find()]
    assert len(users) == 4


@pytest.mark.parametrize(
    "query,result",
    [
        ({"admin": True}, 2),
        ({"field": "any"}, 0),
        ({"name": "John"}, 1),
        ({"name": {"$in": ["John", "Jane"]}}, 2),
    ],
)
@pytest.mark.usefixtures("data")
async def test_find(query, result):
    User = make_model()
    users = [user async for user in User.find(query)]
    assert len(users) == result
    assert all(user.id is not None for user in users)


@pytest.mark.usefixtures("data")
async def test_find_one():
    User = make_model()
    user = await User.find_one({"name": "John"})
    assert user is not None
    assert user.id is not None
    assert user.name == "John"


async def test_find_one_by_id(db: AsyncIOMotorDatabase):
    User = make_model()
    inserted_id = (await db["users"].insert_one({"name": "Jake"})).inserted_id
    user = await User.find_one({"_id": inserted_id})
    assert user is not None
    assert user.id == inserted_id
    assert user.name == "Jake"


@pytest.mark.usefixtures("data")
async def test_find_one_absent():
    User = make_model()
    user = await User.find_one({"name": "Test"})
    assert user is None


@pytest.mark.usefixtures("data")
async def test_find_one_and_delete():
    User = make_model()
    user = await User.find_one_and_delete({"name": "John"})
    assert user is not None
    assert user.name == "John"
    assert await User.find_one({"name": "John"}) is None


@pytest.mark.parametrize(
    "doc,name", [(ReturnDocument.BEFORE, "John"), (ReturnDocument.AFTER, "Johnny")]
)
@pytest.mark.usefixtures("data")
async def test_find_one_and_replace(doc, name):
    User = make_model()
    replacement = User(name="Johnny")
    user = await User.find_one_and_replace(
        {"name": "John"}, replacement, return_document=doc
    )
    assert user.name == name
    assert await User.count_documents() == 4


@pytest.mark.parametrize(
    "doc,name", [(ReturnDocument.BEFORE, "John"), (ReturnDocument.AFTER, "Test")]
)
@pytest.mark.usefixtures("data")
async def test_find_one_and_update(doc, name):
    User = make_model()
    user = await User.find_one_and_update(
        {"name": "John"}, {"$set": {"name": "Test"}}, return_document=doc
    )
    assert user is not None
    assert user.id is not None
    assert user.name == name
    assert await User.count_documents() == 4


@pytest.mark.parametrize("doc", [ReturnDocument.BEFORE, ReturnDocument.AFTER])
@pytest.mark.usefixtures("data")
async def test_find_one_and_update_absent(doc):
    User = make_model()
    user = await User.find_one_and_update(
        {"name": "Johnny"}, {"$set": {"name": "Test"}}, return_document=doc
    )
    assert user is None


@pytest.mark.usefixtures("data")
async def test_find_one_and_upsert():
    User = make_model()
    user = await User.find_one_and_update(
        {"name": "Johnny"}, {"$set": {"name": "Test"}}, upsert=True
    )
    assert user is None
    assert await User.count_documents() == 5


@pytest.mark.usefixtures("data")
async def test_find_one_and_upsert_after():
    User = make_model()
    user = await User.find_one_and_update(
        {"name": "Johnny"},
        {"$set": {"name": "Test"}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    assert user is not None
    assert user.id is not None
    assert user.name == "Test"
    assert await User.count_documents() == 5


@pytest.mark.usefixtures("data")
async def test_count_documents(db: AsyncIOMotorDatabase):
    User = make_model()
    assert await User.count_documents() == await db.users.count_documents({})
