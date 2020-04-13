from typing import Type

import pytest
from bson import CodecOptions
from bson.codec_options import TypeEncoder, TypeRegistry
from motor.motor_asyncio import AsyncIOMotorDatabase

from motor_odm import Document, encoders

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("encoder", [encoders.SetEncoder, encoders.FrozensetEncoder])
async def test_encoder(encoder: Type[TypeEncoder], db: AsyncIOMotorDatabase):
    class Doc(Document):
        class Mongo:
            collection = "test"
            codec_options = CodecOptions(type_registry=TypeRegistry([encoder()]))

        val: encoder.python_type

    doc = Doc(val={"A", "B", "C"})
    await doc.save()
    one = await Doc.find_one()
    assert one.val == {"A", "B", "C"}
    assert type(one.val) is encoder.python_type
