"""This module defines the base class for all MongoDB documents."""

from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Generic,
    Mapping,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from bson import CodecOptions
from motor.core import AgnosticClientSession, AgnosticCollection, AgnosticDatabase
from pydantic import BaseModel
from pydantic.main import ModelMetaclass
from pymongo import ReadPreference, WriteConcern
from pymongo.read_concern import ReadConcern

from motor_odm.helpers import inherit_class

if TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr, DictIntStrAny, DictStrAny

    GenericDocument = TypeVar("GenericDocument", bound="MongoDocument")
    MongoType = Type["MongoDocument.Mongo"]

__all__ = ["MongoDocument"]


class DocumentMetaclass(ModelMetaclass):
    """The meta class for :class:`MongoDocument`.

    Its task is mainly to ensure that the ``Mongo`` class is automatically inherited.
    """

    def __new__(
        mcs,
        name: str,
        bases: Tuple[type, ...],
        namespace: "DictStrAny",
        abstract: bool = False,
        **kwargs: Any,
    ) -> "DocumentMetaclass":
        # noinspection PyTypeChecker
        mongo: MongoType = object  # type: ignore
        for base in reversed(bases):
            if base != BaseModel and issubclass(base, MongoDocument):
                mongo = inherit_class("Mongo", base.__mongo__, mongo)
        mongo = inherit_class("Mongo", namespace.get("Mongo"), mongo)
        return super().__new__(  # type: ignore
            mcs,
            name,
            bases,
            {"__mongo__": mongo, "__abstract__": abstract, **namespace},
            **kwargs,
        )


class MongoDocument(BaseModel, metaclass=DocumentMetaclass, abstract=True):
    """The base class for all MongoDB documents.

    This class defines a basic interface for Motor-ODM using Pydantic models. It holds a
    connection to a collection in the database and can read data from that collection.

    :param abstract: Declaring a document as abstract prevents you from instantiating
                     objects of that class. However it enables you to inherit from an
                     abstract document to provide common fields to multiple documents.
    """

    def __init_subclass__(cls, **kwargs):
        mongo = cls.__mongo__
        if not cls.__abstract__ and not mongo.collection:
            raise TypeError(
                f"{cls.__name__} is not abstract and does not define a collection."
            )

    class Config:
        """:meta private:"""

        validate_all = True
        validate_assignment = True
        allow_population_by_field_name = True
        allow_mutation = False

    class Mongo:
        """This class defines default values for the ``Mongo`` class of a document."""

        __merge__: Set[str] = set()
        """:meta private:"""

        collection: Optional[str] = None
        """The name of the collection for a document. This attribute is required."""

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

    if TYPE_CHECKING:
        # populated by the metaclass, defined here to help IDEs only
        __mongo__: "MongoType"
        __abstract__: bool

    __db__: Optional[AgnosticDatabase]
    __collection__: Optional[AgnosticCollection] = None

    # noinspection PyMethodParameters
    # Uses something other than `self` the first arg to allow "self" as a settable
    # attribute
    def __init__(__pydantic_self__, **data: Any) -> None:
        if __pydantic_self__.__abstract__:
            raise TypeError(
                f"Cannot instantiate abstract document "
                f"{__pydantic_self__.__class__.__name__}"
            )
        super().__init__(**data)

    @classmethod
    def use(cls: Type["MongoDocument"], db: AgnosticDatabase) -> None:
        """Sets the database to be used by this document.

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
        superclass). If no :class:`MongoDocument` class had its :meth:`use` method
        called to set a db, an :class:`AttributeError` is raised.
        """
        if not hasattr(cls, "__db__"):
            raise AttributeError("Accessing database without using it first.")
        return cls.__db__

    @classmethod
    async def ensure_collection(
        cls, force: bool = False, session: AgnosticClientSession = None, **kwargs: Any,
    ):
        pass

    @classmethod
    def collection(cls: Type["MongoDocument"]) -> AgnosticCollection:
        """Returns the collection for this document.

        The collection uses the ``codec_options``, ``read_preference``,
        ``write_concern`` and ``read_concern`` from the document's ```Mongo``` class.
        """
        # noinspection PyTypeChecker
        mongo: MongoDocument.Mongo = cls.__mongo__  # type: ignore
        if cls.__collection__ is None or cls.__collection__.database is not cls.db():
            cls.__collection__ = cls.db().get_collection(
                mongo.collection,
                codec_options=mongo.codec_options,
                read_preference=mongo.read_preference,
                write_concern=mongo.write_concern,
                read_concern=mongo.read_concern,
            )
        return cls.__collection__

    def mongo(
        self,
        *,
        include: Union["AbstractSetIntStr", "DictIntStrAny"] = None,
        exclude: Union["AbstractSetIntStr", "DictIntStrAny"] = None,
    ) -> "DictStrAny":
        """Converts this object into a MongoDB-compatible dictionary."""
        document = self.dict(
            by_alias=True, include=include, exclude=exclude, exclude_defaults=True
        )
        return document

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

    @classmethod
    async def estimate_document_count(cls, **kwargs: Any) -> int:
        return await cls.collection().estimated_document_count(**kwargs)  # type: ignore
