"""
Integration tests for the Contact Endorsement Repository.

This module tests that the repository instance correctly composes the mixins
and provides all expected methods.
"""

import pytest
from unittest.mock import MagicMock

from app.db.repositories.contact_endorsement_repository.repository import (
    ContactEndorsementRepository,
)


@pytest.fixture
def dummy_db():
    """
    Fixture that returns a dummy database session with basic methods.
    """
    db = MagicMock()
    db.execute = MagicMock()
    db.get = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    return db


@pytest.fixture
def repository(dummy_db):
    """
    Fixture that returns a Contact Endorsement Repository instance with a dummy DB session.
    """
    repo = ContactEndorsementRepository(dummy_db)
    repo._logger = MagicMock()
    return repo


def test_repository_has_methods(repository):
    """
    Test that the repository instance has all expected methods from the mixins.
    """
    assert hasattr(repository, "get_by_contact_and_user")
    assert hasattr(repository, "get_by_community")
    assert hasattr(repository, "get_stats")
    assert hasattr(repository, "delete_by_contact_and_user")
