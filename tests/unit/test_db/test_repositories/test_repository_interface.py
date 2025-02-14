from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock
import pytest
from sqlalchemy.orm import Session

from app.db.repositories.repository_interface import IRepository


class DummyRepository(IRepository[int, dict, dict]):
    """
    Dummy implementation of the IRepository protocol.

    This class implements each method with fixed dummy behavior:
        - create returns 1
        - get returns the same identifier passed in
        - get_multi returns a range based on skip/limit
        - update returns the same identifier
        - delete returns True
        - exists returns True
        - count returns 42
        - filter_by returns a fixed list [1, 2, 3]
        - bulk_create returns a list of 1's matching the length of the input list
        - bulk_update returns the same list of identifiers
        - bulk_delete returns the number of ids provided
    """

    def __init__(self, db: Session):
        self._db = db

    @property
    def db(self) -> Session:
        return self._db

    async def create(self, schema: dict) -> int:
        return 1

    async def get(self, id: Any) -> Optional[int]:
        return id

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[int]:
        return list(range(skip, skip + limit))

    async def update(self, *, id: Any, schema: dict) -> Optional[int]:
        return id

    async def delete(self, id: Any) -> bool:
        return True

    async def exists(self, id: Any) -> bool:
        return True

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        return 42

    def filter_by(self, **kwargs) -> List[int]:
        return [1, 2, 3]

    async def bulk_create(self, schemas: List[dict]) -> List[int]:
        return [1 for _ in schemas]

    async def bulk_update(self, ids: List[Any], schema: dict) -> List[int]:
        return ids

    async def bulk_delete(self, ids: List[Any]) -> int:
        return len(ids)


@pytest.fixture
def dummy_session() -> Session:
    """
    Fixture that returns a dummy synchronous database session.
    """
    return MagicMock(spec=Session)


@pytest.fixture
def dummy_repo(dummy_session) -> DummyRepository:
    """
    Fixture that returns an instance of the DummyRepository.
    """
    return DummyRepository(dummy_session)


@pytest.mark.asyncio
async def test_db_property(dummy_repo, dummy_session):
    """
    Test that the db property returns the correct database session.
    """
    assert dummy_repo.db == dummy_session


@pytest.mark.asyncio
async def test_create(dummy_repo):
    """
    Test that create() returns the expected dummy record ID.
    """
    result = await dummy_repo.create({"key": "value"})
    assert result == 1


@pytest.mark.asyncio
async def test_get(dummy_repo):
    """
    Test that get() returns the provided identifier.
    """
    rec_id = 5
    record = await dummy_repo.get(rec_id)
    assert record == rec_id


@pytest.mark.asyncio
async def test_get_multi(dummy_repo):
    """
    Test that get_multi() returns a list of record IDs based on pagination.
    """
    skip = 10
    limit = 5
    records = await dummy_repo.get_multi(skip=skip, limit=limit)
    assert records == list(range(skip, skip + limit))


@pytest.mark.asyncio
async def test_get_multi_default(dummy_repo):
    """
    Test that get_multi() returns the default range when no parameters are provided.
    """
    records = await dummy_repo.get_multi()
    assert records == list(range(0, 100))


@pytest.mark.asyncio
async def test_update(dummy_repo):
    """
    Test that update() returns the identifier after update.
    """
    rec_id = 7
    updated = await dummy_repo.update(id=rec_id, schema={"key": "new"})
    assert updated == rec_id


@pytest.mark.asyncio
async def test_delete(dummy_repo):
    """
    Test that delete() returns True indicating deletion was successful.
    """
    result = await dummy_repo.delete(3)
    assert result is True


@pytest.mark.asyncio
async def test_exists(dummy_repo):
    """
    Test that exists() returns True indicating the record exists.
    """
    exists = await dummy_repo.exists(8)
    assert exists is True


@pytest.mark.asyncio
async def test_count_with_filters(dummy_repo):
    """
    Test that count() returns the dummy count when filters are provided.
    """
    count = await dummy_repo.count(filters={"dummy": True})
    assert count == 42


@pytest.mark.asyncio
async def test_count_default(dummy_repo):
    """
    Test that count() returns the dummy count when no filters are provided.
    """
    count = await dummy_repo.count()
    assert count == 42


def test_filter_by(dummy_repo):
    """
    Test that filter_by() returns the expected fixed list of record IDs.
    """
    records = dummy_repo.filter_by(key="value")
    assert records == [1, 2, 3]


def test_filter_by_no_kwargs(dummy_repo):
    """
    Test that filter_by() returns the expected fixed list when no keyword arguments are provided.
    """
    records = dummy_repo.filter_by()
    assert records == [1, 2, 3]


@pytest.mark.asyncio
async def test_bulk_create(dummy_repo):
    """
    Test that bulk_create() returns a list of dummy record IDs for a non-empty input.
    """
    schemas = [{"a": 1}, {"b": 2}]
    records = await dummy_repo.bulk_create(schemas)
    assert records == [1, 1]


@pytest.mark.asyncio
async def test_bulk_create_empty(dummy_repo):
    """
    Test that bulk_create() returns an empty list when provided an empty input list.
    """
    schemas: List[dict] = []
    records = await dummy_repo.bulk_create(schemas)
    assert records == []


@pytest.mark.asyncio
async def test_bulk_update(dummy_repo):
    """
    Test that bulk_update() returns the same list of IDs for a non-empty input.
    """
    ids = [2, 3, 4]
    updated = await dummy_repo.bulk_update(ids, {"key": "value"})
    assert updated == ids


@pytest.mark.asyncio
async def test_bulk_update_empty(dummy_repo):
    """
    Test that bulk_update() returns an empty list when provided an empty list of IDs.
    """
    ids: List[Any] = []
    updated = await dummy_repo.bulk_update(ids, {"key": "value"})
    assert updated == []


@pytest.mark.asyncio
async def test_bulk_delete(dummy_repo):
    """
    Test that bulk_delete() returns the number of deleted records.
    """
    ids = [5, 6]
    deleted_count = await dummy_repo.bulk_delete(ids)
    assert deleted_count == len(ids)


@pytest.mark.asyncio
async def test_bulk_delete_empty(dummy_repo):
    """
    Test that bulk_delete() returns zero when provided an empty list of IDs.
    """
    ids: List[Any] = []
    deleted_count = await dummy_repo.bulk_delete(ids)
    assert deleted_count == 0


# Create a dummy implementation that does not override any methods.
class IncompleteRepository(IRepository[int, dict, dict]):
    pass


def test_incomplete_db_property():
    repo = IncompleteRepository()
    # The db property, not being overridden, executes the default implementation.
    # It should return None.
    assert repo.db is None


@pytest.mark.asyncio
async def test_incomplete_create():
    repo = IncompleteRepository()
    result = await repo.create({})
    assert result is None


@pytest.mark.asyncio
async def test_incomplete_get():
    repo = IncompleteRepository()
    result = await repo.get(42)
    assert result is None


@pytest.mark.asyncio
async def test_incomplete_get_multi():
    repo = IncompleteRepository()
    result = await repo.get_multi(skip=5, limit=10, filters={"foo": "bar"})
    assert result is None


@pytest.mark.asyncio
async def test_incomplete_update():
    repo = IncompleteRepository()
    result = await repo.update(id=99, schema={"key": "value"})
    assert result is None


@pytest.mark.asyncio
async def test_incomplete_delete():
    repo = IncompleteRepository()
    result = await repo.delete(1)
    assert result is None


@pytest.mark.asyncio
async def test_incomplete_exists():
    repo = IncompleteRepository()
    result = await repo.exists(1)
    assert result is None


@pytest.mark.asyncio
async def test_incomplete_count():
    repo = IncompleteRepository()
    result = await repo.count(filters={"active": True})
    assert result is None


def test_incomplete_filter_by():
    repo = IncompleteRepository()
    result = repo.filter_by(name="test")
    assert result is None


@pytest.mark.asyncio
async def test_incomplete_bulk_create():
    repo = IncompleteRepository()
    result = await repo.bulk_create([{"a": 1}, {"b": 2}])
    assert result is None


@pytest.mark.asyncio
async def test_incomplete_bulk_update():
    repo = IncompleteRepository()
    result = await repo.bulk_update(ids=[1, 2, 3], schema={"update": True})
    assert result is None


@pytest.mark.asyncio
async def test_incomplete_bulk_delete():
    repo = IncompleteRepository()
    result = await repo.bulk_delete(ids=[1, 2])
    assert result is None
