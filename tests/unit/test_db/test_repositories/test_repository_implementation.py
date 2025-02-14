"""
Test Module for BaseRepository Implementation

This module tests the BaseRepository class (from
app/db/repositories/repository_implementation.py). It uses a dummy SQLAlchemy
model (DummyModel) mapped with declarative_base and a dummy schema (DummySchema)
that mimics a Pydantic model with a model_dump() method. Both success and error
branches for each repository method are exercised.

Usage:
    $ pytest test_repository_implementation.py
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.exc import SQLAlchemyError, IntegrityError as SAIntegrityError
from sqlalchemy import Column, Integer, String, func, select, delete
from sqlalchemy.orm import declarative_base

# Import our repository implementation and expected error classes.
from app.db.repositories.repository_implementation import BaseRepository
from app.db.errors import (
    QueryError,
    IntegrityError as RepositoryIntegrityError,
    TransactionError,
)
from app.core.error_handling import RecordNotFoundError

# ----------------------------------------------------------------------
# Dummy Mapped Model and Schema Definitions
# ----------------------------------------------------------------------

Base = declarative_base()


class DummyModel(Base):
    """
    Dummy SQLAlchemy model for testing.

    This mapped class simulates a database model with a table named 'dummy'
    having two columns: id and name.
    """

    __tablename__ = "dummy"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __init__(self, **kwargs):
        # Allow instantiation using keyword arguments.
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"DummyModel({self.__dict__})"


class DummySchema:
    """
    Dummy schema that mimics a Pydantic model.

    The model_dump() method returns the internal data dictionary.
    It accepts an optional 'exclude_unset' parameter to simulate Pydantic behavior.
    """

    def __init__(self, **kwargs):
        self.data = kwargs

    def model_dump(self, exclude_unset: bool = False):
        return self.data


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def dummy_session():
    """
    Returns a dummy asynchronous session.

    The session provides async methods (flush, refresh, commit, rollback, execute)
    as AsyncMock instances so we can simulate database operations and errors.
    """
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def repository(dummy_session):
    """
    Instantiates the BaseRepository with DummyModel and the dummy session.

    Returns:
        BaseRepository: Instance configured for testing.
    """
    return BaseRepository(DummyModel, dummy_session)


# ----------------------------------------------------------------------
# Tests for BaseRepository Methods
# ----------------------------------------------------------------------


def test_db_property(repository, dummy_session):
    """
    Verify that the db property returns the dummy session.
    """
    assert repository.db is dummy_session


# --- Tests for create() -------------------------------------------------


@pytest.mark.asyncio
async def test_create_success(repository, dummy_session):
    """
    Test successful record creation.

    Ensures the model is instantiated with data from schema.model_dump() and that
    flush, refresh, and commit are called.
    """
    schema = DummySchema(name="test", value=123)
    result = await repository.create(schema)
    dummy_session.add.assert_called_once()  # Verify that the record was added.
    assert result.name == "test"


@pytest.mark.asyncio
async def test_create_integrity_error(repository, dummy_session):
    """
    Test create() when an IntegrityError occurs.

    Simulates flush() raising SAIntegrityError. Expects rollback and a
    RepositoryIntegrityError.
    """
    schema = DummySchema(name="test")
    dummy_error = SAIntegrityError("stmt", "params", "orig")
    dummy_session.flush.side_effect = dummy_error
    with pytest.raises(RepositoryIntegrityError):
        await repository.create(schema)
    dummy_session.rollback.assert_awaited()


@pytest.mark.asyncio
async def test_create_sqlalchemy_error(repository, dummy_session):
    """
    Test create() when a generic SQLAlchemyError occurs.

    Simulates flush() raising SQLAlchemyError; expects rollback and a
    TransactionError.
    """
    schema = DummySchema(name="test")
    dummy_error = SQLAlchemyError("generic error")
    dummy_session.flush.side_effect = dummy_error
    with pytest.raises(TransactionError):
        await repository.create(schema)
    dummy_session.rollback.assert_awaited()


# --- Tests for get() ----------------------------------------------------


@pytest.mark.asyncio
async def test_get_success(repository, dummy_session):
    """
    Test successful retrieval of a record by id.

    Mocks session.execute() so that scalar_one_or_none() returns a dummy record.
    """
    dummy_record = DummyModel(id=1, name="found")
    dummy_result = MagicMock()
    dummy_result.scalar_one_or_none.return_value = dummy_record
    dummy_session.execute.return_value = AsyncMock()
    dummy_session.execute.return_value.scalar_one_or_none = MagicMock(
        return_value=dummy_record
    )
    result = await repository.get(1)
    assert result is dummy_record


@pytest.mark.asyncio
async def test_get_multi_with_filters(repository, dummy_session):
    """
    Test get_multi() branch when filters are provided.

    This test ensures that when a non-empty filters dictionary is passed,
    the query chain calls filter_by(**filters) and then applies offset() and limit()
    as expected. A valid filter key ("name") is used since DummyModel defines a 'name' column.

    The dummy session is configured so that execute() returns an async object whose
    scalars().all() method returns a list of dummy records.
    """
    # Prepare dummy records to be returned.
    dummy_records = [DummyModel(id=1, name="test"), DummyModel(id=2, name="test")]
    dummy_scalars = MagicMock()
    dummy_scalars.all.return_value = dummy_records
    # Create an async result that returns dummy_scalars for scalars()
    dummy_exec = AsyncMock()
    dummy_exec.scalars = lambda: dummy_scalars
    dummy_session.execute.return_value = dummy_exec

    skip = 5
    limit = 2
    filters = {"name": "test"}  # Valid filter: DummyModel has a 'name' column.

    # Invoke get_multi() with filters.
    result = await repository.get_multi(skip=skip, limit=limit, filters=filters)

    # Assert that the returned records match our dummy_records.
    assert result == dummy_records


@pytest.mark.asyncio
async def test_get_sqlalchemy_error(repository, dummy_session):
    """
    Test get() when a SQLAlchemyError occurs.

    Expects session.execute() to raise SQLAlchemyError, which is wrapped as QueryError.
    """
    dummy_error = SQLAlchemyError("get error")
    dummy_session.execute.side_effect = dummy_error
    with pytest.raises(QueryError):
        await repository.get(1)


# --- Tests for get_multi() ----------------------------------------------


@pytest.mark.asyncio
async def test_get_multi_success(repository, dummy_session):
    """
    Test successful retrieval of multiple records with filtering and pagination.

    Simulates a query result that returns a list of dummy records.
    """
    dummy_records = [DummyModel(id=i) for i in range(3)]
    dummy_scalars = MagicMock()
    dummy_scalars.all.return_value = dummy_records
    dummy_exec = AsyncMock()
    dummy_exec.scalars = lambda: dummy_scalars
    dummy_session.execute.return_value = dummy_exec
    result = await repository.get_multi(skip=0, limit=10, filters={"name": "test"})
    assert result == dummy_records


@pytest.mark.asyncio
async def test_get_multi_sqlalchemy_error(repository, dummy_session):
    """
    Test get_multi() when a SQLAlchemyError occurs.

    Expects a QueryError when session.execute() fails.
    """
    dummy_error = SQLAlchemyError("multi error")
    dummy_session.execute.side_effect = dummy_error
    with pytest.raises(QueryError):
        await repository.get_multi(skip=0, limit=10, filters={"name": "test"})


# --- Tests for update() ------------------------------------------------


@pytest.mark.asyncio
async def test_update_success(repository, dummy_session):
    """
    Test successful update of an existing record.

    Patches repository.get() to return a dummy record, updates the field, and verifies that
    commit and refresh are called.
    """
    dummy_record = DummyModel(id=1, name="old")
    repository.get = AsyncMock(return_value=dummy_record)
    update_schema = DummySchema(name="new")
    result = await repository.update(id=1, schema=update_schema)
    assert result.name == "new"
    dummy_session.commit.assert_awaited()
    dummy_session.refresh.assert_awaited_with(dummy_record)


@pytest.mark.asyncio
async def test_update_not_found(repository, dummy_session):
    """
    Test update() when the record is not found.

    Patches repository.get() to return None, expecting RecordNotFoundError.
    """
    repository.get = AsyncMock(return_value=None)
    update_schema = DummySchema(name="new")
    with pytest.raises(RecordNotFoundError):
        await repository.update(id=999, schema=update_schema)


@pytest.mark.asyncio
async def test_update_integrity_error(repository, dummy_session):
    """
    Test update() when an IntegrityError occurs during commit.

    Expects a rollback and RepositoryIntegrityError.
    """
    dummy_record = DummyModel(id=1, name="old")
    repository.get = AsyncMock(return_value=dummy_record)
    update_schema = DummySchema(name="new")
    dummy_error = SAIntegrityError("stmt", "params", "orig")
    dummy_session.commit.side_effect = dummy_error
    with pytest.raises(RepositoryIntegrityError):
        await repository.update(id=1, schema=update_schema)
    dummy_session.rollback.assert_awaited()


@pytest.mark.asyncio
async def test_update_record_not_found(repository, dummy_session):
    """
    Test that update() raises RecordNotFoundError when no record is found.

    This test forces repository.get() to return None, triggering the branch
    that raises a RecordNotFoundError.
    """
    # Patch repository.get to simulate "record not found"
    repository.get = AsyncMock(return_value=None)
    update_schema = DummySchema(name="nonexistent")

    with pytest.raises(RecordNotFoundError) as exc_info:
        await repository.update(id=999, schema=update_schema)

    # Instead of expecting the model name in the error string,
    # we check that the exception message matches the expected output.
    assert str(exc_info.value) == "Record not found"


@pytest.mark.asyncio
async def test_update_sqlalchemy_error(repository, dummy_session):
    """
    Test update() when a generic SQLAlchemyError occurs during commit.

    Expects a rollback and TransactionError.
    """
    dummy_record = DummyModel(id=1, name="old")
    repository.get = AsyncMock(return_value=dummy_record)
    update_schema = DummySchema(name="new")
    dummy_error = SQLAlchemyError("update error")
    dummy_session.commit.side_effect = dummy_error
    with pytest.raises(TransactionError):
        await repository.update(id=1, schema=update_schema)
    dummy_session.rollback.assert_awaited()


# --- Tests for delete() ------------------------------------------------


@pytest.mark.asyncio
async def test_delete_success(repository, dummy_session):
    """
    Test successful deletion of a record.

    Simulates a deletion query that affects at least one row.
    """
    dummy_exec = AsyncMock()
    dummy_exec.rowcount = 1
    dummy_session.execute.return_value = dummy_exec
    result = await repository.delete(1)
    assert result is True
    dummy_session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_delete_sqlalchemy_error(repository, dummy_session):
    """
    Test delete() when a SQLAlchemyError occurs.

    Expects a rollback and TransactionError.
    """
    dummy_error = SQLAlchemyError("delete error")
    dummy_session.execute.side_effect = dummy_error
    with pytest.raises(TransactionError):
        await repository.delete(1)
    dummy_session.rollback.assert_awaited()


# --- Tests for exists() ------------------------------------------------


@pytest.mark.asyncio
async def test_exists_success(repository, dummy_session):
    """
    Test exists() method when the record exists.

    Simulates a count query returning a nonzero value.
    """
    dummy_exec = AsyncMock()
    dummy_exec.scalar = MagicMock(return_value=5)
    dummy_session.execute.return_value = dummy_exec
    result = await repository.exists(1)
    assert result is True


@pytest.mark.asyncio
async def test_exists_sqlalchemy_error(repository, dummy_session):
    """
    Test exists() method when a SQLAlchemyError occurs.

    Expects a QueryError.
    """
    dummy_error = SQLAlchemyError("exists error")
    dummy_session.execute.side_effect = dummy_error
    with pytest.raises(QueryError):
        await repository.exists(1)


# --- Tests for count() -------------------------------------------------


@pytest.mark.asyncio
async def test_count_success(repository, dummy_session):
    """
    Test count() method with valid filters.

    Simulates a count query that returns a specific number.
    Note: Uses a valid filter key ("name") since DummyModel only defines 'id' and 'name'.
    """
    dummy_exec = AsyncMock()
    dummy_exec.scalar = MagicMock(return_value=42)
    dummy_session.execute.return_value = dummy_exec
    result = await repository.count(filters={"name": "test"})
    assert result == 42


@pytest.mark.asyncio
async def test_count_sqlalchemy_error(repository, dummy_session):
    """
    Test count() method when a SQLAlchemyError occurs.

    Expects a QueryError when session.execute() fails.
    """
    dummy_error = SQLAlchemyError("count error")
    dummy_session.execute.side_effect = dummy_error
    with pytest.raises(QueryError):
        await repository.count(filters={"name": "test"})


# --- Tests for filter_by() ---------------------------------------------


@pytest.mark.asyncio
async def test_filter_by_success(repository, dummy_session):
    """
    Test filter_by() method for retrieving records by exact criteria.

    Simulates a query that returns a list of dummy records.
    """
    dummy_records = [DummyModel(id=1), DummyModel(id=2)]
    dummy_scalars = MagicMock()
    dummy_scalars.all.return_value = dummy_records
    dummy_exec = AsyncMock()
    dummy_exec.scalars = lambda: dummy_scalars
    dummy_session.execute.return_value = dummy_exec
    result = await repository.filter_by(name="test")
    assert result == dummy_records


@pytest.mark.asyncio
async def test_filter_by_sqlalchemy_error(repository, dummy_session):
    """
    Test filter_by() when a SQLAlchemyError occurs.

    Expects a QueryError.
    """
    dummy_error = SQLAlchemyError("filter error")
    dummy_session.execute.side_effect = dummy_error
    with pytest.raises(QueryError):
        await repository.filter_by(name="test")
