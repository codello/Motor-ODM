"""
This module contains the base class for interacting with Motor-ODM: :class:`Document`.
The :class:`Document` class is the main entry point to Motor-ODM and provides its main
interface.
"""

from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Callable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
)

from bson import CodecOptions, ObjectId
from motor.core import AgnosticClientSession, AgnosticCollection, AgnosticDatabase
from pydantic import BaseModel, Field
from pydantic.main import ModelMetaclass
from pymongo import IndexModel, ReadPreference, ReturnDocument, WriteConcern
from pymongo.errors import DuplicateKeyError
from pymongo.read_concern import ReadConcern

from motor_odm.helpers import monkey_patch

from .helpers import inherit_class
from .indexes import IndexManager

if TYPE_CHECKING:
    from pydantic.typing import (  # noqa: F401
        DictStrAny,
        AbstractSetIntStr,
        DictIntStrAny,
    )

    GenericDocument = TypeVar("GenericDocument", bound="Document")
    MongoType = Type["Mongo"]

__all__ = ["Document", "Mongo"]


@monkey_patch(ObjectId)
def __get_validators__() -> Iterator[Callable[[Any], ObjectId]]:
    """
    Returns a generator yielding the validators for the `ObjectId` type.
    """

    def validate(value: Union[str, bytes]) -> ObjectId:
        """
        Creates an `ObjectId` from a value. If the
        :param value: An `ObjectId` or a string.
        :return: An `ObjectId`.
        :raises TypeError: If `value` os not a string type.
        :raises InvalidId: If `value` does not represent a valid `ObjectId`.
        """

        return ObjectId(value)

    yield validate


class Mongo:
    """This class defines the defaults for collection configurations.

    Each collection (defined by a subclass of :class:`Document`) can override these
    using an inner class named ``Mongo``. Attributes are implicitly and transitively
    inherited from the Mongo classes of base classes.
    """

    collection: Optional[str]
    """The name of the collection for a document. This attribute is required."""

    abstract: bool = False
    """Whether the document is abstract.

    The value for this field cannot be specified in the ``Mongo`` class but as a keyword
    argument on class creation.
    """

    indexes: List[IndexModel] = []
    """A list of indexes to create for the collection."""

    codec_options: Optional[CodecOptions] = None
    """The codec options to use when accessing the collection.
    
    Defaults to the database's :attr:`codec_options`.
    """

    read_preference: Optional[ReadPreference] = None
    """The read preference to use when accessing the collection.
    
    Defaults to the database's :attr:`read_preference`.
    """

    write_concern: Optional[WriteConcern] = None
    """The write concern to use when accessing the collection.
    
    Defaults to the database's :attr:`write_concern`.
    """

    read_concern: Optional[ReadConcern] = None
    """The read concern to use when accessing the collection.
    
    Defaults to the database's :attr:`read_concern`.
    """


class DocumentMetaclass(ModelMetaclass):
    """The meta class for :class:`Document`.

    Its task is mainly to ensure that the ``Mongo`` class is automatically inherited.
    """

    def __new__(
        mcs,
        name: str,
        bases: Sequence[type],
        namespace: "DictStrAny",
        abstract: bool = False,
        **kwargs: Any,
    ) -> "DocumentMetaclass":
        mcs.validate(name, bases, namespace, abstract)
        mongo: "MongoType" = Mongo
        for base in reversed(bases):
            if base != BaseModel and base != Document and issubclass(base, Document):
                mongo = mcs.inherit_mongo(base.__mongo__, mongo)
        mongo = mcs.inherit_mongo(namespace.get("Mongo"), mongo)  # type: ignore
        mongo.abstract = abstract

        return super().__new__(  # type: ignore
            mcs, name, bases, {"__mongo__": mongo, **namespace}, **kwargs
        )

    @classmethod
    def inherit_mongo(mcs, self: "MongoType", parent: "MongoType") -> "MongoType":
        # noinspection PyTypeChecker
        return inherit_class("Mongo", self, parent, merge={"indexes"})

    @classmethod
    def validate(
        mcs, name: str, bases: Sequence[type], namespace: "DictStrAny", abstract: bool
    ) -> None:
        if "Mongo" in namespace:
            mongo = namespace["Mongo"]
        else:
            mongo = object()
        if hasattr(mongo, "abstract"):
            raise TypeError(
                "Cannot specify `abstract` in Mongo class. Use a keyword argument on "
                "the class instead."
            )
        if not abstract and not hasattr(mongo, "collection"):
            raise TypeError(f"{name} is not abstract and does not define a collection.")


class Document(BaseModel, metaclass=DocumentMetaclass, abstract=True):
    """This is the base class for all documents defined using Motor-ODM.

    A :class:`Document` is a pydantic model that can be inserted into a MongoDB
    collection. This class provides an easy interface for interacting with the database.
    Each document has an :attr:`Document.id` (named ``_id`` in MongoDB) by default by
    which it can be uniquely identified in the database. The name of this field cannot
    be customized however you can override it if you don't want to use :class:`ObjectID
    <bson.objectid.ObjectId>` values for your IDs.

    :param abstract: Mark subclasses as ``abstract`` in order to create an abstract
                     document. An abstract document cannot be instantiated but can be
                     subclassed. This enables you to extract common functionality from
                     multiple documents into a common abstract super-document.
    """

    class Config:
        """:meta private:"""

        validate_all = True
        validate_assignment = True
        allow_population_by_field_name = True

    if TYPE_CHECKING:
        # populated by the metaclass, defined here to help IDEs only
        __mongo__: MongoType

    __db__: Optional[AgnosticDatabase]
    __collection__: Optional[AgnosticCollection] = None

    id: ObjectId = Field(None, alias="_id")
    """The document's ID in the database.

    By default this field is of type :class:`ObjectId <bson.objectid.ObjectId>` but it
    can be overridden to supply your own ID types. Note that if you intend to override
    this field you **must** set its alias to ``_id`` in order for your IDs to be
    recognized as such by MongoDB.
    """

    # noinspection PyMethodParameters
    def __init__(__pydantic_self__, **data: Any) -> None:
        # Uses something other than `self` the first arg to allow "self" as a settable
        # attribute
        if __pydantic_self__.__mongo__.abstract:
            raise TypeError(
                f"Cannot instantiate abstract document {__pydantic_self__.__class__.__name__}"
            )
        super().__init__(**data)

    @classmethod
    def use(cls: Type["Document"], db: AgnosticDatabase) -> None:
        """Sets the database to be used by this :class:`Document`.

        The database will also be used by subclasses of this class unless they
        :meth:`use` their own database. This method has to be invoked before the ODM
        class can be used.
        """
        assert db is not None
        cls.__db__ = db

    @classmethod
    def db(cls) -> AgnosticDatabase:
        """Returns the database that is currently associated with this document.

        If no such database exists this returns the database of the parent document (its
        superclass). If no :class:`Document` class had its :meth:`use` method called to
        set a db, an :class:`AttributeError` is raised.
        """
        if not hasattr(cls, "__db__"):
            raise AttributeError("Accessing database without using it first.")
        return cls.__db__

    @classmethod
    def collection(cls: Type["Document"]) -> AgnosticCollection:
        """Returns the collection for this :class:`Document`.

        The collection uses the ``codec_options``, ``read_preference``,
        ``write_concern`` and ``read_concern`` from the document's ```Mongo``` class.
        """
        meta = cls.__mongo__
        if cls.__collection__ is None or cls.__collection__.database is not cls.db():
            cls.__collection__ = cls.db().get_collection(
                meta.collection,
                codec_options=meta.codec_options,
                read_preference=meta.read_preference,
                write_concern=meta.write_concern,
                read_concern=meta.read_concern,
            )
        return cls.__collection__

    @classmethod
    async def init_indexes(
        cls, drop: bool = True, session: AgnosticClientSession = None, **kwargs: Any
    ) -> None:
        """Creates the indexes for this collection of documents.

        The indexes are specified in the ``indexes`` field of the ``Mongo`` class. By
        default this method makes sure that after the coroutine completes the
        collection's indexes equal the specified indexes. If you do not want to drop
        existing indexes you can specify ``drop=True`` as keyword argument. Note however
        that this method will always override existing indexes.

        :param drop: If ``True`` all indexes not specified by this collection will be
                     dropped. Default is ``True``.
        :param session: A session to use for any database actions.
        :param kwargs: Any keyword arguments are passed to the DB calls. This may be
                       used to specify timeouts etc.
        """
        im = IndexManager(cls.collection(), session, **kwargs)
        await im.ensure_indexes(cls.__mongo__.indexes, drop=drop)

    def mongo(
        self,
        *,
        include: Union["AbstractSetIntStr", "DictIntStrAny"] = None,
        exclude: Union["AbstractSetIntStr", "DictIntStrAny"] = None,
    ) -> "DictStrAny":
        """Converts this object into a dictionary suitable to be saved to MongoDB."""
        document = self.dict(
            by_alias=True, include=include, exclude=exclude, exclude_defaults=True
        )
        if self.id is None:
            document.pop("_id", None)
        return document

    async def insert(self, *args: Any, **kwargs: Any) -> bool:
        """Inserts the object into the database.

        The object is inserted as a new object.
        """
        try:
            result = await self.collection().insert_one(self.mongo(), *args, **kwargs)
            self.id = result.inserted_id
            return True
        except DuplicateKeyError:
            return False

    @classmethod
    async def insert_many(
        cls: Type["GenericDocument"], *objects: "GenericDocument", **kwargs: Any
    ) -> None:
        """Inserts multiple documents at once.

        It is preferred to use this method over multiple :meth:`insert` calls as the
        performance can be much better.
        """
        result = await cls.collection().insert_many(
            [obj.mongo() for obj in objects], **kwargs
        )
        for obj, inserted_id in zip(objects, result.inserted_ids):
            obj.id = inserted_id

    async def save(self, upsert: bool = True, *args: Any, **kwargs: Any,) -> bool:
        assert self.id is not None
        result = await self.collection().replace_one(
            {"_id": self.id}, self.mongo(), *args, **kwargs
        )
        return result.modified_count == 1  # type: ignore

    async def upsert(self, *args: Any, **kwargs: Any) -> bool:
        if self.id is None:
            return await self.insert(*args, **kwargs)
        else:
            return await self.save(*args, **kwargs)

    async def reload(self, *args: Any, **kwargs: Any) -> bool:
        """Reloads a document from the database.

        Use this method if a model might have changed in the database and you need to
        retrieve the current version. You do **not** need to call this after inserting a
        newly created object into the database.
        """
        assert self.id is not None
        result = await self.collection().find_one({"_id": self.id}, *args, **kwargs)
        if result is None:
            return False
        updated = self.__class__(**result)
        object.__setattr__(self, "__dict__", updated.__dict__)
        return True

    async def delete(self, *args: Any, **kwargs: Any) -> bool:
        """Deletes the document from the database.

        This method does not modify the instance in any way. ``args`` and ``kwargs``
        are passed to motor's ``delete_one`` method.

        :returns: ``True`` if the document was deleted.
        """
        result = await self.collection().delete_one(self.mongo(), *args, **kwargs)
        return result.deleted_count == 1  # type: ignore

    @classmethod
    async def delete_many(
        cls: Type["GenericDocument"], *objects: "GenericDocument"
    ) -> int:
        """Deletes all specified objects.

        :param objects: All objects to be deleted.
        :returns: The number of documents deleted.
        """
        result = await cls.collection().delete_many(
            {"_id": {"$in": [obj.id for obj in objects]}}
        )
        return result.deleted_count  # type: ignore

    @classmethod
    def find(
        cls: Type["GenericDocument"],
        filter: "DictStrAny" = None,
        *args: Any,
        **kwargs: Any,
    ) -> AsyncIterator["GenericDocument"]:
        """Returns an iterable over a cursor returning documents matching ``filter``.

        ``args`` and ``kwargs`` are passed to motor's ``find`` method.
        """

        async def context() -> AsyncIterator["GenericDocument"]:
            async for doc in cls.collection().find(filter, *args, **kwargs):
                yield cls(**doc)

        return context()

    @classmethod
    async def find_one(
        cls: Type["GenericDocument"],
        filter: "DictStrAny" = None,
        *args: Any,
        **kwargs: Any,
    ) -> Optional["GenericDocument"]:
        """Returns a single document from the collection."""
        doc = await cls.collection().find_one(filter, *args, **kwargs)
        return cls(**doc) if doc else None

    @classmethod
    async def find_one_and_delete(
        cls: Type["GenericDocument"],
        filter: "DictStrAny" = None,
        *args: Any,
        **kwargs: Any,
    ) -> Optional["GenericDocument"]:
        """Finds a document and deletes it.

        This method works exactly like pymongo's find_one_and_delete except that this
        returns a :class:`Document` instance.
        """
        result = await cls.collection().find_one_and_delete(filter, *args, **kwargs)
        return cls(**result) if result else None

    @classmethod
    async def find_one_and_replace(
        cls: Type["GenericDocument"],
        filter: "DictStrAny",
        replacement: Union["DictStrAny", "GenericDocument"],
        return_document: bool = ReturnDocument.BEFORE,
        *args: Any,
        **kwargs: Any,
    ) -> Optional["GenericDocument"]:
        """Finds a document and replaces it.

        This method works exactly like pymongo's find_one_and_replace except that this
        returns a :class:`Document` instance. Note that if you specify
        ``return_document=ReturnDocument.AFTER`` this method will reload the
        ``replacement`` document.
        """
        data = replacement.mongo() if isinstance(replacement, Document) else replacement
        result = await cls.collection().find_one_and_replace(
            filter, data, return_document=return_document, *args, **kwargs
        )
        if result is None:
            return None
        instance = cls(**result)
        if return_document == ReturnDocument.AFTER and isinstance(replacement, cls):
            object.__setattr__(replacement, "__dict__", instance.__dict__)
            return replacement
        else:
            return instance

    @classmethod
    async def find_one_and_update(
        cls: Type["GenericDocument"],
        filter: "DictStrAny",
        update: "DictStrAny",
        *args: Any,
        **kwargs: Any,
    ) -> Optional["GenericDocument"]:
        """Finds a document and updates it.

        This method works exactly like pymongo's find_one_and_update except that this
        returns a :class:`Document` instance.
        """
        result = await cls.collection().find_one_and_update(
            filter, update, *args, **kwargs
        )
        return cls(**result) if result else None

    @classmethod
    async def count_documents(
        cls, filter: Mapping = None, *args: Any, **kwargs: Any
    ) -> int:
        """Returns the number of documents in this class's collection.

        This method is filterable."""
        if filter is None:
            filter = {}
        return await cls.collection().count_documents(  # type: ignore
            filter, *args, **kwargs
        )
