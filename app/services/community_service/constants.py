"""
Constants module for community service operations.

This module defines constants used throughout the community service layer,
including membership limits, role hierarchies, privacy transition rules, and
restricted community names.

Attributes:
    - MAX_MEMBERS_FREE (int): Maximum members allowed for free communities.
    - MAX_MEMBERS_PREMIUM (int): Maximum members allowed for premium communities.
    - MAX_COMMUNITIES_FREE (int): Maximum number of communities a free-tier user can create.
    - MAX_COMMUNITIES_PREMIUM (int): Maximum number of communities a premium user can create.
    - MAX_RELATIONSHIPS (int): Maximum number of related communities per community.
    - MAX_PENDING_INVITES (int): Maximum number of pending invitations per community.
    - RESTRICTED_NAMES (set): Set of restricted community names that cannot be used.
    - ROLE_HIERARCHY (dict): Dictionary defining role hierarchy and permitted assignments.
    - PRIVACY_TRANSITION_RULES (dict): Allowed transitions between privacy levels.
"""

from enum import Enum
from app.db.models.community_model import PrivacyLevel

# Maximum members allowed per community type
MAX_MEMBERS_FREE = 50
MAX_MEMBERS_PREMIUM = 500

MAX_COMMUNITIES_FREE = 5  # Adjust this limit based on your business rules
MAX_COMMUNITIES_PREMIUM = 20  # Adjust this limit for premium users

# Relationship and invitation limits
MAX_RELATIONSHIPS = 10
MAX_PENDING_INVITES = 100

# Restricted community names to prevent misuse
RESTRICTED_NAMES = {
    "admin",
    "moderator",
    "official",
    "banned",
    "restricted",
    "community_admin",
    "system",
    "support",
    "test",
}


class MemberRole(str, Enum):
    """
    Enumeration of possible community member roles.
    """

    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"
    PENDING = "pending"


# Role hierarchy defining permissible role assignments
ROLE_HIERARCHY = {
    MemberRole.OWNER: {MemberRole.ADMIN, MemberRole.MODERATOR, MemberRole.MEMBER},
    MemberRole.ADMIN: {MemberRole.MODERATOR, MemberRole.MEMBER},
    MemberRole.MODERATOR: {MemberRole.MEMBER},
    MemberRole.MEMBER: set(),
}

# Allowed privacy transitions for communities
PRIVACY_TRANSITION_RULES = {
    PrivacyLevel.PUBLIC: {PrivacyLevel.PRIVATE, PrivacyLevel.INVITATION_ONLY},
    PrivacyLevel.PRIVATE: {PrivacyLevel.PUBLIC, PrivacyLevel.INVITATION_ONLY},
    PrivacyLevel.INVITATION_ONLY: {PrivacyLevel.PRIVATE},
}
