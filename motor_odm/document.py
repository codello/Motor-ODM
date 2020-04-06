from typing import Type, TypeVar, Union, TYPE_CHECKING, Sequence, Optional, AsyncIterator

from bson import ObjectId, CodecOptions
from motor.core import AgnosticDatabase, AgnosticCollection
from pydantic import BaseModel, Field
from pydantic.main import ModelMetaclass
from pymongo import WriteConcern, ReadPreference
from pymongo.read_concern import ReadConcern

from motor_odm.helpers import inherit_class

if TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr, DictIntStrAny, DictStrAny

    GenericDocument = TypeVar("GenericDocument", bound='Document')
    MongoType = Type['MongoBase']

__all__ = ["DocumentMetaclass", "Document"]


class MongoBase:
    collection: str = None
    codec_options: CodecOptions = None
    read_preference: ReadPreference = None
    write_concern: WriteConcern = None
    read_concern: ReadConcern = None


class DocumentMetaclass(ModelMetaclass):
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
        cls.__collection__ = None

    @classmethod
    def db(cls) -> AgnosticDatabase:
        if getattr(cls, '__db__'):
            raise AttributeError("Accessing database without using it first.")
        return cls.__db__

    @classmethod
    def collection(cls: Type['Document']) -> AgnosticCollection:
        meta = cls.__mongo__
        if not cls.__collection__:
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
    async def batch_create(cls, objects: Sequence['Document']) -> None:
        await cls.collection().insert_many([o.document() for o in objects])

    @classmethod
    async def all(cls: Type['GenericDocument']) -> AsyncIterator['GenericDocument']:
        async for doc in cls.collection().find():
            yield cls(**doc)

    @classmethod
    async def get(cls: Type['GenericDocument'], filter: 'DictStrAny' = None, **kwargs) -> Optional['GenericDocument']:
        if filter is None:
            filter = {}
        if filter is None:
            for key, value in kwargs:
                try:
                    field = cls.__fields__.get(key)
                #            mongo_filter[field.alias] = value
                except KeyError:
                    pass

        #           mongo_filter[key] = value
        # TODO: Issue a warning here
        # return cls.collection().find_one(**mongo_filter)

    async def reload(self) -> None:
        updated = self.__class__(**await self.collection().find_one({"_id": self.id}))
        object.__setattr__(self, '__dict__', updated.__dict__)

    async def insert(self) -> None:
        result = await self.collection().insert_one(self.document())
        self.id = result.inserted_id
