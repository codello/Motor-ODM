from typing import Optional, TypeVar

T = TypeVar('T', bound=type)


def inherit_class(name: str, self: Optional[T], parent: T) -> T:
    if not self:
        base_classes = (parent,)
    elif self == parent:
        base_classes = (self,)
    else:
        base_classes = self, parent
    return type(name, base_classes, {})
