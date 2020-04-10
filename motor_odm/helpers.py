from inspect import isclass, ismodule
from types import ModuleType
from typing import Any, Callable, Optional, Tuple, TypeVar, Union

T = TypeVar("T", bound=type)
C = TypeVar("C", bound=Callable)
D = TypeVar("D", bound=Union[object, Callable[[Any], Any]])


def inherit_class(name: str, self: Optional[T], parent: T) -> T:
    base_classes: Tuple[T, ...]
    if not self:
        base_classes = (parent,)
    elif self == parent:
        base_classes = (self,)
    else:
        base_classes = self, parent
    return type(name, base_classes, {})  # type: ignore


def monkey_patch(
    cls: Union[type, ModuleType], name: Optional[str] = None
) -> Callable[[C], C]:
    """
    Monkey patches class or module by adding to it decorated function.

    Anything overwritten could be accessed via .original attribute of decorated object.
    """
    assert isclass(cls) or ismodule(
        cls
    ), "Attempting to monkey patch non-class and non-module"

    def decorator(value: D) -> D:
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
