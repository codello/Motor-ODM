"""
This module contains the base class for interacting with Motor-ODM: :class:`Document` as well as some important
descendants.
"""

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator, Optional, Type, TypeVar, Union

from bson import CodecOptions
from motor.core import AgnosticCollection, AgnosticDatabase
from pydantic import BaseModel, Field
from pydantic.main import ModelMetaclass
from pymongo import ReadPreference, WriteConcern
from pymongo.read_concern import ReadConcern
from pymongo.results import InsertManyResult

from .fixtures import ObjectId
from .helpers import inherit_class
from .query import create_query

if TYPE_CHECKING:
    from pydantic.typing import DictStrAny
    from motor_odm.query import Query

    GenericDocument = TypeVar("GenericDocument", bound='Document')
    MongoType = Type['MongoBase']

__all__ = ["DocumentMetaclass", "Document"]


class MongoBase:
    """This class defines the defaults for collection configurations.

    Each collection (defined by a subclass of :class:`Document`) can override these using an inner class named
    ``Mongo``. Attributes are implicitly and transitively inherited from the Mongo classes of base classes.
    """

    collection: str = None
    """The name of the collection for a document. This attribute is required."""

    codec_options: CodecOptions = None
    """The codec options to use when accessing the collection. Defaults to the database's :attr:`codec_options`."""

    read_preference: ReadPreference = None
    """The read preference to use when accessing the collection. Defaults to the database's :attr:`read_preference`."""

    write_concern: WriteConcern = None
    """The write concern to use when accessing the collection. Defaults to the database's :attr:`write_concern`."""

    read_concern: ReadConcern = None
    """The read concern to use when accessing the collection. Defaults to the database's :attr:`read_concern`."""


class DocumentMetaclass(ModelMetaclass):
    """The meta class for :class:`Document`. Ensures that the ``Mongo`` class is automatically inherited."""

    def __new__(mcs, name, bases, namespace, **kwargs):
        mongo = MongoBase
        for base in reversed(bases):
            if base != BaseModel and base != Document and issubclass(base, Document):
                mongo = inherit_class('Mongo', base.__mongo__, mongo)
        mongo = inherit_class('Mongo', namespace.get('Mongo'), mongo)

        if (namespace.get('__module__'), namespace.get('__qualname__')) != ('motor_odm.document', 'Document'):
            if mongo.collection is None:
                raise TypeError(f"{name} does not define a collection.")

        return super().__new__(mcs, name, bases, {'__mongo__': mongo, **namespace}, **kwargs)


class Document(BaseModel, metaclass=DocumentMetaclass):
    """This is the base class for all documents defined using Motor-ODM.

    A `Document` is a pydantic model that can be inserted into a MongoDB collection. Each document has an `id` by
    default by which it can be uniquely identified in the database.
    """

    class Config:
        validate_all = True
        validate_assignment = True
        allow_population_by_field_name = True

    if TYPE_CHECKING:
        # populated by the metaclass, defined here to help IDEs only
        __mongo__: MongoType

    __db__: Optional[AgnosticDatabase]
    __collection__: Optional[AgnosticCollection] = None

    id: ObjectId = Field(None, alias="_id")

    @classmethod
    def use(cls: Type['Document'], db: AgnosticDatabase):
        assert db is not None
        cls.__db__ = db

    @classmethod
    def db(cls) -> AgnosticDatabase:
        if not hasattr(cls, '__db__'):
            raise AttributeError("Accessing database without using it first.")
        return cls.__db__

    @classmethod
    def collection(cls: Type['Document']) -> AgnosticCollection:
        meta = cls.__mongo__
        if cls.__collection__ is None or cls.__collection__.database is not cls.db():
            cls.__collection__ = cls.db().get_collection(meta.collection,
                                                         codec_options=meta.codec_options,
                                                         read_preference=meta.read_preference,
                                                         write_concern=meta.write_concern,
                                                         read_concern=meta.read_concern)
        return cls.__collection__

    def document(self, *,
                 include: Union['AbstractSetIntStr', 'DictIntStrAny'] = None,
                 exclude: Union['AbstractSetIntStr', 'DictIntStrAny'] = None) -> 'DictStrAny':
        return self.dict(by_alias=True, include=include, exclude=exclude, exclude_defaults=True)

    @classmethod
    async def count(cls, db_filter: 'Query' = None, **kwargs):
        query = create_query(db_filter, **kwargs)
        return await cls.collection().count_documents(query)

    @classmethod
    async def batch_insert(cls: Type['GenericDocument'], *objects: 'GenericDocument') -> None:
        result: InsertManyResult = await cls.collection().insert_many([obj.document() for obj in objects])
        for obj, inserted_id in zip(objects, result.inserted_ids):
            obj.id = inserted_id

    @classmethod
    async def get(cls: Type['GenericDocument'],
                  db_filter: 'Query' = None,
                  **kwargs) -> Optional['GenericDocument']:
        query = create_query(db_filter, **kwargs)
        doc = await cls.collection().find_one(query)
        return cls(**doc) if doc else None

    @classmethod
    def all(cls: Type['GenericDocument']) -> AsyncIterator['GenericDocument']:
        return cls.find()

    @classmethod
    def find(cls: Type['GenericDocument'],
             db_filter: 'Query' = None,
             **kwargs) -> AsyncIterator['GenericDocument']:
        query = create_query(db_filter, **kwargs)

        @asynccontextmanager
        async def context():
            async for doc in cls.collection().find(query):
                yield cls(**doc)

        return context()

    async def reload(self) -> None:
        updated = self.__class__(**await self.collection().find_one({"_id": self.id}))
        object.__setattr__(self, '__dict__', updated.__dict__)

    async def insert(self) -> None:
        result = await self.collection().insert_one(self.document())
        self.id = result.inserted_id
