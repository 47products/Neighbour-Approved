"""
Unit tests for the ServiceRegistry module.

This module tests the functionality of the service registration system, including
service registration, dependency resolution, context management, error handling,
and registry reset. Dummy service classes are used to simulate real services.
The tests are written using pytest and make use of shared fixtures from conftest.py.

Key components tested:
- Service registration and retrieval via get_service
- Dependency resolution between services
- The service_context context manager
- The reset functionality to clear service registrations
- Prevention of duplicate registrations
- Wrapping of instantiation errors in DependencyError
- Creation of FastAPI dependency callables via create_dependency
- Global registry retrieval via get_registry
- Core service registration via register_core_services

Usage example:
    $ pytest test_service_registration.py

Dependencies:
    - pytest
"""

import pytest
from app.services.service_registration import (
    registry,
    get_registry,
    register_core_services,
    DependencyError,
    logger,
)


class DummyService:
    """
    Dummy service class for testing service registration.

    This class simulates a basic service that stores a database session and
    any additional initialization parameters.
    """

    def __init__(self, db, **kwargs):
        self.db = db
        self.params = kwargs


class DummyDependentService:
    """
    Dummy service class that depends on another service.

    This service requires an instance of DummyService (provided via dependency
    injection) along with the database session.
    """

    def __init__(self, db, dummy_service, **kwargs):
        self.db = db
        self.dummy_service = dummy_service
        self.params = kwargs


class FailingService:
    """
    Dummy service class that fails upon instantiation.

    This class is used to test the error handling in service initialization.
    Its constructor intentionally raises a RuntimeError.
    """

    def __init__(self, db, **kwargs):
        raise RuntimeError("Intentional failure")


@pytest.fixture(autouse=True)
def reset_registry_before_and_after_tests():
    """
    Fixture to reset the service registry before and after each test.

    This ensures that tests do not affect each other's registry state.
    """
    registry.reset()
    yield
    registry.reset()


def test_register_and_get_service(sync_dummy_db):
    """
    Test registering a service and retrieving it via get_service.

    This test registers DummyService under a given name and verifies that
    get_service returns an instance of DummyService with the expected database session
    and initialization parameters.
    """
    # Register DummyService with an extra parameter.
    registry.register(DummyService, name="DummyService", custom_param="value")
    # Retrieve the service instance using the synchronous dummy db fixture.
    service_instance = registry.get_service("DummyService", sync_dummy_db)
    # Verify that the returned instance is of type DummyService and has expected attributes.
    assert isinstance(service_instance, DummyService)
    assert service_instance.db is sync_dummy_db
    assert service_instance.params.get("custom_param") == "value"


def test_dependency_resolution(sync_dummy_db):
    """
    Test service dependency resolution.

    This test registers DummyService and DummyDependentService, where the latter
    depends on the former. It verifies that the dependency is correctly resolved
    and injected into the DummyDependentService instance.
    """
    registry.register(DummyService, name="DummyService", custom_param="independent")
    registry.register(
        DummyDependentService,
        name="DummyDependentService",
        dependencies={"dummy_service": "DummyService"},
        additional_param="dependent",
    )
    dependent_instance = registry.get_service("DummyDependentService", sync_dummy_db)
    # Verify that the instance is of the correct type.
    assert isinstance(dependent_instance, DummyDependentService)
    # Verify that the injected dependency is an instance of DummyService.
    assert isinstance(dependent_instance.dummy_service, DummyService)
    # Ensure that both the dependent service and its dependency share the same db session.
    assert dependent_instance.db is sync_dummy_db
    assert dependent_instance.dummy_service.db is sync_dummy_db


def test_service_context(sync_dummy_db):
    """
    Test the service_context context manager.

    This test registers a dummy service and verifies that the service_context
    correctly yields the service instance within the context.
    """
    registry.register(DummyService, name="DummyService")
    # Use the context manager to retrieve the service.
    with registry.service_context("DummyService", sync_dummy_db) as service_instance:
        assert isinstance(service_instance, DummyService)
        assert service_instance.db is sync_dummy_db


def test_reset(sync_dummy_db):
    """
    Test the reset functionality of the registry.

    This test registers a dummy service, calls reset, and verifies that the registry
    no longer contains the registered service and that its initialization flag is cleared.
    """
    registry.register(DummyService, name="DummyService")
    assert "DummyService" in registry._services
    # Reset the registry.
    registry.reset()
    # Verify that the registry is cleared.
    assert registry._services == {}
    assert registry._initialized is False


def test_duplicate_registration(sync_dummy_db):
    """
    Test that duplicate registration of a service does not overwrite the existing registration.

    This test registers a dummy service under a specific name, then attempts to register it
    again with different parameters. The second registration should be ignored.
    """
    registry.register(DummyService, name="DummyService", initial="first")
    first_service_info = registry._services.get("DummyService").copy()
    # Attempt duplicate registration.
    registry.register(DummyService, name="DummyService", initial="second")
    second_service_info = registry._services.get("DummyService")
    # The parameters should remain unchanged after the first registration.
    assert first_service_info["params"] == second_service_info["params"]


def test_dependency_error(sync_dummy_db):
    """
    Test that an exception during service instantiation is wrapped in a DependencyError.

    This test registers a service whose constructor raises an exception. When get_service
    is called, a DependencyError should be raised with the original error message.
    """
    registry.register(FailingService, name="FailingService")
    with pytest.raises(DependencyError) as excinfo:
        registry.get_service("FailingService", sync_dummy_db)
    assert "Intentional failure" in str(excinfo.value)


def test_create_dependency(sync_dummy_db):
    """
    Test the creation of a FastAPI dependency callable using create_dependency.

    This test registers a dummy service and retrieves a dependency function via create_dependency.
    It then simulates calling this function with a dummy database session to verify that it returns
    the correct service instance.
    """
    registry.register(DummyService, name="DummyService")
    dependency_callable = registry.create_dependency("DummyService")
    # Simulate dependency injection by calling the dependency callable with the dummy db.
    service_instance = dependency_callable(db=sync_dummy_db)
    assert isinstance(service_instance, DummyService)
    assert service_instance.db is sync_dummy_db


def test_get_registry():
    """
    Test that get_registry returns the global registry instance.

    This test verifies that the get_registry function returns the same instance as the global registry.
    """
    global_registry = get_registry()
    assert global_registry is registry


def test_register_core_services(sync_dummy_db):
    """
    Test the registration of core services.

    This test calls register_core_services and verifies that the expected core services are
    registered in the registry. It also ensures that calling the function a second time does not
    alter the registry.
    """
    # Reset registry to ensure a clean state.
    registry.reset()
    register_core_services()
    expected_services = {
        "SecurityService",
        "AuthenticationService",
        "EmailVerificationService",
        "RoleService",
        "UserManagementService",
    }
    registered_services = set(registry._services.keys())
    assert expected_services.issubset(registered_services)
    current_services_state = registry._services.copy()
    # Calling register_core_services a second time should not modify the registry.
    register_core_services()
    assert registry._services == current_services_state


def test_duplicate_registration_logs_warning(sync_dummy_db, monkeypatch):
    """
    Test that duplicate registration logs a warning and does not override the original registration.

    This test registers DummyService under a specific name, then attempts to register it again.
    The duplicate registration should be ignored, and a warning should be logged.
    """
    # List to capture warning calls
    warning_calls = []

    def fake_warning(message, **kwargs):
        warning_calls.append((message, kwargs))

    # Monkey-patch the registry's logger warning method
    monkeypatch.setattr(registry._logger, "warning", fake_warning)

    # Register DummyService for the first time with a parameter.
    registry.register(DummyService, name="DummyService", param="first")
    # Attempt duplicate registration with a different parameter.
    registry.register(DummyService, name="DummyService", param="second")

    # Verify that a warning was logged.
    assert len(warning_calls) > 0, "Duplicate registration did not log a warning."

    # Verify that the service registration was not overridden.
    service_info = registry._services.get("DummyService")
    assert (
        service_info["params"]["param"] == "first"
    ), "Original registration was overridden."


def test_get_service_not_registered(sync_dummy_db):
    """
    Test that calling get_service for an unregistered service raises a KeyError.

    This test verifies that if a service is not registered in the registry,
    attempting to retrieve it will result in a KeyError.
    """
    with pytest.raises(KeyError) as excinfo:
        registry.get_service("NonExistentService", sync_dummy_db)
    assert "NonExistentService" in str(
        excinfo.value
    ), "Error message should reference the unregistered service."


def test_get_service_dependency_failure(sync_dummy_db):
    """
    Test that get_service wraps dependency resolution failures in a DependencyError.

    This test registers a service that depends on a non-existent service.
    When get_service is called, the missing dependency should cause a DependencyError.
    """
    # Register a service with a dependency on "MissingService" (which is not registered).
    registry.register(
        DummyDependentService,
        name="Dependent",
        dependencies={"dummy_service": "MissingService"},
    )

    with pytest.raises(DependencyError) as excinfo:
        registry.get_service("Dependent", sync_dummy_db)

    error_message = str(excinfo.value)
    # The error message should indicate failure to initialize the "Dependent" service.
    assert (
        "Failed to initialize service Dependent:" in error_message
    ), "Error message should indicate failure during service initialization."
    # The underlying KeyError message should mention that "MissingService" is not registered.
    assert (
        "Service MissingService is not registered" in error_message
    ), "Error message should indicate that the dependency is not registered."


def test_reset_method(sync_dummy_db):
    """
    Test that the reset method clears all service registrations and resets the initialization flag.

    This test registers a dummy service and sets the _initialized flag to True,
    then calls reset. The registry should be empty afterward and _initialized should be False.
    """
    # Register a dummy service.
    registry.register(DummyService, name="DummyService")
    # Manually set the _initialized flag.
    registry._initialized = True

    # Call the reset method.
    registry.reset()

    # Verify that the registry is cleared and _initialized is reset.
    assert registry._services == {}, "Registry services should be empty after reset."
    assert (
        registry._initialized is False
    ), "Registry _initialized flag should be False after reset."


def test_get_service_dependency_exception(sync_dummy_db):
    """
    Test that get_service raises a DependencyError when dependency resolution fails.

    This test registers a service (DummyDependentService) with a dependency on a non-registered
    service ("MissingService"). When get_service is invoked, the missing dependency should trigger
    an exception that is caught and wrapped in a DependencyError.
    """
    # Register DummyDependentService with a dependency that is not registered.
    registry.register(
        DummyDependentService,
        name="DependentService",
        dependencies={"missing_dep": "MissingService"},
    )
    # Attempting to get the service should raise a DependencyError.
    with pytest.raises(DependencyError) as excinfo:
        registry.get_service("DependentService", sync_dummy_db)
    # Check that the error message contains expected substrings.
    error_message = str(excinfo.value)
    assert "Failed to initialize service DependentService" in error_message
    assert "Service MissingService is not registered" in error_message


def test_register_core_services_exception(monkeypatch):
    """
    Test that register_core_services logs an error and re-raises an exception when registration fails.

    This test monkey-patches the registry.register method so that it raises an exception
    (simulating a failure during core service registration). It then verifies that the exception
    is re-raised and that an error message is logged.
    """

    # Define a fake register method that always raises an exception.
    def fake_register(*args, **kwargs):
        raise Exception("Simulated registration failure")

    # Monkey-patch the registry.register method with our fake method.
    monkeypatch.setattr(registry, "register", fake_register)
    # Capture logger.error calls.
    error_calls = []

    def fake_logger_error(message, **kwargs):
        error_calls.append((message, kwargs))

    monkeypatch.setattr(logger, "error", fake_logger_error)
    # Calling register_core_services should re-raise the simulated exception.
    with pytest.raises(Exception) as excinfo:
        register_core_services()
    # Verify that the exception message matches the simulated failure.
    assert "Simulated registration failure" in str(excinfo.value)
    # Verify that logger.error was called with an appropriate error message.
    assert any("Service registration failed" in msg for msg, _ in error_calls)
