"""
Integration tests for the Community Repository.

This module tests that the repository instance correctly composes the queries
and actions mixins, providing all expected methods.
"""

import pytest
from unittest.mock import MagicMock
from app.db.repositories.community_repository.repository import CommunityRepository


@pytest.fixture
def dummy_db():
    """
    Fixture that returns a dummy database session with basic methods.
    """
    db = MagicMock()
    db.execute = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    return db


@pytest.fixture
def repository(dummy_db):
    """
    Fixture that returns a CommunityRepository instance with a dummy DB session.
    """
    repo = CommunityRepository(dummy_db)
    repo._logger = MagicMock()
    return repo


def test_repository_has_methods(repository):
    """
    Test that the repository instance has all expected query and action methods.
    """
    # Query methods
    assert hasattr(repository, "get_by_name")
    assert hasattr(repository, "get_with_relationships")
    assert hasattr(repository, "get_member_role")
    assert hasattr(repository, "get_members_by_role")
    assert hasattr(repository, "get_user_communities")
    assert hasattr(repository, "get_related_communities")
    assert hasattr(repository, "search_communities")
    assert hasattr(repository, "get_pending_members")
    assert hasattr(repository, "get_member_stats")
    # Action methods
    assert hasattr(repository, "add_member")
    assert hasattr(repository, "remove_member")
    assert hasattr(repository, "update_member_role")
    assert hasattr(repository, "update_member_count")
