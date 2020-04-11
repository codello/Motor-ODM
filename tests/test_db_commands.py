import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase

from motor_odm import Document

pytestmark = pytest.mark.asyncio


def make_model():
    class User(Document):
        class Mongo:
            collection = "users"

        name: str

    return User


async def test_insert_single(db: AsyncIOMotorDatabase):
    User = make_model()
    user = User(name="Test")
    await user.insert()
    db_data = [doc async for doc in db.users.find()]
    assert len(db_data) == 1
    assert db_data[0]["name"] == "Test"


async def test_insert_many(db: AsyncIOMotorDatabase):
    User = make_model()
    names = {"Test 1", "Test 2", "Test 3", "Test 4"}
    users = [User(name=name) for name in names]
    await User.insert_many(*users)
    db_data = [doc async for doc in db.users.find()]
    assert len(db_data) == 4
    assert set(data["name"] for data in db_data) == names


@pytest.mark.usefixtures("data")
async def test_find_by_attribute(db: AsyncIOMotorDatabase):
    User = make_model()
    user = await User.find_one({"name": "John"})
    assert user is not None
    assert user.name == "John"


async def test_find_by_id(db: AsyncIOMotorDatabase):
    User = make_model()
    inserted_id = (await db["users"].insert_one({"name": "Jake"})).inserted_id
    user = await User.find_one({"_id": inserted_id})
    assert user is not None
    assert user.name == "Jake"


@pytest.mark.usefixtures("data")
async def test_find_absent_single():
    User = make_model()
    user = await User.find_one({"name": "Test"})
    assert user is None


@pytest.mark.usefixtures("data")
async def test_find_all():
    User = make_model()
    users = [user async for user in User.find()]
    assert len(users) == 4


@pytest.mark.usefixtures("data")
async def test_find_one():
    User = make_model()
    users = [user async for user in User.find({"name": "Peter"})]
    assert len(users) == 1
    assert users[0].name == "Peter"


@pytest.mark.usefixtures("data")
async def test_find_multiple():
    User = make_model()
    users = [user async for user in User.find({"admin": True})]
    assert len(users) == 2


@pytest.mark.usefixtures("data")
async def test_find_absent_multiple():
    User = make_model()
    users = [user async for user in User.find({"field": "any"})]
    assert len(users) == 0
