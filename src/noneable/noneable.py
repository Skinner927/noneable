from __future__ import annotations

import warnings
from typing import Any, Callable, Generic, Optional, TypeVar, Union

T = TypeVar("T")
D = TypeVar("D")


class Noneable(Generic[T]):
    """Prevent direct access of an `Optional[T]` value when the value is
    `None`. This is most useful for bool types, but can be used for any type.

    Works as a regular class and as a data descriptor. The data
    descriptor mostly exists to prevent accidental overwrite, but is the
    preferred way to use the class.

    Check that the `value` is non-`None` with `Noneable.has_value`.
    `has_value` will return `False` if value is None, otherwise `True`.

    Retrieve the value with Noneable.value. If value is None then a
    Noneable exception will be raised.
    """

    class NoneValue(TypeError):
        pass

    def __init__(
        self, value_or_factory: Union[Optional[T], Callable[[], Optional[T]]] = None
    ):
        self._value_factory: Optional[Callable[[], Optional[T]]] = None
        self._value: Optional[T] = None
        if callable(value_or_factory):
            self._value_factory = value_or_factory
            self._value = value_or_factory()
        else:
            self._value = value_or_factory

        # For data descriptor, will be set in __set_name__
        self._private_name: Optional[str] = None

    @property
    def has_value(self) -> bool:
        return self._value is not None

    @property
    def value(self) -> T:
        if not self.has_value:
            raise self.NoneValue(f"{self.__class__.__name__} has no value")
        return self._value

    @value.setter
    def value(self, value: Optional[T]) -> None:
        self._value = value

    def get_or_default(self, default: D) -> Union[T, D]:
        if not self.has_value:
            return default
        return self._value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._value!r})"

    # Block accidental usage of Noneable as value ==============================
    # I'd like to override __str__ too, especially if our subtype is `str`,
    # but I think that'll potentially cause more problems than it's worth.

    def __eq__(self, other):
        raise TypeError(
            f"'==' not supported between instances of '{type(self)}' and '{type(other)}'"
        )

    def __bool__(self):
        raise TypeError(f"__bool__ not supported for instances of '{type(self)}'")

    # Data descriptor impl =====================================================

    def __set_name__(self, instance: Any, name: Optional[str]) -> None:
        if name:
            self._private_name = "_noneable_" + name

    def __get__(self, instance, _owner=None) -> Noneable[T]:
        # Have to use __dict__ and not getattr because we could end up in
        # infinite recursion.
        if instance is None or isinstance(instance, type):
            # Class inspection
            return self
        try:
            return instance.__dict__[self._private_name]
        except KeyError:
            pass

        new = self._clone()
        instance.__dict__[self._private_name] = new
        return new

    def __set__(self, instance: Any, value: Noneable[T]) -> None:
        # The only time __set__ is correctly called is when a dataclass is
        # setting the default value or a dataclass's __init__ because it
        # doesn't know to set Noneable.value.
        if instance is None:
            raise TypeError("Instance is None")
        if isinstance(instance, type):
            raise TypeError(f"Instance is class {type(instance)} expected an instance")
        if not isinstance(value, Noneable):
            raise TypeError(f"Expected Noneable got {type(value)}")
        if self._private_name in instance.__dict__:
            warnings.warn(
                "Noneables should not be re-assigned because of reference changes. "
                "Prefer to update the Noneable.value.",
                stacklevel=2,
            )
        # Update just the value. We use the property setter for setting the value
        # but extract _value to bypass any checks.
        self.__get__(instance).value = value._value

    def _clone(self) -> Noneable[T]:
        new = Noneable(self._value_factory() if self._value_factory else self._value)
        new._value_factory = self._value_factory
        new._private_name = self._private_name
        return new
