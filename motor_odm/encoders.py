from typing import TYPE_CHECKING, FrozenSet, List, Set

from bson.codec_options import TypeEncoder

__all__ = ["SetEncoder", "FrozensetEncoder"]

if TYPE_CHECKING:
    from typing import TypeVar

    T = TypeVar('T')


class SetEncoder(TypeEncoder):
    python_type = set

    def transform_python(self, value: Set['T']) -> List['T']:
        return list(value)


class FrozensetEncoder(TypeEncoder):
    python_type = frozenset

    def transform_python(self, value: FrozenSet['T']) -> List['T']:
        return list(value)
