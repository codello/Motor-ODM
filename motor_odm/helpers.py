"""
This module contains various supporting functions that can be used independently of the Motor-ODM framework. Some of
these utilities can be found in similar form in other packages or frameworks and are adapted here to reduce the number
of dependencies.
"""
import inspect
from inspect import isclass, ismodule
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, Optional, Tuple, TypeVar, Union

if TYPE_CHECKING:
    T = TypeVar("T", bound=type)
    C = TypeVar("C", bound=Callable)
    D = TypeVar("D", bound=Union[object, Callable[[Any], Any]])


def inherit_class(name: str, self: Optional["T"], *parents: "T") -> "T":
    """
    Performs a pseudo-inheritance by creating a new class that inherits from ``self`` and ``parents``. This is useful to
    support intuitive inheritance on inner classes (typically named ``Meta``).

    Note that this method neither returns ``self`` nor any of the ``parents`` but a new type that inherits from both.

    :param name: The name of the newly created type.
    :param self: The primary base class (fields in this class take preference over the ``parents``' fields.
    :param parents: The secondary base classes. Field preferences are determined by the order of the parent classes.
    :return: A new type inheriting from ``self`` and ``parents``.
    """
    base_classes: Tuple["T", ...]
    if not self:
        base_classes = parents
    elif self == parents[0]:
        base_classes = (self, *parents[1:])
    else:
        base_classes = self, *parents
    return type(name, base_classes, {})  # type: ignore


def monkey_patch(
    cls: Union[type, ModuleType], name: Optional[str] = None
) -> Callable[["C"], "C"]:
    """
    Monkey patches class or module by adding to it decorated function. Anything overwritten can be accessed via a
    ``.original`` attribute of the decorated object.

    :param cls: The class or module to be patched.
    :param name: The name of the attribute to be patched.
    :return: A decorator that monkey patches ``cls.name`` and returns the decorated function.
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
