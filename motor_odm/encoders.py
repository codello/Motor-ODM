"""BSON encoders for common python types.

This module contains a collection of :class:`bson.codec_options.TypeEncoder` subclasses
for common python types such as sets. Note that these encoders are provided as a
convenience but are not used automatically. If you want to use sets in your documents
you have to provide the appropriate ``codec_options`` to the MongoDB client, database,
collection or function.
"""

from typing import TYPE_CHECKING

from bson.codec_options import TypeEncoder

__all__ = ["SetEncoder", "FrozensetEncoder"]

if TYPE_CHECKING:
    from typing import TypeVar

    T = TypeVar("T")


class SetEncoder(TypeEncoder):
    """BSON support for python :class:`set`.

    This encoder encodes a :class:`set` in form of a :class:`list`. The list is not
    converted back into a set automatically but if you are using the :class:`Document
    <motor_odm.document.Document>` class this is done upon initialization of your model.
    """

    python_type = set
    transform_python = list


class FrozensetEncoder(TypeEncoder):
    """BSON support for python :class:`frozenset`.

    This encoder encodes a :class:`frozenset` in form of a :class:`list`. The list is
    not converted back into a set automatically but if you are using the
    :class:`Document <motor_odm.document.Document>` class this is done upon
    initialization of your model.
    """

    python_type = frozenset
    transform_python = list
