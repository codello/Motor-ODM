import json
import os

import pytest
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from motor_odm import Document


@pytest.fixture(scope="function")
async def db() -> AsyncIOMotorDatabase:
    client = AsyncIOMotorClient("localhost")
    db = client["test"]
    await client.drop_database(db)
    Document.use(db)
    yield db
    await client.drop_database(db)


@pytest.fixture(scope="function")
async def data(db: AsyncIOMotorDatabase) -> None:
    with open(os.path.join(os.path.dirname(__file__), "data.json")) as f:
        file_data = json.load(f)
    for key, value in file_data.items():
        await db[key].insert_many(value)
