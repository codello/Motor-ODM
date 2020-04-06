from bson.codec_options import TypeEncoder

__all__ = ["SetEncoder", "FrozensetEncoder"]


class SetEncoder(TypeEncoder):
    python_type = set

    def transform_python(self, value):
        return list(value)


class FrozensetEncoder(TypeEncoder):
    python_type = frozenset

    def transform_python(self, value):
        return list(value)
