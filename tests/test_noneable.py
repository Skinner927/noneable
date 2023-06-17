from __future__ import annotations

import dataclasses

import pytest

from noneable import Noneable


def test_not_net_noneable() -> None:
    n: Noneable[bool] = Noneable()

    assert isinstance(n, Noneable)

    # Test default None
    assert n.has_value is False
    with pytest.raises(Noneable.NoneValue):
        _ = n.value

    # Test setting to True
    n.value = True
    assert n.has_value is True
    assert n.value is True

    # Test setting to False
    n.value = False
    assert n.has_value is True
    assert n.value is False

    # Test setting back to None
    n.value = None
    assert n.has_value is False
    with pytest.raises(Noneable.NoneValue):
        _ = n.value

    # A bool cast of Noneable should always raise regardless of value
    with pytest.raises(TypeError):
        if n:
            pass

    n.value = True
    with pytest.raises(TypeError):
        if n:
            pass

    with pytest.raises(TypeError):
        if n == n:
            pass
    with pytest.raises(TypeError):
        if n > n:
            pass


def test_on_class_no_init():
    class Numba:
        thing: Noneable[int] = Noneable()

    n = Numba()

    # Default is None
    assert n.thing.has_value is False

    n.thing.value = 1
    assert n.thing.has_value is True
    assert n.thing.value == 1

    n.thing.value = 0
    assert n.thing.has_value is True
    assert n.thing.value == 0

    n.thing.value = None
    assert n.thing.has_value is False
    with pytest.raises(Noneable.NoneValue):
        # Accessing None raises
        _ = n.thing.value

    # Set Noneable to non-None value for the following tests
    # so we know it's not a Noneable issue.
    n.thing.value = 1

    # A Noneable cannot be compared or bool'd
    assert isinstance(n.thing, Noneable)
    with pytest.raises(TypeError):
        if n.thing:
            pass
    with pytest.raises(TypeError):
        bool(n.thing)
    # Cannot be re-assigned
    with pytest.raises(TypeError):
        n.thing = 1
    with pytest.raises(TypeError):
        assert n.thing == 1
    with pytest.raises(TypeError):
        if n.thing > 0:
            pass
    with pytest.raises(TypeError):
        if len(n.thing):
            pass
    # Cannot be deleted
    with pytest.raises(AttributeError, match="__delete__"):
        del n.thing


def test_on_dataclass_with_default():
    @dataclasses.dataclass
    class DcFoo:
        val: Noneable[bool] = Noneable(True)

    d = DcFoo()
    z = DcFoo()

    assert d.val.has_value
    assert d.val.value

    d.val.value = None
    assert not d.val.has_value

    with pytest.raises(TypeError):
        d.val = None
    with pytest.raises(TypeError):
        d.val = True

    # Ensure we're writing to the instance
    d.val.value = True
    z.val.value = False
    assert d.val.value != z.val.value


def test_on_dataclass_with_no_default():
    """
    WARNING: THIS IS INVALID USAGE

    Noneable cannot be a data descriptor if it's not assigned at the class level
    """

    @dataclasses.dataclass
    class DcFoo:
        val: Noneable[bool]

    d = DcFoo(Noneable(True))

    assert d.val.has_value
    assert d.val.value

    d.val.value = None
    assert not d.val.has_value

    # Would normally error
    d.val = None
    d.val = True

    # Only errors because we don't have descriptor protections
    with pytest.raises(AttributeError, match="has_value"):
        assert d.val.has_value


def test_on_dataclass_with_field_default():
    @dataclasses.dataclass
    class DcFoo:
        val: Noneable[bool] = dataclasses.field(default=Noneable(True))

    d = DcFoo()
    z = DcFoo()

    assert d.val.has_value
    assert d.val.value

    d.val.value = None
    assert not d.val.has_value

    with pytest.raises(TypeError):
        d.val = None
    with pytest.raises(TypeError):
        d.val = True

    # Ensure we're writing to the instance
    d.val.value = True
    z.val.value = False
    assert d.val.value != z.val.value
