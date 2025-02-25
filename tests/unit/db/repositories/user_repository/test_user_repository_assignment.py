"""
Test Module for UserRepository Role Assignment Operations.

This module tests the role assignment functionality provided by the
UserAssignmentMixin. It verifies that roles are correctly assigned, that
no assignment occurs if the user or role is missing or if the role is already assigned,
and that exceptions are handled.
"""

import pytest
from unittest.mock import AsyncMock
from sqlalchemy.exc import SQLAlchemyError
from app.db.repositories.user_repository.assignment import UserAssignmentMixin
from app.db.models.role_model import Role


class DummyAssignmentRepo(UserAssignmentMixin):
    """
    Dummy repository class to test role assignment operations.

    Attributes:
        db: Simulated asynchronous database session.
        _model: Dummy model (unused here).
        _logger: Dummy logger instance.
        _user: The dummy user instance to operate on.
    """

    def __init__(self, db, model, logger, user):
        self.db = db
        self._model = model
        self._logger = logger
        self._user = user

    async def get(self, user_id):
        """
        Simulate retrieval of a user by ID.

        Returns:
            The dummy user if IDs match; otherwise, None.
        """
        if self._user is None:
            return None
        return self._user if user_id == self._user.id else None


class DummyLogger:
    """
    Dummy logger that implements an error logging method.
    """

    def error(self, *args, **kwargs):
        pass


class DummyUser:
    """
    Dummy user class for testing role assignment.

    Attributes:
        id (int): User identifier.
        roles (list): List of assigned roles.
    """

    def __init__(self, id):
        self.id = id
        self.roles = []


@pytest.mark.asyncio
async def test_assign_role_success(dummy_db):
    """
    Test that assign_role() successfully assigns a role to a user.
    """
    dummy_user = DummyUser(id=1)
    role = Role(id=10, name="admin")

    repo = DummyAssignmentRepo(dummy_db, None, DummyLogger(), dummy_user)
    dummy_db.get = AsyncMock(return_value=role)
    dummy_db.commit = AsyncMock()

    result = await repo.assign_role(user_id=1, role_id=10)
    assert result is True
    assert role in dummy_user.roles
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_assign_role_already_assigned(dummy_db):
    """
    Test that assign_role() returns False if the role is already assigned.
    """
    dummy_user = DummyUser(id=1)
    role = Role(id=10, name="admin")
    # Pre-assign the role
    dummy_user.roles.append(role)

    repo = DummyAssignmentRepo(dummy_db, None, DummyLogger(), dummy_user)
    dummy_db.get = AsyncMock(return_value=role)
    dummy_db.commit = AsyncMock()

    result = await repo.assign_role(user_id=1, role_id=10)
    # Should return False because role is already in the user's roles.
    assert result is False
    dummy_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_assign_role_no_user(dummy_db):
    """
    Test that assign_role() returns False when the user is not found.
    """
    repo = DummyAssignmentRepo(dummy_db, None, DummyLogger(), None)
    result = await repo.assign_role(user_id=999, role_id=10)
    assert result is False


@pytest.mark.asyncio
async def test_assign_role_no_role(dummy_db):
    """
    Test that assign_role() returns False when the role is not found.
    """
    dummy_user = DummyUser(id=1)
    repo = DummyAssignmentRepo(dummy_db, None, DummyLogger(), dummy_user)
    dummy_db.get = AsyncMock(return_value=None)

    result = await repo.assign_role(user_id=1, role_id=999)
    assert result is False


@pytest.mark.asyncio
async def test_assign_role_exception(dummy_db):
    """
    Test that assign_role() handles exceptions and returns False.
    """
    dummy_user = DummyUser(id=1)
    repo = DummyAssignmentRepo(dummy_db, None, DummyLogger(), dummy_user)
    dummy_db.get = AsyncMock(side_effect=SQLAlchemyError("Error"))

    result = await repo.assign_role(user_id=1, role_id=10)
    assert result is False
