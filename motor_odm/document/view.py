from typing import TYPE_CHECKING, Any, List, Type, TypeVar

from motor.core import AgnosticClientSession
from pymongo.collation import Collation

from motor_odm.document.base import MongoDocument
from motor_odm.helpers import equal_views

if TYPE_CHECKING:
    from pydantic.typing import DictStrAny

    GenericDocument = TypeVar("GenericDocument", bound="ComputedDocument")


class ComputedDocument(MongoDocument, abstract=True):
    def __init_subclass__(cls, **kwargs):
        mongo = cls.__mongo__
        if not cls.__abstract__:
            if not mongo.source:
                raise TypeError(f"{cls.__name__} does not define a source view.")

    class Mongo(MongoDocument.Mongo):
        source: str
        pipeline: List["DictStrAny"] = []
        collation: Collation = None

    if TYPE_CHECKING:
        # populated by the metaclass, defined here to help IDEs only
        __mongo__: Type[Mongo]

    @classmethod
    async def ensure_collection(
        cls, force: bool = False, session: AgnosticClientSession = None, **kwargs: Any
    ):
        mongo = cls.__mongo__
        collections = {
            collection.name: collection
            for collection in await cls.db().list_collections()
        }
        collection = collections.get(mongo.collection)
        if collection and collection["type"] != "view":
            # A collection with the same name exists
            if force:
                await cls.db().drop_collection(mongo.collection, session=session)
            else:
                raise TypeError(f"Collection {mongo.collation} does already exist.")
        elif collection:
            # A view with the same name already exists
            await cls.db().drop_collection(mongo.collection, session=session)

        await cls.db().create_collection(
            mongo.collection,
            mongo.codec_options,
            mongo.read_preference,
            mongo.write_concern,
            mongo.read_concern,
            session=session,
            viewOn=mongo.source,
            pipeline=mongo.pipeline,
            collation=mongo.collation,
            **kwargs,
        )
        colls = await cls.db().list_collections()
        for coll in colls:
            print(coll)
        exit(1)
