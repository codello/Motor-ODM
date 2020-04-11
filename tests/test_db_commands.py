import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase

pytestmark = pytest.mark.asyncio


@pytest.mark.usefixtures("data")
async def test_get_by_name(db: AsyncIOMotorDatabase):
    result = await db["test"].find_one({"name": "Test 1"})
    assert result is not None
    assert isinstance(result, dict)
