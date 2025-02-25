"""
Unit tests for the Category model.

This module tests all aspects of the Category model, including:
- Object instantiation
- Relationship handling
- Hierarchical methods
- Instance methods
- Class methods
- Validation and sorting

The tests leverage shared fixtures for mock database sessions, repositories, and test data.

Typical usage example:
    pytest tests/unit/test_db/test_models/test_category_model.py
"""

import pytest
from unittest.mock import MagicMock
from app.db.models.category_model import Category, CategoryCreate


@pytest.fixture
def test_category():
    """
    Create a test Category instance.

    Returns:
        Category: A Category instance with test data.
    """
    return Category(
        id=1,
        name="Test Category",
        slug="test-category",
        parent=None,
        depth=0,
        path="test-category",
        sort_order=1,
        is_active=True,
    )


def test_category_creation(test_category):
    """
    Test that a Category object is correctly instantiated.

    Args:
        test_category (Category): A test category instance.
    """
    assert test_category.id == 1
    assert test_category.name == "Test Category"
    assert test_category.slug == "test-category"
    assert test_category.parent is None
    assert test_category.depth == 0
    assert test_category.path == "test-category"
    assert test_category.sort_order == 1
    assert test_category.is_active is True


def test_category_create():
    """
    Test that the create class method correctly instantiates a Category from CategoryCreate.

    This test ensures that data is correctly mapped from the DTO to the Category model.
    """
    category_data = CategoryCreate(
        name="New Category",
        slug="new-category",
        description="A new test category",
        parent=None,
        sort_order=2,
    )
    new_category = Category.create(category_data)

    assert new_category.name == "New Category"
    assert new_category.slug == "new-category"
    assert new_category.description == "A new test category"
    assert new_category.sort_order == 2


def test_category_update_hierarchy_info(test_category):
    """
    Test that update_hierarchy_info correctly updates depth and path.
    """
    parent_category = MagicMock()
    parent_category.depth = 1
    parent_category.path = "parent-category"

    test_category.parent = parent_category
    test_category.update_hierarchy_info()

    assert test_category.depth == 2
    assert test_category.path == "parent-category/test-category"


def test_category_get_ancestors(test_category):
    """
    Test that get_ancestors correctly retrieves all ancestor categories.
    """
    grandparent = MagicMock()
    grandparent.parent = None
    grandparent.id = 10

    parent = MagicMock()
    parent.parent = grandparent
    parent.id = 5

    test_category.parent = parent

    ancestors = test_category.get_ancestors()

    assert len(ancestors) == 2
    assert ancestors[0].id == 10  # Grandparent
    assert ancestors[1].id == 5  # Parent


def test_category_get_descendants(test_category):
    """
    Test that get_descendants correctly retrieves all descendant categories.
    """
    child1 = MagicMock()
    child1.children = []

    child2 = MagicMock()
    child2.children = []

    test_category.children = [child1, child2]

    descendants = test_category.get_descendants()

    assert len(descendants) == 2
    assert child1 in descendants
    assert child2 in descendants


def test_category_is_ancestor_of():
    """
    Test that is_ancestor_of correctly determines ancestor relationship.
    """
    # Create a root category
    parent = Category(id=1, name="Parent", slug="parent")
    parent.depth = 0  # Ensure parent has depth
    parent.path = "parent"  # Manually set path

    # Create a child category with the correct parent reference
    child = Category(id=2, name="Child", slug="child", parent=parent)
    child.update_hierarchy_info()  # Ensure depth and path are updated

    # Ensure correct path formation
    assert child.path == "parent/child"
    assert child.depth == 1  # Should be 1 level deeper than parent

    # Check ancestor relationship
    assert parent.is_ancestor_of(child) is True
    assert (
        child.is_ancestor_of(parent) is False
    )  # Child should not be ancestor of parent

    # Ensure non-related category does not register as an ancestor
    unrelated = Category(id=3, name="Unrelated", slug="unrelated")
    unrelated.path = "unrelated"
    assert unrelated.is_ancestor_of(child) is False


def test_category_is_descendant_of():
    """
    Test that is_descendant_of correctly determines descendant relationship.
    """
    # Create a root category
    parent = Category(id=1, name="Parent", slug="parent")
    parent.depth = 0  # Ensure parent has depth
    parent.path = "parent"  # Manually set path

    # Create a child category with the correct parent reference
    child = Category(id=2, name="Child", slug="child", parent=parent)
    child.update_hierarchy_info()  # Ensure depth and path are updated

    # Ensure correct path formation
    assert child.path == "parent/child"
    assert child.depth == 1  # Should be 1 level deeper than parent

    # Check descendant relationship
    assert child.is_descendant_of(parent) is True
    assert (
        parent.is_descendant_of(child) is False
    )  # Parent should not be descendant of child

    # Ensure non-related category does not register as a descendant
    unrelated = Category(id=3, name="Unrelated", slug="unrelated")
    unrelated.path = "unrelated"
    assert child.is_descendant_of(unrelated) is False


def test_category_move_to_parent():
    """
    Test that move_to_parent correctly assigns a new parent.
    """
    new_parent = MagicMock()
    new_parent.is_descendant_of.return_value = False
    new_parent.depth = 1
    new_parent.path = "new-parent"

    category = Category(id=3, name="SubCategory", slug="subcategory")

    category.move_to_parent(new_parent)

    assert category.parent == new_parent
    assert category.depth == 2
    assert category.path == "new-parent/subcategory"


def test_category_move_to_parent_invalid():
    """
    Test that move_to_parent raises an error if trying to move a category into its own descendant.
    """
    # Create a root category
    parent = Category(id=1, name="Parent", slug="parent")
    parent.depth = 0  # Ensure parent has depth
    parent.path = "parent"  # Manually set path

    # Create a child category with the correct parent reference
    child = Category(id=2, name="Child", slug="child", parent=parent)
    child.update_hierarchy_info()  # Ensure depth and path are updated

    # Ensure valid hierarchy before moving
    assert child.path == "parent/child"
    assert child.depth == 1  # Child should be 1 level deeper than parent

    # Attempt to move parent under its child (invalid operation)
    with pytest.raises(
        ValueError, match="Cannot move category to one of its descendants"
    ):
        parent.move_to_parent(child)


def test_category_get_siblings():
    """
    Test that get_siblings correctly retrieves sibling categories.
    """
    # Create a parent category
    parent = Category(id=1, name="Parent", slug="parent")
    parent.depth = 0  # Ensure parent has depth
    parent.path = "parent"  # Manually set path

    # Create sibling categories under the same parent
    sibling1 = Category(id=2, name="Sibling1", slug="sibling1", parent=parent)
    sibling2 = Category(id=3, name="Sibling2", slug="sibling2", parent=parent)
    orphan = Category(id=4, name="Orphan", slug="orphan")  # No parent

    # Ensure parent has children set
    parent.children = [sibling1, sibling2]

    # Verify siblings
    assert sibling1.get_siblings() == [sibling2]
    assert sibling2.get_siblings() == [sibling1]

    # Orphan category should have no siblings
    assert orphan.get_siblings() == []


def test_category_get_root():
    """
    Test that get_root correctly retrieves the root category.
    """
    # Create a root category
    grandparent = Category(id=1, name="Grandparent", slug="grandparent")
    grandparent.depth = 0  # Ensure root depth is set
    grandparent.path = "grandparent"

    # Create a parent category linked to grandparent
    parent = Category(id=2, name="Parent", slug="parent", parent=grandparent)
    parent.update_hierarchy_info()

    # Create a child category linked to parent
    child = Category(id=3, name="Child", slug="child", parent=parent)
    child.update_hierarchy_info()

    # Ensure that all categories correctly reference the root
    assert child.get_root() == grandparent
    assert parent.get_root() == grandparent
    assert grandparent.get_root() == grandparent


def test_category_is_leaf():
    """
    Test that is_leaf correctly determines if a category has no children.
    """
    parent = Category(id=1, name="Parent", slug="parent")
    parent.depth = 0  # ✅ Ensure parent has depth

    child = Category(id=2, name="Child", slug="child", parent=parent)
    parent.children = [child]  # ✅ Ensure parent tracks child
    child.children = []  # ✅ Ensure child has no children

    assert child.is_leaf() is True
    assert parent.is_leaf() is False


def test_category_is_empty():
    """
    Test that is_empty correctly determines if a category has no contacts or services.
    """
    category = Category(id=1, name="Empty Category", slug="empty-category")

    # Ensure empty lists for contacts and services
    category.contacts = []
    category.services = []

    assert category.is_empty() is True

    # Add a contact, now it should not be empty
    mock_contact = MagicMock()
    category.contacts = [mock_contact]
    assert category.is_empty() is False

    # Reset contacts, add a service, it should still not be empty
    category.contacts = []
    mock_service = MagicMock()
    category.services = [mock_service]
    assert category.is_empty() is False

    # Ensure it's empty again
    category.services = []
    assert category.is_empty() is True


def test_category_get_active_services_count():
    """
    Test that get_active_services_count correctly counts active services.
    """
    # Create a test category
    category = Category(id=1, name="Test Category", slug="test-category")

    # Mock active and inactive services
    active_service = MagicMock()
    active_service.is_active = True

    inactive_service = MagicMock()
    inactive_service.is_active = False

    # Assign services to category
    category.services = [active_service, inactive_service]

    # Ensure only active services are counted
    assert category.get_active_services_count() == 1

    # Add another active service
    another_active_service = MagicMock()
    another_active_service.is_active = True
    category.services.append(another_active_service)

    # Ensure count updates correctly
    assert category.get_active_services_count() == 2


def test_category_get_sorted_children():
    """
    Test that get_sorted_children correctly sorts children.
    """
    # Create a parent category
    parent = Category(id=1, name="Parent", slug="parent")

    # Create child categories with different sort_order values
    child1 = Category(id=2, name="Child1", slug="child1", parent=parent, sort_order=2)
    child2 = Category(id=3, name="Child2", slug="child2", parent=parent, sort_order=1)
    child3 = Category(id=4, name="Child3", slug="child3", parent=parent, sort_order=3)

    # Assign children to parent
    parent.children = [child1, child2, child3]

    # Get sorted children
    sorted_children = parent.get_sorted_children()

    # Verify correct sorting by sort_order
    assert sorted_children == [child2, child1, child3]

    # Test sorting with active_only=True
    child1.is_active = True
    child2.is_active = False
    child3.is_active = True

    sorted_active_children = parent.get_sorted_children(active_only=True)

    # Should only return active children in the correct order
    assert sorted_active_children == [child1, child3]


def test_category_update_hierarchy_info():
    """
    Test that update_hierarchy_info correctly updates depth and path.
    """
    # Case 1: Root category (no parent)
    root = Category(id=1, name="Root", slug="root")
    root.update_hierarchy_info()

    assert root.depth == 0
    assert root.path == "root"

    # Case 2: Child category with a parent
    child = Category(id=2, name="Child", slug="child", parent=root)
    child.update_hierarchy_info()

    assert child.depth == 1  # Parent depth + 1
    assert child.path == "root/child"


def test_category_get_full_path_names():
    """
    Test that get_full_path_names correctly returns the category hierarchy.
    """
    # Create hierarchy: Grandparent -> Parent -> Child
    grandparent = Category(id=1, name="Grandparent", slug="grandparent")
    parent = Category(id=2, name="Parent", slug="parent", parent=grandparent)
    child = Category(id=3, name="Child", slug="child", parent=parent)

    # Update hierarchy info
    grandparent.update_hierarchy_info()
    parent.update_hierarchy_info()
    child.update_hierarchy_info()

    assert child.get_full_path_names() == ["Grandparent", "Parent", "Child"]
    assert parent.get_full_path_names() == ["Grandparent", "Parent"]
    assert grandparent.get_full_path_names() == ["Grandparent"]


def test_category_update_hierarchy_info():
    """
    Test that update_hierarchy_info correctly updates depth and path.
    """
    # Case 1: Root category (no parent)
    root = Category(id=1, name="Root", slug="root")
    root.update_hierarchy_info()

    assert root.depth == 0
    assert root.path == "root"

    # Case 2: Child category with a parent
    parent = Category(id=2, name="Parent", slug="parent", parent=root)
    parent.update_hierarchy_info()

    assert parent.depth == 1
    assert parent.path == "root/parent"

    # Case 3: Grandchild category
    child = Category(id=3, name="Child", slug="child", parent=parent)
    child.update_hierarchy_info()

    assert child.depth == 2
    assert child.path == "root/parent/child"


def test_category_get_hierarchy_level():
    """
    Test that get_hierarchy_level correctly determines the level in the hierarchy.
    """
    root = Category(id=1, name="Root", slug="root")
    parent = Category(id=2, name="Parent", slug="parent", parent=root)
    child = Category(id=3, name="Child", slug="child", parent=parent)

    assert root.get_hierarchy_level() == 0
    assert parent.get_hierarchy_level() == 1
    assert child.get_hierarchy_level() == 2


def test_category_reorder_children():
    """
    Test that reorder_children correctly updates children's sort_order.
    """
    parent = Category(id=1, name="Parent", slug="parent")

    # Create children with different sort orders
    child1 = Category(id=2, name="Child1", slug="child1", parent=parent, sort_order=1)
    child2 = Category(id=3, name="Child2", slug="child2", parent=parent, sort_order=2)
    child3 = Category(id=4, name="Child3", slug="child3", parent=parent, sort_order=3)

    # Assign children
    parent.children = [child1, child2, child3]

    # Define a new order
    new_order = [3, 4, 2]  # Order by ID

    # Reorder children
    parent.reorder_children(new_order)

    # Ensure correct order after sorting
    assert [child.id for child in parent.children] == [3, 4, 2]

    # Test invalid order (missing ID)
    with pytest.raises(
        ValueError, match="New order must contain exactly the current child IDs"
    ):
        parent.reorder_children([2, 3])  # Missing child ID 4


def test_category_repr(test_category):
    """
    Test that the __repr__ method correctly formats the string representation.

    Args:
        test_category (Category): A test category instance.
    """
    assert repr(test_category) == "Category(id=1, name=Test Category)"
