"""
This module contains various supporting functions that can be used independently of the
Motor-ODM framework. Some of these utilities can be found in similar form in other
packages or frameworks and are adapted here to reduce the number of dependencies.
"""
import inspect
from inspect import isclass, ismodule
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    T = TypeVar("T", bound=type)
    C = TypeVar("C", bound=Callable)
    D = TypeVar("D", bound=Union[object, Callable[[Any], Any]])


def inherit_class(
    name: str, self: Optional["T"], parent: "T", merge: Iterable[str] = None
) -> "T":
    """
    Performs a pseudo-inheritance by creating a new class that inherits from ``self``
    and ``parents``. This is useful to support intuitive inheritance on inner classes
    (typically named ``Meta``).

    Note that this method neither returns ``self`` nor any of the ``parents`` but a new
    type that inherits from both.

    :param name: The name of the newly created type.
    :param self: The primary base class (fields in this class take preference over the
                 ``parents``' fields.
    :param parent: The secondary base class (a pseudo-parent of ``self``).
    :param merge: A list of fields that should not be replaces during inheritance but
                  merged. This only works for some types.
    :return: A new type inheriting from ``self`` and ``parents``.
    """
    base_classes: Sequence["T"]
    if not self:
        base_classes = (parent,)
    elif self == parent:
        base_classes = (self,)
    else:
        base_classes = self, parent
    clazz = type(name, base_classes, {})
    if merge is None:
        merge = {}
    for key in merge:
        if hasattr(self, key) and hasattr(parent, key):
            value1 = getattr(parent, key)
            value2 = getattr(self, key)
            setattr(clazz, key, merge_values(value1, value2))
    return clazz  # type: ignore


def merge_values(value1: Any, value2: Any) -> Any:
    """Merges two values.

    This method works only for specific collection types (namely lists, dicts and sets).
    For other values a :exc:`ValueError` is raised.

    The type of the resulting value is determined by the type of ``value2``, however
    ``value1`` may override some of the contents in ``value2`` (e.g. replace values for
    dict keys).
    """
    copy: Any
    if isinstance(value1, list):
        copy = value1.copy()
        copy.extend(value2)
    elif isinstance(value1, dict):
        copy = value1.copy()
        copy.update(value2)
    elif isinstance(value1, set):
        copy = value1.copy()
        copy.update(value2)
    else:
        raise ValueError(
            f"Cannot merge value of type {type(value2)} "
            f"into value of type {type(value1)}"
        )
    return copy


def monkey_patch(
    cls: Union[type, ModuleType], name: Optional[str] = None
) -> Callable[["C"], "C"]:
    """
    Monkey patches class or module by adding to it decorated function. Anything
    overwritten can be accessed via a ``.original`` attribute of the decorated object.

    :param cls: The class or module to be patched.
    :param name: The name of the attribute to be patched.
    :return: A decorator that monkey patches ``cls.name`` and returns the decorated
             function.
    """
    assert isclass(cls) or ismodule(
        cls
    ), "Attempting to monkey patch non-class and non-module"

    def decorator(value: "D") -> "D":
        assert inspect.isfunction(value)

        func = getattr(value, "fget", value)  # Support properties
        if name:
            func_name = name
        elif func.__name__.startswith(f"{cls.__name__}__"):
            func_name = func.__name__[len(f"{cls.__name__}__") :]
        else:
            func_name = func.__name__

        func.__name__ = func_name
        func.original = getattr(cls, func_name, None)

        setattr(cls, func_name, value)
        return value

    return decorator
