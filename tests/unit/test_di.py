import pytest

from qal_kernel.di import Container
from qal_kernel.errors import DependencyNotFoundError, DuplicateRegistrationError


def test_container_resolves_singleton_factory_once() -> None:
    container = Container()
    calls = 0

    def factory(_: Container) -> list[str]:
        nonlocal calls
        calls += 1
        return []

    container.register_factory(list, factory)
    assert container.resolve(list) is container.resolve(list)
    assert calls == 1


def test_container_rejects_duplicates_and_unknown_contracts() -> None:
    container = Container()
    container.register_instance(str, "registered")
    with pytest.raises(DuplicateRegistrationError):
        container.register_instance(str, "duplicate")
    with pytest.raises(DependencyNotFoundError):
        container.resolve(int)
