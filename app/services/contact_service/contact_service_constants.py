"""
Contact Service Constants Module.

This module defines constants used in the contact service, including limits and
restricted words for validation and business rules.

Key Components:
- Defines maximum allowed contacts, services, and categories per user.
- Lists restricted words for contact names.
- Specifies required fields for contact creation.

Typical usage example:
    from app.services.contact_service_constants import MAX_CONTACTS_FREE
    if user_contacts_count >= MAX_CONTACTS_FREE:
        raise BusinessRuleViolationError("User has reached maximum contacts limit.")
"""

# Maximum number of contacts a free user can have
MAX_CONTACTS_FREE = 10

# Maximum number of services a contact can be associated with
MAX_SERVICES = 20

# Maximum number of categories a contact can be assigned to
MAX_CATEGORIES = 5

# Restricted words that cannot be used in contact names
RESTRICTED_WORDS = {"admin", "system", "support", "test"}

# Required fields for contact creation
REQUIRED_FIELDS = {
    "contact_name",
    "primary_contact_first_name",
    "primary_contact_last_name",
    "email",
}
