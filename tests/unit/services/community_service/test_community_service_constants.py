"""
Unit tests for `constants.py` in the community service module.

This module ensures that all constants in `constants.py` are properly defined and function as expected.

Tested Constants:
    - MAX_MEMBERS_FREE
    - MAX_MEMBERS_PREMIUM
    - MAX_RELATIONSHIPS
    - MAX_PENDING_INVITES
    - RESTRICTED_NAMES
    - MemberRole Enum
    - ROLE_HIERARCHY
    - PRIVACY_TRANSITION_RULES

Dependencies:
    - 
"""

from app.services.community_service.constants import (
    MAX_MEMBERS_FREE,
    MAX_MEMBERS_PREMIUM,
    MAX_RELATIONSHIPS,
    MAX_PENDING_INVITES,
    RESTRICTED_NAMES,
    MemberRole,
    ROLE_HIERARCHY,
    PRIVACY_TRANSITION_RULES,
)
from app.db.models.community_model import PrivacyLevel


def test_max_members_limits():
    """
    Ensure maximum members allowed for free and premium communities are correctly set.
    """
    assert MAX_MEMBERS_FREE == 50, "MAX_MEMBERS_FREE should be 50"
    assert MAX_MEMBERS_PREMIUM == 500, "MAX_MEMBERS_PREMIUM should be 500"


def test_max_relationships_limits():
    """
    Ensure maximum relationships and pending invites are correctly set.
    """
    assert MAX_RELATIONSHIPS == 10, "MAX_RELATIONSHIPS should be 10"
    assert MAX_PENDING_INVITES == 100, "MAX_PENDING_INVITES should be 100"


def test_restricted_names():
    """
    Ensure restricted names contain expected values.
    """
    restricted_names = {
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
    assert (
        RESTRICTED_NAMES == restricted_names
    ), "RESTRICTED_NAMES do not match expected values"

    # Ensure specific names are restricted
    assert "admin" in RESTRICTED_NAMES
    assert "system" in RESTRICTED_NAMES
    assert "support" in RESTRICTED_NAMES
    assert "test" in RESTRICTED_NAMES

    # Ensure an arbitrary name is NOT restricted
    assert "random" not in RESTRICTED_NAMES


def test_member_role_enum():
    """
    Ensure `MemberRole` Enum contains expected roles.
    """
    expected_roles = {"owner", "admin", "moderator", "member", "pending"}
    actual_roles = {role.value for role in MemberRole}

    assert (
        actual_roles == expected_roles
    ), "MemberRole enum values do not match expected values"


def test_role_hierarchy():
    """
    Ensure role hierarchy is correctly structured.
    """
    assert ROLE_HIERARCHY[MemberRole.OWNER] == {
        MemberRole.ADMIN,
        MemberRole.MODERATOR,
        MemberRole.MEMBER,
    }
    assert ROLE_HIERARCHY[MemberRole.ADMIN] == {MemberRole.MODERATOR, MemberRole.MEMBER}
    assert ROLE_HIERARCHY[MemberRole.MODERATOR] == {MemberRole.MEMBER}
    assert ROLE_HIERARCHY[MemberRole.MEMBER] == set()  # Members cannot assign roles


def test_privacy_transition_rules():
    """
    Ensure privacy transition rules are correctly structured.
    """
    assert PRIVACY_TRANSITION_RULES[PrivacyLevel.PUBLIC] == {
        PrivacyLevel.PRIVATE,
        PrivacyLevel.INVITATION_ONLY,
    }
    assert PRIVACY_TRANSITION_RULES[PrivacyLevel.PRIVATE] == {
        PrivacyLevel.PUBLIC,
        PrivacyLevel.INVITATION_ONLY,
    }
    assert PRIVACY_TRANSITION_RULES[PrivacyLevel.INVITATION_ONLY] == {
        PrivacyLevel.PRIVATE
    }
