"""
Unit tests for the Service model.

This module tests all aspects of the Service model, including:
- Object instantiation
- Relationship handling
- Property methods
- Instance methods
- Class methods
- Constraint validation

The tests leverage shared fixtures for mock database sessions, repositories, and test data.

Typical usage example:
    pytest tests/unit/test_db/test_models/test_service_model.py
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from app.db.models.service_model import Service, ServiceCreate


@pytest.fixture
def test_service():
    """
    Create a test Service instance.

    Returns:
        Service: A Service instance with test data.
    """
    return Service(
        id=1,
        name="Test Service",
        category_id=100,
        description="A test service",
        base_price=Decimal("50.00"),
        price_unit="hour",
        minimum_hours=2,
        maximum_hours=8,
        requires_consultation=False,
        is_remote_available=True,
        is_active=True,
    )


def test_service_creation(test_service):
    """
    Test that a Service object is correctly instantiated.

    Args:
        test_service (Service): A test service instance.
    """
    assert test_service.id == 1
    assert test_service.name == "Test Service"
    assert test_service.category_id == 100
    assert test_service.description == "A test service"
    assert test_service.base_price == Decimal("50.00")
    assert test_service.price_unit == "hour"
    assert test_service.minimum_hours == 2
    assert test_service.maximum_hours == 8
    assert test_service.requires_consultation is False
    assert test_service.is_remote_available is True
    assert test_service.is_active is True


def test_service_create():
    """
    Test that the create class method correctly instantiates a Service from ServiceCreate.

    This test ensures that data is correctly mapped from the DTO to the Service model.
    """
    service_data = ServiceCreate(
        name="New Service",
        category_id=200,
        description="New service description",
        base_price=Decimal("75.00"),
        price_unit="hour",
        requires_consultation=True,
        is_remote_available=False,
        minimum_hours=1,
        maximum_hours=5,
    )
    new_service = Service.create(service_data)

    assert new_service.name == "New Service"
    assert new_service.category_id == 200
    assert new_service.description == "New service description"
    assert new_service.base_price == Decimal("75.00")
    assert new_service.price_unit == "hour"
    assert new_service.requires_consultation is True
    assert new_service.is_remote_available is False
    assert new_service.minimum_hours == 1
    assert new_service.maximum_hours == 5


def test_service_get_formatted_price(test_service):
    """
    Test that get_formatted_price returns the correct formatted price string.

    Args:
        test_service (Service): A test service instance.
    """
    assert test_service.get_formatted_price() == "$50.00 per hour"


def test_service_get_formatted_price_no_price():
    """
    Test that get_formatted_price returns None when base price or price unit is missing.
    """
    service = Service(id=2, name="No Price Service", base_price=None, price_unit=None)
    assert service.get_formatted_price() is None


def test_service_calculate_price(test_service):
    """
    Test that calculate_price correctly computes the total cost.

    Args:
        test_service (Service): A test service instance.
    """
    assert test_service.calculate_price(4) == Decimal("200.00")


def test_service_calculate_price_minimum_error(test_service):
    """
    Test that calculate_price raises a ValueError when the hours are below the minimum.
    """
    with pytest.raises(ValueError, match="Minimum booking duration is 2 hours"):
        test_service.calculate_price(1)


def test_service_calculate_price_maximum_error(test_service):
    """
    Test that calculate_price raises a ValueError when the hours exceed the maximum.
    """
    with pytest.raises(ValueError, match="Maximum booking duration is 8 hours"):
        test_service.calculate_price(10)


def test_service_calculate_price_no_hours(test_service):
    """
    Test that calculate_price returns base price when no hours are specified.
    """
    assert test_service.calculate_price() == Decimal("50.00")


def test_service_is_available_for_duration(test_service):
    """
    Test that is_available_for_duration correctly checks service availability.

    Args:
        test_service (Service): A test service instance.
    """
    assert test_service.is_available_for_duration(3) is True
    assert test_service.is_available_for_duration(1) is False  # Below min
    assert test_service.is_available_for_duration(9) is False  # Above max


def test_service_is_available_for_duration_inactive():
    """
    Test that is_available_for_duration returns False if the service is inactive.
    """
    service = Service(id=3, name="Inactive Service", is_active=False)
    assert service.is_available_for_duration(3) is False


def test_service_duration_constraints(test_service):
    """
    Test that duration_constraints returns the correct human-readable string.

    Args:
        test_service (Service): A test service instance.
    """
    assert test_service.duration_constraints == "Duration: 2-8 hours"


def test_service_duration_constraints_minimum_only():
    """
    Test that duration_constraints correctly displays minimum hours only.
    """
    service = Service(id=4, name="Min Only", minimum_hours=3, maximum_hours=None)
    assert service.duration_constraints == "Minimum duration: 3 hours"


def test_service_duration_constraints_maximum_only():
    """
    Test that duration_constraints correctly displays maximum hours only.
    """
    service = Service(id=5, name="Max Only", minimum_hours=None, maximum_hours=6)
    assert service.duration_constraints == "Maximum duration: 6 hours"


def test_service_duration_constraints_no_limits():
    """
    Test that duration_constraints returns None when no limits are set.
    """
    service = Service(id=6, name="No Limits", minimum_hours=None, maximum_hours=None)
    assert service.duration_constraints is None


def test_service_repr(test_service):
    """
    Test that the __repr__ method correctly formats the string representation.

    Args:
        test_service (Service): A test service instance.
    """
    assert repr(test_service) == "Service(id=1, name=Test Service)"


def test_service_calculate_price_no_base_price():
    """
    Test that calculate_price returns None when base_price is None.
    """
    service = Service(id=7, name="No Price Service", base_price=None, price_unit="hour")
    assert service.calculate_price(5) is None
