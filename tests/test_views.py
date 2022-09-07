import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase

from motor_odm import ComputedDocument

pytestmark = pytest.mark.asyncio


async def test_create_view(db: AsyncIOMotorDatabase):
    class View(ComputedDocument):
        class Mongo:
            collection = "view"
            source = "users"
            pipeline = [{"$project": {"name": 1}}]

    await View.ensure_collection()
