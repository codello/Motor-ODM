from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterator,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
)

from bson import ObjectId
from motor.core import AgnosticClientSession
from pydantic import Field
from pymongo import IndexModel, ReturnDocument
from pymongo.errors import DuplicateKeyError

from motor_odm.document.base import MongoDocument
from motor_odm.helpers import monkey_patch
from motor_odm.indexes import IndexManager
from motor_odm.query import q

if TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr, DictIntStrAny, DictStrAny

    GenericDocument = TypeVar("GenericDocument", bound="Document")
    MongoType = Type["Document.Mongo"]


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


class Document(MongoDocument, abstract=True):
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

        allow_mutation = True

    class Mongo:
        __merge__ = {"indexes"}
        indexes: List[IndexModel] = []
        """A list of indexes to create for the collection."""

    if TYPE_CHECKING:
        # populated by the metaclass, defined here to help IDEs only
        __mongo__: MongoType  # type: ignore

    id: ObjectId = Field(None, alias="_id")
    """The document's ID in the database.

    By default this field is of type :class:`ObjectId <bson.objectid.ObjectId>` but it
    can be overridden to supply your own ID types. Note that if you intend to override
    this field you **must** set its alias to ``_id`` in order for your IDs to be
    recognized as such by MongoDB.
    """

    @classmethod
    async def ensure_indexes(
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
        document = super().mongo(include=include, exclude=exclude)
        if self.id is None:
            document.pop("_id", None)
        return document

    async def insert(self, *args: Any, **kwargs: Any) -> bool:
        """Inserts the object into the database.

        The object is inserted as a new object. If the document already exists this
        method will raise an error. Use :meth:`save` instead if you want to update an
        existing value.
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
        """Saves this instance to the database.

        By default this method creates the document in the database if it doesn't exist.
        If you don't want this behavior you can pass ``upsert=False``.

        Any ``args`` and ``kwargs`` are passed to motor's ``replace_one`` method.

        :param upsert: Whether to create the document if it doesn't exist.
        :returns: ``True`` if the document was inserted/updated, ``False`` if nothing
                  changed. This may also indicate that the document was not changed.
        """
        result = await self.collection().replace_one(
            q(self.id), self.mongo(), upsert=upsert, *args, **kwargs
        )
        if result.upserted_id is not None:
            self.id = result.upserted_id
            return True
        else:
            return result.modified_count == 1  # type: ignore

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
            q(_id__in=[obj.id for obj in objects])
        )
        return result.deleted_count  # type: ignore

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
