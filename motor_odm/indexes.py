from typing import Any, Dict, Iterable, Optional

from bson import SON
from motor.core import AgnosticClientSession, AgnosticCollection
from pymongo import IndexModel


class IndexManager:
    """An ``IndexManager`` instance can create a specific state concerning indexes.

    .. note::

       The ``IndexManager`` is used internally by
       :class:`Document <motor_odm.document.Document>`. Normally there is no need to use
       this class manually.
    """

    def __init__(
        self,
        collection: AgnosticCollection,
        session: AgnosticClientSession,
        **kwargs: Any
    ) -> None:
        self.collection = collection
        self.session = session
        self.kwargs = kwargs
        self.db_indexes: Optional[Dict[str, SON]] = None

    async def ensure_indexes(
        self, indexes: Iterable[IndexModel], drop: bool = True
    ) -> None:
        """Ensures that the specified ``indexes`` exist in the databse.

        This method communicates with the database several times to compare the
        specified ``indexes`` to the indexes already present in the database. If an
        index already exists it is not recreated. If an index exists with different
        options (name, uniqueness, ...) it is dropped and recreated.

        Any indexes in the database that are not specified in ``indexes`` will be
        dropped unless ``drop=False`` is specified.
        """
        await self.load_db_indexes()
        assert self.db_indexes is not None
        new_indexes = []
        for index in indexes:
            db_index = self.get_db_index(index.document["key"])
            if db_index is None:
                new_indexes.append(index)
            elif self.equal(index, db_index):
                del self.db_indexes[db_index["name"]]
            else:
                await self.collection.drop_index(
                    db_index["name"], session=self.session, **self.kwargs
                )
                del self.db_indexes[db_index["name"]]
                new_indexes.append(index)
        if new_indexes:
            await self.collection.create_indexes(
                new_indexes, session=self.session, **self.kwargs
            )
        if drop:
            for name in self.db_indexes.keys():
                await self.collection.drop_index(
                    name, session=self.session, **self.kwargs
                )

    async def load_db_indexes(self) -> None:
        """Loads the existing indexes from the database."""
        # noinspection PyTypeChecker
        self.db_indexes = {
            index["name"]: index
            async for index in self.collection.list_indexes(session=self.session)
            if index["name"] != "_id_"
        }

    def get_db_index(self, spec: SON) -> Optional[SON]:
        """Fetches the database index matching the ``spec``.

        This method does not communicate with the database. You have to have called
        :meth:`load_db_indexes` before.

        :returns: An index from the database or ``None`` if no index matching ``spec``
                  exists.
        """
        assert self.db_indexes is not None
        for index in self.db_indexes.values():
            if index["key"] == spec:
                return index
        return None

    @staticmethod
    def equal(index: IndexModel, db_index: SON) -> bool:
        """Compares the specified ``index`` and ``db_index``.

        This method return ``True`` if the ``index`` specification can be considered
        equal to the existing ``db_index`` in the database.
        """
        dbi = db_index.copy()
        del dbi["v"]
        del dbi["ns"]
        return dbi == index.document  # type: ignore
