"""
Unit tests for the Community Repository Queries Mixin.

This module tests all read-only operations for community data access. It covers:
  - Retrieving a community by name.
  - Retrieving a community with relationships.
  - Getting a member's role.
  - Getting members by role.
  - Retrieving communities for a user.
  - Retrieving related communities.
  - Searching communities.
  - Getting pending membership requests.
  - Getting community member statistics.

Both positive (successful) and negative (error) branches are tested.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.repositories.community_repository.repository import CommunityRepository
from app.db.errors import QueryError
from app.db.models.community_model import Community, PrivacyLevel
from app.db.models.community_member_model import CommunityMember
from app.db.models.user_model import User


@pytest.fixture
def dummy_db():
    """
    Fixture that returns a dummy database session with async methods.
    """
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def repository(dummy_db):
    """
    Fixture that returns a CommunityRepository instance with a dummy DB session.

    The _logger is set to a MagicMock and _model is set to Community.
    """
    repo = CommunityRepository(dummy_db)
    repo._logger = MagicMock()
    repo._model = Community
    return repo


# --- get_by_name ---
@pytest.mark.asyncio
async def test_get_by_name_success(repository, dummy_db):
    """
    Test that get_by_name returns the expected community on success.
    """
    dummy_comm = Community()
    dummy_result = MagicMock()
    dummy_result.scalar_one_or_none.return_value = dummy_comm
    dummy_db.execute.return_value = dummy_result

    result = await repository.get_by_name("Test Community")
    assert result == dummy_comm
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_name_failure(repository, dummy_db):
    """
    Test that get_by_name raises a QueryError when a SQLAlchemyError occurs.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("error")
    with pytest.raises(QueryError) as excinfo:
        await repository.get_by_name("Test Community")
    assert "Failed to retrieve community by name" in str(excinfo.value)
    dummy_db.execute.assert_called_once()


# --- get_with_relationships ---
@pytest.mark.asyncio
async def test_get_with_relationships_success(repository, dummy_db):
    """
    Test that get_with_relationships returns the expected community with relationships.
    """
    dummy_comm = Community()
    dummy_result = MagicMock()
    dummy_result.scalar_one_or_none.return_value = dummy_comm
    dummy_db.execute.return_value = dummy_result

    result = await repository.get_with_relationships(1)
    assert result == dummy_comm
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_with_relationships_failure(repository, dummy_db):
    """
    Test that get_with_relationships raises a QueryError when a SQLAlchemyError occurs.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("error")
    with pytest.raises(QueryError) as excinfo:
        await repository.get_with_relationships(1)
    assert "Failed to retrieve community with relationships" in str(excinfo.value)
    dummy_db.execute.assert_called_once()


# --- get_member_role ---
@pytest.mark.asyncio
async def test_get_member_role_success(repository, dummy_db):
    """
    Test that get_member_role returns the expected role.
    """
    dummy_result = MagicMock()
    dummy_result.scalar_one_or_none.return_value = "admin"
    dummy_db.execute.return_value = dummy_result

    result = await repository.get_member_role(1, 2)
    assert result == "admin"
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_member_role_failure(repository, dummy_db):
    """
    Test that get_member_role raises a QueryError when a SQLAlchemyError occurs.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("error")
    with pytest.raises(QueryError) as excinfo:
        await repository.get_member_role(1, 2)
    assert "Failed to retrieve member role" in str(excinfo.value)
    dummy_db.execute.assert_called_once()


# --- get_members_by_role ---
@pytest.mark.asyncio
async def test_get_members_by_role_success(repository, dummy_db):
    """
    Test that get_members_by_role returns the expected list of users.
    """
    user1 = User()
    user2 = User()
    dummy_result = MagicMock()
    dummy_result.scalars.return_value.all.return_value = [user1, user2]
    dummy_db.execute.return_value = dummy_result

    result = await repository.get_members_by_role(1, "member")
    assert result == [user1, user2]
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_members_by_role_failure(repository, dummy_db):
    """
    Test that get_members_by_role raises a QueryError when a SQLAlchemyError occurs.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("error")
    with pytest.raises(QueryError) as excinfo:
        await repository.get_members_by_role(1, "member")
    assert "Failed to retrieve members by role" in str(excinfo.value)
    dummy_db.execute.assert_called_once()


# --- get_user_communities ---
@pytest.mark.asyncio
async def test_get_user_communities_success(repository, dummy_db):
    """
    Test that get_user_communities returns the expected communities.
    """
    comm1 = Community()
    comm2 = Community()
    dummy_result = MagicMock()
    dummy_result.scalars.return_value.all.return_value = [comm1, comm2]
    dummy_db.execute.return_value = dummy_result

    result = await repository.get_user_communities(
        1, active_only=True, privacy_level=PrivacyLevel.PUBLIC
    )
    assert result == [comm1, comm2]
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_communities_failure(repository, dummy_db):
    """
    Test that get_user_communities raises a QueryError when a SQLAlchemyError occurs.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("error")
    with pytest.raises(QueryError) as excinfo:
        await repository.get_user_communities(1)
    assert "Failed to retrieve user communities" in str(excinfo.value)
    dummy_db.execute.assert_called_once()


# --- get_related_communities ---
@pytest.mark.asyncio
async def test_get_related_communities_success(repository, dummy_db):
    """
    Test that get_related_communities returns the expected list of related communities.
    """
    comm1 = Community()
    dummy_result = MagicMock()
    dummy_result.scalars.return_value.all.return_value = [comm1]
    dummy_db.execute.return_value = dummy_result

    result = await repository.get_related_communities(1, active_only=True)
    assert result == [comm1]
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_related_communities_failure(repository, dummy_db):
    """
    Test that get_related_communities raises a QueryError when a SQLAlchemyError occurs.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("error")
    with pytest.raises(QueryError) as excinfo:
        await repository.get_related_communities(1)
    assert "Failed to retrieve related communities" in str(excinfo.value)
    dummy_db.execute.assert_called_once()


# --- search_communities ---
@pytest.mark.asyncio
async def test_search_communities_success(repository, dummy_db):
    """
    Test that search_communities returns the expected list of communities.
    """
    comm1 = Community()
    dummy_result = MagicMock()
    dummy_result.scalars.return_value.all.return_value = [comm1]
    dummy_db.execute.return_value = dummy_result

    result = await repository.search_communities(
        "test", skip=0, limit=10, privacy_level=PrivacyLevel.PUBLIC, active_only=True
    )
    assert result == [comm1]
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_search_communities_failure(repository, dummy_db):
    """
    Test that search_communities raises a QueryError when a SQLAlchemyError occurs.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("error")
    with pytest.raises(QueryError) as excinfo:
        await repository.search_communities("test")
    assert "Failed to search communities" in str(excinfo.value)
    dummy_db.execute.assert_called_once()


# --- get_pending_members ---
@pytest.mark.asyncio
async def test_get_pending_members_success(repository, dummy_db):
    """
    Test that get_pending_members returns the expected list of pending members.
    """
    user = User()
    pending_date = datetime(2022, 1, 1)
    dummy_result = MagicMock()
    dummy_result.all.return_value = [(user, pending_date)]
    dummy_db.execute.return_value = dummy_result

    result = await repository.get_pending_members(1)
    assert result == [(user, pending_date)]
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_pending_members_failure(repository, dummy_db):
    """
    Test that get_pending_members raises a QueryError when a SQLAlchemyError occurs.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("error")
    with pytest.raises(QueryError) as excinfo:
        await repository.get_pending_members(1)
    assert "Failed to retrieve pending members" in str(excinfo.value)
    dummy_db.execute.assert_called_once()


# --- get_member_stats ---
@pytest.mark.asyncio
async def test_get_member_stats_success(repository, dummy_db):
    """
    Test that get_member_stats returns correct member statistics.
    """

    class DummyRow:
        total_members = 10
        active_members = 8

    dummy_result = MagicMock()
    dummy_result.one.return_value = DummyRow()
    dummy_db.execute.return_value = dummy_result

    stats = await repository.get_member_stats(1)
    assert stats["total_members"] == 10
    assert stats["active_members"] == 8
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_member_stats_failure(repository, dummy_db):
    """
    Test that get_member_stats raises a QueryError when a SQLAlchemyError occurs.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("error")
    with pytest.raises(QueryError) as excinfo:
        await repository.get_member_stats(1)
    assert "Failed to retrieve member statistics" in str(excinfo.value)
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_related_communities_active_only_false(repository, dummy_db):
    """
    Test that get_related_communities correctly returns results
    when active_only is set to False (i.e. the extra active filter is skipped).
    """
    # Setup: simulate a dummy result with one related community.
    dummy_comm = Community()
    dummy_result = MagicMock()
    # Simulate scalars().all() returning a list of communities.
    dummy_result.scalars.return_value.all.return_value = [dummy_comm]
    dummy_db.execute.return_value = dummy_result

    # Call get_related_communities with active_only=False.
    result = await repository.get_related_communities(community_id=1, active_only=False)
    assert result == [dummy_comm]
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_search_communities_with_privacy_level(repository, dummy_db):
    """
    Test that search_communities correctly adds the privacy level condition
    when a non-None privacy_level is provided.
    """
    # Setup: simulate a dummy community and a dummy result.
    dummy_comm = Community()
    dummy_result = MagicMock()
    dummy_result.scalars.return_value.all.return_value = [dummy_comm]
    dummy_db.execute.return_value = dummy_result

    # Call search_communities with a privacy_level provided.
    result = await repository.search_communities(
        search_term="example",
        skip=0,
        limit=10,
        privacy_level=PrivacyLevel.PRIVATE,
        active_only=True,
    )
    assert result == [dummy_comm]
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_member_stats_with_none_counts(repository, dummy_db):
    """
    Test that get_member_stats returns 0 for total_members and active_members
    when the database returns None values.
    """

    # Create a dummy row where counts are None.
    class DummyRow:
        total_members = None
        active_members = None

    dummy_result = MagicMock()
    dummy_result.one.return_value = DummyRow()
    dummy_db.execute.return_value = dummy_result

    stats = await repository.get_member_stats(community_id=1)
    assert stats["total_members"] == 0
    assert stats["active_members"] == 0
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_related_communities_active_true(repository, dummy_db):
    """
    Test that get_related_communities calls is_active.is_(True) when active_only is True.

    This ensures that the branch inside the if active_only: block (lines 201-208) is executed.
    """
    # Set up a dummy for is_active on the _model.
    dummy_active = MagicMock()
    dummy_active.is_.return_value = "active filter"
    # Override the _model's is_active attribute.
    repository._model.is_active = dummy_active

    # Simulate a dummy result with one related community.
    dummy_comm = Community()
    dummy_result = MagicMock()
    dummy_result.scalars.return_value.all.return_value = [dummy_comm]
    dummy_db.execute.return_value = dummy_result

    # Call get_related_communities with active_only=True.
    result = await repository.get_related_communities(community_id=1, active_only=True)
    assert result == [dummy_comm]
    # Verify that is_active.is_(True) was indeed called.
    dummy_active.is_.assert_called_once_with(True)


@pytest.mark.asyncio
async def test_get_related_communities_active_true(repository, dummy_db):
    """
    Test that get_related_communities applies the active filter when active_only is True.

    This ensures that the branch in which the query adds:
        .where(self._model.is_active.is_(True))
    is executed.
    """
    # Set up a dummy for is_active on the _model using a valid SQLAlchemy expression.
    dummy_active = MagicMock()
    dummy_active.is_.return_value = text("1=1")
    repository._model.is_active = dummy_active

    # Simulate a dummy result with one related community.
    dummy_comm = Community()
    dummy_result = MagicMock()
    dummy_result.scalars.return_value.all.return_value = [dummy_comm]
    dummy_db.execute.return_value = dummy_result

    # Call get_related_communities with active_only=True.
    result = await repository.get_related_communities(community_id=1, active_only=True)
    assert result == [dummy_comm]
    dummy_active.is_.assert_called_once_with(True)


@pytest.mark.asyncio
async def test_search_communities_active_true(repository, dummy_db):
    """
    Test that search_communities applies the active filter when active_only is True.

    This ensures that the branch adding:
        conditions.append(self._model.is_active.is_(True))
    is executed.
    """
    # Set up a dummy for is_active on the _model using a valid SQLAlchemy expression.
    dummy_active = MagicMock()
    dummy_active.is_.return_value = text("1=1")
    repository._model.is_active = dummy_active

    # Simulate a dummy result with one matching community.
    dummy_comm = Community()
    dummy_result = MagicMock()
    dummy_result.scalars.return_value.all.return_value = [dummy_comm]
    dummy_db.execute.return_value = dummy_result

    # Call search_communities with active_only=True and no privacy_level.
    result = await repository.search_communities(
        search_term="test", skip=0, limit=10, privacy_level=None, active_only=True
    )
    assert result == [dummy_comm]
    dummy_active.is_.assert_called_once_with(True)


@pytest.mark.asyncio
async def test_get_member_role_returns_none(repository, dummy_db):
    """
    Test that get_member_role returns None when no active member role is found.

    This covers the branch where result.scalar_one_or_none() returns None.
    """
    dummy_result = MagicMock()
    dummy_result.scalar_one_or_none.return_value = None
    dummy_db.execute.return_value = dummy_result

    result = await repository.get_member_role(community_id=1, user_id=2)
    assert result is None
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_search_communities_empty(repository, dummy_db):
    """
    Test that search_communities returns an empty list when no communities match the criteria.

    This covers the branch where result.scalars().all() returns an empty list.
    """
    dummy_result = MagicMock()
    dummy_result.scalars.return_value.all.return_value = []
    dummy_db.execute.return_value = dummy_result

    result = await repository.search_communities(
        search_term="nonexistent",
        skip=0,
        limit=10,
        privacy_level=None,
        active_only=True,
    )
    assert result == []
    dummy_db.execute.assert_called_once()
