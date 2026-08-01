import pytest

from qal_kernel.di import Container
from qal_kernel.errors import (
    CircularDependencyError,
    DependencyNotFoundError,
    DuplicateRegistrationError,
    InvalidDependencyError,
)


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


def test_container_detects_circular_dependencies() -> None:
    class ServiceA:
        pass

    class ServiceB:
        pass

    container = Container()
    container.register_factory(
        ServiceA,
        lambda dependencies: dependencies.resolve(ServiceB),
    )
    container.register_factory(
        ServiceB,
        lambda dependencies: dependencies.resolve(ServiceA),
    )

    with pytest.raises(CircularDependencyError):
        container.resolve(ServiceA)


def test_container_rejects_incompatible_factory_result() -> None:
    container = Container()

    def invalid_factory(_: Container) -> str:
        return "not an integer"

    container.register_factory(int, invalid_factory)  # type: ignore[arg-type]

    with pytest.raises(InvalidDependencyError):
        container.resolve(int)