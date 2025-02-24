"""
Database models initialization module.

This module serves as the central point of access for all database models in the
application. It provides organized imports of model classes while preventing
circular dependencies. The module ensures proper initialization order and
maintains a clean interface for accessing models throughout the application.

The module also exports common database components like the Base class and
custom types, making them easily accessible to other parts of the application.
"""

from app.db.database_engine import Base
from app.db.database_types import TZDateTime
from app.db.models.user_model import User
from app.db.models.role_model import Role
from app.db.models.community_model import Community, PrivacyLevel
from app.db.models.community_member_model import CommunityMember
from app.db.models.category_model import Category
from app.db.models.service_model import Service
from app.db.models.contact_model import Contact
from app.db.models.contact_endorsement_model import ContactEndorsement

# Version information
__version__ = "1.0.0"

# Export all models and related components
__all__ = [
    # Base classes and types
    "Base",
    "TZDateTime",
    # Models
    "User",
    "Role",
    "Community",
    "CommunityMember",
    "Category",
    "Service",
    "Contact",
    "ContactEndorsement",
    # Enums and Constants
    "PrivacyLevel",
]

# Model dependencies for reference
model_dependencies = {
    "User": ["Role", "Community", "Contact", "ContactEndorsement"],
    "Role": ["User"],
    "Community": ["User", "Contact", "ContactEndorsement"],
    "Category": ["Contact", "Service"],
    "Service": ["Category", "Contact"],
    "Contact": ["User", "Community", "Category", "Service", "ContactEndorsement"],
    "ContactEndorsement": ["User", "Community", "Contact"],
}


def get_model_class(model_name: str) -> type:
    """
    Get a model class by its name.

    This function provides a way to dynamically access model classes,
    which can be useful for generic operations or dynamic model handling.

    Args:
        model_name: Name of the model class to retrieve

    Returns:
        The requested model class

    Raises:
        ValueError: If the model name is not recognized
    """
    models = {
        "User": User,
        "Role": Role,
        "Community": Community,
        "Category": Category,
        "Service": Service,
        "Contact": Contact,
        "ContactEndorsement": ContactEndorsement,
    }

    if model_name not in models:
        raise ValueError(f"Unknown model: {model_name}")

    return models[model_name]
