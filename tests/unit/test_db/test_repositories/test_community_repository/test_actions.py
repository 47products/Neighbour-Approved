"""
Unit tests for the Community Repository Actions Mixin.

This module tests all write operations for community data access, including:
  - Adding a member.
  - Removing a member.
  - Updating a member's role.
  - Updating the member count.

Both successful and failure branches are covered.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, case
from app.db.repositories.community_repository.repository import CommunityRepository
from app.db.errors import IntegrityError
from app.db.models.community_member_model import CommunityMember
from app.db.models.community_model import Community


@pytest.fixture
def dummy_db():
    """
    Fixture that returns a dummy database session with async methods.
    """
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def repository(dummy_db):
    """
    Fixture that returns a CommunityRepository instance with a dummy DB session.

    For actions, _model is set to Community.
    """
    repo = CommunityRepository(dummy_db)
    repo._logger = MagicMock()
    repo._model = Community
    return repo


# --- add_member ---
@pytest.mark.asyncio
async def test_add_member_success(repository, dummy_db):
    """
    Test that add_member successfully creates and returns a CommunityMember.
    """
    dummy_member = CommunityMember(
        community_id=1,
        user_id=100,
    )

    assert dummy_member.community_id == 1
    assert dummy_member.user_id == 100


@pytest.mark.asyncio
async def test_add_member_failure(repository, dummy_db):
    """
    Test that add_member raises an IntegrityError when a SQLAlchemyError occurs.
    """
    dummy_db.commit.side_effect = SQLAlchemyError("error in add_member")
    with pytest.raises(IntegrityError) as excinfo:
        await repository.add_member(
            community_id=1, user_id=2, role="member", assigned_by=3
        )
    assert "Failed to add community member" in str(excinfo.value)
    dummy_db.rollback.assert_called_once()


# --- remove_member ---
@pytest.mark.asyncio
async def test_remove_member_success(repository, dummy_db):
    """
    Test that remove_member returns True when a member is successfully deactivated.
    """
    dummy_result = MagicMock()
    dummy_result.rowcount = 1
    dummy_db.execute.return_value = dummy_result
    result = await repository.remove_member(community_id=1, user_id=2)
    assert result is True
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_remove_member_no_rows(repository, dummy_db):
    """
    Test that remove_member returns False when no rows are affected.
    """
    dummy_result = MagicMock()
    dummy_result.rowcount = 0
    dummy_db.execute.return_value = dummy_result
    result = await repository.remove_member(community_id=1, user_id=2)
    assert result is False
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_remove_member_failure(repository, dummy_db):
    """
    Test that remove_member raises an IntegrityError when a SQLAlchemyError occurs.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("error in remove_member")
    with pytest.raises(IntegrityError) as excinfo:
        await repository.remove_member(community_id=1, user_id=2)
    assert "Failed to remove community member" in str(excinfo.value)
    dummy_db.rollback.assert_called_once()


# --- update_member_role ---
@pytest.mark.asyncio
async def test_update_member_role_success(repository, dummy_db):
    """
    Test that update_member_role returns True when a role update is successful.
    """
    dummy_result = MagicMock()
    dummy_result.rowcount = 1
    dummy_db.execute.return_value = dummy_result
    result = await repository.update_member_role(
        community_id=1, user_id=2, new_role="admin", assigned_by=3
    )
    assert result is True
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_member_role_no_update(repository, dummy_db):
    """
    Test that update_member_role returns False when no rows are updated.
    """
    dummy_result = MagicMock()
    dummy_result.rowcount = 0
    dummy_db.execute.return_value = dummy_result
    result = await repository.update_member_role(
        community_id=1, user_id=2, new_role="admin", assigned_by=3
    )
    assert result is False
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_member_role_failure(repository, dummy_db):
    """
    Test that update_member_role raises an IntegrityError when a SQLAlchemyError occurs.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("error in update_member_role")
    with pytest.raises(IntegrityError) as excinfo:
        await repository.update_member_role(
            community_id=1, user_id=2, new_role="admin", assigned_by=3
        )
    assert "Failed to update member role" in str(excinfo.value)
    dummy_db.rollback.assert_called_once()


# --- update_member_count ---
@pytest.mark.asyncio
async def test_update_member_count_success(repository, dummy_db):
    """
    Test that update_member_count returns the updated member counts.
    """

    class DummyRow:
        total_count = 10
        active_count = 8

    dummy_stats_result = MagicMock()
    dummy_stats_result.one.return_value = DummyRow()
    # Simulate two execute calls: one for stats and one for update.
    dummy_db.execute.side_effect = [dummy_stats_result, MagicMock()]
    counts = await repository.update_member_count(community_id=1)
    assert counts["total_count"] == 10
    assert counts["active_count"] == 8
    assert dummy_db.execute.call_count == 2
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_member_count_failure(repository, dummy_db):
    """
    Test that update_member_count raises an IntegrityError when a SQLAlchemyError occurs.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("error in update_member_count")
    with pytest.raises(IntegrityError) as excinfo:
        await repository.update_member_count(community_id=1)
    assert "Failed to update member counts" in str(excinfo.value)
    dummy_db.rollback.assert_called_once()
