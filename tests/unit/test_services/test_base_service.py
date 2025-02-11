"""
Unit tests for BaseService.

This module contains tests for verifying the functionality of the BaseService class,
including CRUD operations, business rule enforcement, and error handling.

Key Test Cases:
- Creating a new record
- Retrieving a single record
- Retrieving multiple records
- Updating a record
- Deleting a record
- Handling service exceptions
- Validating pre/post-processing hooks

Dependencies:
    - pytest
    - unittest.mock
"""

from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
import pytest
from app.services.base_service import BaseService, ServiceException
from app.services.base_service import ValidationException
from app.core.error_handling import BusinessLogicError


@pytest.fixture
def base_service(mock_model, mock_repository):
    """
    Instantiate BaseService with mocked dependencies.

    Args:
        mock_model (MagicMock): Mocked SQLAlchemy model.
        mock_repository (MagicMock): Mocked repository instance.

    Returns:
        BaseService: An instance of BaseService with mocks.
    """
    return BaseService(mock_model, mock_repository)


@pytest.mark.asyncio
async def test_create_success(base_service, mock_repository):
    """
    Test successful record creation.

    Ensures that:
    - The repository create method is called with the correct data.
    - The returned record matches the expected model instance.
    - Pre- and post-processing hooks are executed correctly.
    """
    data = MagicMock()
    mock_record = MagicMock()

    # Mock repository behavior
    mock_repository.create.return_value = mock_record

    result = await base_service.create(data)

    assert result == mock_record
    mock_repository.create.assert_called_once_with(data)


@pytest.mark.asyncio
async def test_create_validation_exception(base_service):
    """
    Test validation exception during record creation.

    Ensures that:
    - BusinessLogicError is raised and transformed into ValidationException.
    - The repository create method is never called.
    """
    data = MagicMock()

    # ✅ Ensure `validate_create` raises `BusinessLogicError`
    base_service.validate_create = AsyncMock(
        side_effect=BusinessLogicError("Invalid data")
    )

    # ✅ Use `async with` to properly capture async exceptions
    with pytest.raises(ValidationException) as exc_info:
        await base_service.create(data)

    # ✅ Check that the message matches
    assert "Invalid data" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_generic_exception(base_service, mock_repository):
    """
    Test the create method when an unexpected (non-BusinessLogicError)
    exception occurs (e.g. in pre_create).
    """
    data = MagicMock()
    base_service.validate_create = AsyncMock(return_value=None)
    # Simulate pre_create raising a generic Exception.
    base_service.pre_create = AsyncMock(side_effect=Exception("Pre-create failed"))
    with pytest.raises(ServiceException, match="Failed to create"):
        await base_service.create(data)


@pytest.mark.asyncio
async def test_get_existing_record(base_service, mock_repository):
    """
    Test retrieving an existing record by ID.

    Ensures that:
    - The correct record is returned from the repository.
    - The check_access method is called for access control.
    """
    mock_record = MagicMock()
    mock_repository.get.return_value = mock_record

    result = await base_service.get(1)

    assert result == mock_record
    mock_repository.get.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_generic_exception(base_service, mock_repository):
    """
    Test the get method when repository.get raises a generic exception.
    """
    mock_repository.get.side_effect = Exception("DB failure")
    with pytest.raises(ServiceException, match="Failed to retrieve"):
        await base_service.get(1)


@pytest.mark.asyncio
async def test_get_check_access_http_exception(base_service, mock_repository):
    """
    Test the get method when check_access raises an HTTPException.
    The HTTPException should propagate.
    """
    record = MagicMock()
    mock_repository.get.return_value = record
    base_service.check_access = AsyncMock(side_effect=HTTPException(status_code=403))
    with pytest.raises(HTTPException):
        await base_service.get(1)


@pytest.mark.asyncio
async def test_get_non_existent_record(base_service, mock_repository):
    """
    Test retrieving a non-existent record.

    Ensures that:
    - The service returns None if the record is not found.
    """
    mock_repository.get.return_value = None

    result = await base_service.get(999)

    assert result is None
    mock_repository.get.assert_called_once_with(999)


@pytest.mark.asyncio
async def test_get_multi(base_service, mock_repository):
    """
    Test retrieving multiple records.

    Ensures that:
    - The repository get_multi method is called with the correct parameters.
    - The retrieved records match the expected result.
    """
    mock_records = [MagicMock(), MagicMock()]
    mock_repository.get_multi.return_value = mock_records

    result = await base_service.get_multi(skip=0, limit=10)

    assert result == mock_records
    mock_repository.get_multi.assert_called_once_with(skip=0, limit=10, filters={})


@pytest.mark.asyncio
async def test_get_multi_with_filters(base_service, mock_repository):
    """
    Test get_multi using a custom process_filters override.
    The repository.get_multi should be called with the processed filters.
    """

    async def custom_process_filters(filters):
        return {"custom": "value"}

    base_service.process_filters = AsyncMock(side_effect=custom_process_filters)
    records = [MagicMock(), MagicMock()]
    mock_repository.get_multi.return_value = records

    result = await base_service.get_multi(skip=5, limit=20, filters={"ignored": "test"})
    mock_repository.get_multi.assert_called_once_with(
        skip=5, limit=20, filters={"custom": "value"}
    )
    assert result == records


@pytest.mark.asyncio
async def test_get_multi_filter_can_access(base_service, mock_repository):
    """
    Test that get_multi only returns records for which can_access returns True.
    """
    record1 = MagicMock()
    record2 = MagicMock()
    records = [record1, record2]
    mock_repository.get_multi.return_value = records

    async def custom_can_access(record):
        return record is record2  # Only record2 is accessible

    base_service.can_access = custom_can_access
    result = await base_service.get_multi(skip=0, limit=10)
    assert result == [record2]


@pytest.mark.asyncio
async def test_update_success(base_service, mock_repository):
    """
    Test successful record update.

    Ensures that:
    - The repository update method is called with the correct parameters.
    - The returned record matches the expected model instance.
    """
    mock_record = MagicMock()
    data = MagicMock()
    mock_repository.update.return_value = mock_record

    result = await base_service.update(id=1, data=data)

    assert result == mock_record
    mock_repository.update.assert_called_once_with(id=1, schema=data)


@pytest.mark.asyncio
async def test_update_with_validation_exception(base_service):
    """
    Test validation exception during record update.

    Ensures that:
    - BusinessLogicError is raised and transformed into ValidationException.
    - The repository update method is never called.
    """
    data = MagicMock()

    async def mock_validate(id, data):
        raise BusinessLogicError("Invalid update")

    base_service.validate_update = mock_validate

    with pytest.raises(
        ValidationException, match="Invalid update"
    ):  # ✅ Expect ValidationException
        await base_service.update(id=1, data=data)


@pytest.mark.asyncio
async def test_update_generic_exception(base_service, mock_repository):
    """
    Test the update method when a generic (non-BusinessLogicError) exception occurs.
    """
    data = MagicMock()
    base_service.validate_update = AsyncMock(return_value=None)
    base_service.pre_update = AsyncMock(return_value=data)
    # Simulate repository.update raising a generic Exception.
    mock_repository.update.side_effect = Exception("Update failed")
    with pytest.raises(Exception, match="Update failed"):
        await base_service.update(id=1, data=data)


@pytest.mark.asyncio
async def test_update_hooks_called(base_service, mock_repository):
    """
    Test that pre_update and post_update hooks are called during update.
    """
    data = MagicMock()
    modified_data = MagicMock()
    base_service.validate_update = AsyncMock(return_value=None)
    base_service.pre_update = AsyncMock(return_value=modified_data)
    post_update_called = False

    async def post_update(record):
        nonlocal post_update_called
        post_update_called = True

    base_service.post_update = post_update
    mock_record = MagicMock()
    mock_repository.update.return_value = mock_record

    result = await base_service.update(id=1, data=data)
    mock_repository.update.assert_called_once_with(id=1, schema=modified_data)
    assert post_update_called
    assert result == mock_record


@pytest.mark.asyncio
async def test_delete_success(base_service, mock_repository):
    """
    Test successful record deletion.

    Ensures that:
    - The repository delete method is called with the correct ID.
    - The method returns True on successful deletion.
    """
    result = await base_service.delete(1)

    assert result is True
    mock_repository.delete.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_delete_non_existent(base_service, mock_repository):
    """
    Test deleting a non-existent record.

    Ensures that:
    - The service handles deletion of non-existent records gracefully.
    """
    mock_repository.delete.return_value = False

    result = await base_service.delete(999)

    assert result is False
    mock_repository.delete.assert_called_once_with(999)


@pytest.mark.asyncio
async def test_delete_with_validation_exception(base_service):
    """
    Test validation exception during record deletion.

    Ensures that:
    - BusinessLogicError is raised and transformed into ValidationException.
    - The repository delete method is never called.
    """

    async def mock_validate(id):
        raise BusinessLogicError("Cannot delete this record")

    base_service.validate_delete = mock_validate

    with pytest.raises(
        ValidationException, match="Cannot delete this record"
    ):  # ✅ Expect ValidationException
        await base_service.delete(1)


@pytest.mark.asyncio
async def test_delete_generic_exception(base_service, mock_repository):
    """
    Test the delete method when repository.delete raises a generic exception.
    The exception should be caught and wrapped in a ServiceException.
    """
    mock_repository.delete.side_effect = Exception("Delete failed")
    with pytest.raises(ServiceException, match="Failed to delete"):
        await base_service.delete(1)


@pytest.mark.asyncio
async def test_delete_hooks_called(base_service, mock_repository):
    """
    Test that pre_delete and post_delete hooks are called during delete.
    """
    base_service.validate_delete = AsyncMock(return_value=None)
    pre_delete_called = False

    async def pre_delete(id):
        nonlocal pre_delete_called
        pre_delete_called = True

    base_service.pre_delete = pre_delete
    post_delete_called = False

    async def post_delete(id):
        nonlocal post_delete_called
        post_delete_called = True

    base_service.post_delete = post_delete
    mock_repository.delete.return_value = True

    result = await base_service.delete(1)
    assert result is True
    assert pre_delete_called
    assert post_delete_called


@pytest.mark.asyncio
async def test_properties_and_logger_binding(dummy_model, mock_repository):
    """
    Test that the BaseService __init__ properly binds the logger and that
    the repository and db properties return the expected objects.
    """
    # Setup: assign a dummy db to the repository
    dummy_db = MagicMock()
    mock_repository.db = dummy_db

    service = BaseService(dummy_model, mock_repository)

    # Verify the repository property
    assert service.repository is mock_repository

    # Verify the db property
    assert service.db is dummy_db

    # Verify that the logger is bound with a service name (using the model's __name__)
    # (We simply check that the _logger attribute is set.)
    assert service._logger is not None
    # Optionally, if your logger supports accessing its context:
    # assert service._logger._context.get("service") == dummy_model.__name__


@pytest.mark.asyncio
async def test_create_with_model_dump(dummy_model, mock_repository):
    """
    Test the create method when pre_create returns an object that implements
    a model_dump() method. This verifies that the info log for "creating_record"
    and "record_created" is executed.
    """

    # Create a dummy processed_data object with a model_dump method.
    class DummyData:
        def model_dump(self, exclude=None):
            return {"data": "value", "exclude": exclude}

    dummy_processed = DummyData()
    dummy_record = MagicMock()
    dummy_record.id = 42

    service = BaseService(dummy_model, mock_repository)
    service.validate_create = AsyncMock(return_value=None)
    service.pre_create = AsyncMock(return_value=dummy_processed)
    service.post_create = AsyncMock(return_value=None)
    # Replace logger.info with a MagicMock so we can inspect calls.
    service._logger.info = MagicMock()
    mock_repository.create = AsyncMock(return_value=dummy_record)

    result = await service.create("dummy input")

    # Verify that repository.create was called with the processed_data object.
    mock_repository.create.assert_called_once_with(dummy_processed)

    # Verify that the "creating_record" log call includes the output of model_dump.
    service._logger.info.assert_any_call(
        "creating_record",
        model=dummy_model.__name__,
        data=dummy_processed.model_dump(
            exclude=({"password"} if hasattr(dummy_processed, "password") else None)
        ),
    )
    # Verify that the "record_created" log call contains the record id.
    service._logger.info.assert_any_call(
        "record_created",
        model=dummy_model.__name__,
        record_id=dummy_record.id,
    )
    assert result == dummy_record


@pytest.mark.asyncio
async def test_update_returns_none_does_not_call_post_update(
    dummy_model, mock_repository
):
    """
    Test that if repository.update returns None, the update method returns None
    and post_update is not called.
    """
    service = BaseService(dummy_model, mock_repository)
    service.validate_update = AsyncMock(return_value=None)
    service.pre_update = AsyncMock(return_value="processed_data")
    # Set repository.update to return None.
    mock_repository.update = AsyncMock(return_value=None)

    post_update_called = False

    async def fake_post_update(record):
        nonlocal post_update_called
        post_update_called = True

    service.post_update = fake_post_update

    result = await service.update(id=1, data="input_data")
    assert result is None
    assert post_update_called is False


@pytest.mark.asyncio
async def test_delete_result_false_no_post_delete_called(dummy_model, mock_repository):
    """
    Test that when repository.delete returns False, pre_delete is still called
    but post_delete is not called.
    """
    service = BaseService(dummy_model, mock_repository)
    service.validate_delete = AsyncMock(return_value=None)

    pre_delete_called = False

    async def fake_pre_delete(id):
        nonlocal pre_delete_called
        pre_delete_called = True

    service.pre_delete = fake_pre_delete

    post_delete_called = False

    async def fake_post_delete(id):
        nonlocal post_delete_called
        post_delete_called = True

    service.post_delete = fake_post_delete

    mock_repository.delete = AsyncMock(return_value=False)
    result = await service.delete(1)
    assert result is False
    assert pre_delete_called is True
    assert post_delete_called is False


@pytest.mark.asyncio
async def test_delete_result_true_calls_post_delete(dummy_model, mock_repository):
    """
    Test that when repository.delete returns True, both pre_delete and post_delete
    are called and the result is returned.
    """
    service = BaseService(dummy_model, mock_repository)
    service.validate_delete = AsyncMock(return_value=None)

    pre_delete_called = False

    async def fake_pre_delete(id):
        nonlocal pre_delete_called
        pre_delete_called = True

    service.pre_delete = fake_pre_delete

    post_delete_called = False

    async def fake_post_delete(id):
        nonlocal post_delete_called
        post_delete_called = True

    service.post_delete = fake_post_delete

    mock_repository.delete = AsyncMock(return_value=True)
    result = await service.delete(1)
    assert result is True
    assert pre_delete_called is True
    assert post_delete_called is True
