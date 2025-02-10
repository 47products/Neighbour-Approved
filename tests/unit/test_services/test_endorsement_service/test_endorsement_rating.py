"""
Unit tests for the RatingMixin in the Endorsement Service Rating Module.

This module tests the functionality of the RatingMixin, including:
    - Calculation of weighted ratings via calculate_weighted_rating.
    - Recalculation of contact ratings via recalculate_contact_ratings.
    - Helper methods such as:
        * _calculate_seasonal_factor
        * _calculate_verification_impact
        * _get_community_trust_factor
        * _get_endorser_activity_factor

Usage:
    Run these tests using pytest.
Dependencies:
    - pytest
    - pytest-asyncio
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from app.services.endorsement_service.endorsement_rating import RatingMixin
from app.services.notification_service import NotificationType
from app.services.service_exceptions import StateError
from app.db.models.contact_model import Contact
from app.db.models.community_model import Community

# ------------------------------------------------------------------------------
# Dummy Contact and DummyDB Definitions (Persistent Instances)
# ------------------------------------------------------------------------------


class DummyContact:
    """
    Dummy Contact class for testing recalculate_contact_ratings.

    Attributes:
        id (int): The unique identifier of the contact.
        user_id (int): The user ID associated with the contact.
        average_rating (float or None): The contact's average rating.
    """

    def __init__(self, id: int, user_id: int):
        self.id = id
        self.user_id = user_id
        self.average_rating = None


class DummyDB:
    """
    Dummy database class for testing recalculate_contact_ratings.

    This implementation stores contacts so that modifications persist across calls.

    Attributes:
        committed (bool): Indicates if commit() was called.
        contacts (dict): A mapping of contact IDs to DummyContact instances.
    """

    def __init__(self):
        self.committed = False
        self.contacts = {}  # Cache contacts by id

    async def get(self, model, id):
        """
        Simulate retrieving a Contact by id.

        If the contact does not already exist in the cache, create and store it.
        """
        if model.__name__ == "Contact":
            if id not in self.contacts:
                self.contacts[id] = DummyContact(id=id, user_id=30)
            return self.contacts[id]
        return None

    async def commit(self):
        """
        Simulate committing a transaction.
        """
        self.committed = True


# ------------------------------------------------------------------------------
# Other Dummy Classes for Testing
# ------------------------------------------------------------------------------


class DummyContactForRating:
    """
    Dummy contact class for testing rating calculations.

    Attributes:
        categories (list): A list of categories associated with the contact.
        user_id (int): The unique user identifier.
    """

    def __init__(self, categories=None, user_id: int = 20):
        self.categories = categories if categories is not None else []
        self.user_id = user_id


class DummyEndorsementForRating:
    """
    Dummy endorsement class for testing rating calculations.

    This dummy object is a plain Python object with the attributes required for
    rating calculations and does not inherit from any SQLAlchemy model to avoid
    instrumentation issues (e.g. missing _sa_instance_state).

    Args:
        rating (float): The base rating on a 1.0 to 5.0 scale.
        created_at (datetime): The creation timestamp.
        user_id (int): The identifier of the endorser.
        community_id (int): The identifier of the community.
        is_verified (bool): Whether the endorsement is verified.
        verification_notes (str): Any verification notes.
        contact (DummyContactForRating): The contact receiving the endorsement.
    """

    def __init__(
        self,
        rating,
        created_at,
        user_id,
        community_id,
        is_verified,
        verification_notes,
        contact: DummyContactForRating,
    ):
        self.rating = rating
        self.created_at = created_at
        self.user_id = user_id
        self.community_id = community_id
        self.is_verified = is_verified
        self.verification_notes = verification_notes
        self.contact = contact


class DummyRatingMixin(RatingMixin):
    """
    Dummy subclass of RatingMixin that overrides external dependencies to produce
    deterministic results for testing.

    This class provides dummy implementations for:
        - _get_endorser_statistics
        - _calculate_reputation_score
        - _calculate_expertise_weight
        - _get_community_trust_factor (overridden below)
    """

    def __init__(self):
        # For calculate_weighted_rating tests we do not require db, repository, or notification service.
        self.db = None
        self.repository = None
        self._notification_service = None

    async def _get_endorser_statistics(self, user_id: int) -> dict:
        """Return dummy endorser statistics."""
        return {"dummy": True}

    def _calculate_reputation_score(self, stats: dict) -> float:
        """Return a fixed reputation score."""
        return 1.2

    async def _calculate_expertise_weight(self, user_id: int, categories) -> float:
        """Return a fixed expertise weight."""
        return 1.0

    async def _get_community_trust_factor(self, community_id: int) -> float:
        """Return a fixed community trust factor."""
        return 1.1


# Dummy classes for testing recalculate_contact_ratings


class DummyRepo:
    """
    Dummy repository for retrieving contact endorsements.

    This version returns two endorsements, both with a base rating of 4.0,
    so that the overridden calculate_weighted_rating returns 4.0 for each.
    """

    async def get_contact_endorsements(self, contact_id: int):
        contact = DummyContactForRating(categories=[])
        endorsement1 = DummyEndorsementForRating(
            rating=4.0,  # Both endorsements now have 4.0
            created_at=datetime.now(timezone.utc) - timedelta(days=10),
            user_id=10,
            community_id=1,
            is_verified=True,
            verification_notes="",
            contact=contact,
        )
        endorsement2 = DummyEndorsementForRating(
            rating=4.0,  # Changed from 5.0 to 4.0
            created_at=datetime.now(timezone.utc) - timedelta(days=20),
            user_id=10,
            community_id=1,
            is_verified=True,
            verification_notes="",
            contact=contact,
        )
        return [endorsement1, endorsement2]


class DummyRepoEmpty:
    """
    Dummy repository that returns no endorsements.
    """

    async def get_contact_endorsements(self, contact_id: int):
        return []


class DummyDBNoContact:
    """
    Dummy database that always returns None for Contact.
    """

    async def get(self, model, id):
        return None


# Subclass of DummyRatingMixin for recalculate_contact_ratings tests
class DummyRatingMixinForRecalc(DummyRatingMixin):
    """
    Dummy subclass that overrides calculate_weighted_rating to return a fixed value.
    """

    async def calculate_weighted_rating(
        self, endorsement: DummyEndorsementForRating
    ) -> float:
        return 4.0


class DummyRepoForActivity:
    """
    Dummy repository for testing _get_endorser_activity_factor.
    """

    async def get_user_activity_stats(self, user_id: int) -> dict:
        return {"monthly_endorsements": 5, "verification_success_rate": 0.8}


# ------------------------------------------------------------------------------
# Tests for calculate_weighted_rating and Helper Methods
# ------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_calculate_weighted_rating_saturates_to_5():
    """
    Test that calculate_weighted_rating clamps the value to a maximum of 5.0.

    This test simulates an endorsement where the raw weighted rating exceeds 5.0.
    To achieve this, we set the endorsement's created_at to the current time so that
    the age is zero and the time decay factor is 1.0. With the dummy factors defined,
    the computed rating will be above 5.0 and should then be clamped to 5.0.
    """
    mixin = DummyRatingMixin()
    # Set created_at to now so that age_days is zero (time_factor = 1.0).
    created_at = datetime.now(timezone.utc)
    contact = DummyContactForRating(categories=[])
    # Create an endorsement with base rating 4.0 and a verification note that adds weight.
    endorsement = DummyEndorsementForRating(
        rating=4.0,
        created_at=created_at,
        user_id=10,
        community_id=100,
        is_verified=True,
        verification_notes="verified_identity",  # Expected to add 0.1 extra weight
        contact=contact,
    )
    # Force the seasonal factor to 1.0.
    mixin._calculate_seasonal_factor = AsyncMock(return_value=1.0)
    rating = await mixin.calculate_weighted_rating(endorsement)
    # The raw computed rating should exceed 5.0 and be clamped to 5.0.
    assert rating == pytest.approx(5.0)


@pytest.mark.asyncio
async def test_calculate_weighted_rating_floors_to_1():
    """
    Test that calculate_weighted_rating enforces a minimum rating of 1.0.

    Even if the base rating is 0 or very low, the returned value should be at least 1.0.
    """
    mixin = DummyRatingMixin()
    created_at = datetime(2023, 2, 1, tzinfo=timezone.utc)
    contact = DummyContactForRating(categories=[])
    endorsement = DummyEndorsementForRating(
        rating=0.0,  # Zero base rating
        created_at=created_at,
        user_id=10,
        community_id=100,
        is_verified=False,
        verification_notes="",
        contact=contact,
    )
    mixin._calculate_seasonal_factor = AsyncMock(return_value=1.0)
    rating = await mixin.calculate_weighted_rating(endorsement)
    # The minimum rating should be clamped to 1.0.
    assert rating == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_calculate_weighted_rating_normal_range():
    """
    Test that calculate_weighted_rating returns the computed rating when it is within the allowed range.

    This test simulates an endorsement where the calculated weighted rating is between 1.0 and 5.0.
    All multiplicative factors are overridden to 1.0 so that the weighted rating equals the base rating,
    and no clamping occurs.

    Expected computation:
        base_rating = 3.0
        time_factor = 1.0 (since created_at is now)
        reputation_score = 1.0
        community_factor = 1.0
        expertise_weight = 1.0
        verification_factor = 1.0
        weighted_rating = 3.0 * 1.0 * 1.0 * 1.0 * 1.0 * 1.0 = 3.0
    """
    mixin = DummyRatingMixin()
    # Override all factors to return 1.0.
    mixin._calculate_seasonal_factor = AsyncMock(return_value=1.0)
    mixin._get_community_trust_factor = AsyncMock(return_value=1.0)
    mixin._calculate_expertise_weight = AsyncMock(return_value=1.0)
    mixin._get_endorser_statistics = AsyncMock(return_value={"dummy": True})
    mixin._calculate_reputation_score = lambda stats: 1.0
    # Override the verification impact so that it returns 1.0.
    # (Assume that for an unverified endorsement with no verification notes the base factor is 1.0.)
    mixin._calculate_verification_impact = lambda endorsement: 1.0

    # Set created_at to now so that age_days is zero and time_factor is 1.0.
    created_at = datetime.now(timezone.utc)
    contact = DummyContactForRating(categories=[])
    endorsement = DummyEndorsementForRating(
        rating=3.0,
        created_at=created_at,
        user_id=10,
        community_id=100,
        is_verified=False,
        verification_notes="",
        contact=contact,
    )
    rating = await mixin.calculate_weighted_rating(endorsement)
    # Verify that the computed weighted rating is 3.0 (i.e. no clamping is applied).
    assert rating == pytest.approx(3.0)


@pytest.mark.asyncio
async def test_calculate_seasonal_factor_for_january_and_may():
    """
    Test _calculate_seasonal_factor returns correct factors for different months.

    January should yield a factor of 1.2 (per the seasonal_weights mapping),
    whereas May (an unspecified month) should default to 1.0.
    """
    mixin = DummyRatingMixin()
    dt_jan = datetime(2023, 1, 15, tzinfo=timezone.utc)
    factor_jan = await mixin._calculate_seasonal_factor(dt_jan)
    assert factor_jan == pytest.approx(1.2)

    dt_may = datetime(2023, 5, 15, tzinfo=timezone.utc)
    factor_may = await mixin._calculate_seasonal_factor(dt_may)
    assert factor_may == pytest.approx(1.0)


def test_calculate_verification_impact_verified_no_notes():
    """
    Test _calculate_verification_impact returns the base factor for a verified endorsement without notes.

    For a verified endorsement without additional verification notes, the impact should be 1.2.
    """
    mixin = DummyRatingMixin()
    contact = DummyContactForRating(categories=[])
    endorsement = DummyEndorsementForRating(
        rating=4.0,
        created_at=datetime.now(timezone.utc),
        user_id=10,
        community_id=100,
        is_verified=True,
        verification_notes="",
        contact=contact,
    )
    impact = mixin._calculate_verification_impact(endorsement)
    assert impact == pytest.approx(1.2)


def test_calculate_verification_impact_not_verified():
    """
    Test _calculate_verification_impact returns 1.0 for an unverified endorsement.

    When the endorsement is not verified, no bonus is applied.
    """
    mixin = DummyRatingMixin()
    contact = DummyContactForRating(categories=[])
    endorsement = DummyEndorsementForRating(
        rating=4.0,
        created_at=datetime.now(timezone.utc),
        user_id=10,
        community_id=100,
        is_verified=False,
        verification_notes="",
        contact=contact,
    )
    impact = mixin._calculate_verification_impact(endorsement)
    assert impact == pytest.approx(1.0)


def test_calculate_verification_impact_with_notes():
    """
    Test _calculate_verification_impact properly sums additional weights from verification notes.

    For a verified endorsement with specific keywords, the additional weight should be added.
    """
    mixin = DummyRatingMixin()
    contact = DummyContactForRating(categories=[])
    endorsement = DummyEndorsementForRating(
        rating=4.0,
        created_at=datetime.now(timezone.utc),
        user_id=10,
        community_id=100,
        is_verified=True,
        verification_notes="Confirmed_transaction and documented_evidence",
        contact=contact,
    )
    # Expected: base factor 1.2 + 0.15 (for confirmed_transaction) + 0.2 (for documented_evidence) = 1.55
    impact = mixin._calculate_verification_impact(endorsement)
    assert abs(impact - 1.55) < 0.001


class DummyDBForCommunity:
    """
    Dummy database for testing _get_community_trust_factor.
    """

    async def get(self, model, id):
        if model.__name__ == "Community" and id == 1:
            dummy = MagicMock(spec=Community)
            dummy.verified_endorsements_count = 5
            dummy.total_endorsements = 10
            return dummy
        return None


@pytest.mark.asyncio
async def test_get_community_trust_factor_found_and_not_found():
    """
    Test _get_community_trust_factor returns the correct factor when a community is found or not.

    For a community with id=1, the factor is computed based on the ratio of verified endorsements.
    For a non-existent community, the factor should default to 1.0.
    """
    mixin = DummyRatingMixin()
    mixin.db = DummyDBForCommunity()
    # Override _get_community_trust_factor to use the actual base implementation.
    mixin._get_community_trust_factor = RatingMixin._get_community_trust_factor.__get__(
        mixin
    )

    # For community id=1: verified_ratio = 5/10 = 0.5, so expected factor = min(1.3, 0.8 + 0.5) = 1.3.
    factor_found = await mixin._get_community_trust_factor(1)
    assert factor_found == pytest.approx(1.3)

    # For a non-existent community, the factor should default to 1.0.
    factor_not_found = await mixin._get_community_trust_factor(999)
    assert factor_not_found == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_get_endorser_activity_factor():
    """
    Test _get_endorser_activity_factor returns the correct factor based on user activity.

    The dummy repository returns stats that lead to an activity factor of 1.2.
    """
    mixin = DummyRatingMixin()

    # Provide a dummy repository with a get_user_activity_stats method.
    class DummyRepoForActivity:
        async def get_user_activity_stats(self, user_id: int) -> dict:
            return {"monthly_endorsements": 5, "verification_success_rate": 0.8}

    mixin.repository = DummyRepoForActivity()
    factor = await mixin._get_endorser_activity_factor(10)
    assert factor == pytest.approx(1.2)


# ------------------------------------------------------------------------------
# Tests for recalculate_contact_ratings
# ------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recalculate_contact_ratings_success():
    """
    Test that recalculate_contact_ratings updates the contact's average rating,
    commits the transaction, and sends a notification when endorsements exist.
    """
    mixin = DummyRatingMixinForRecalc()
    mixin.db = DummyDB()  # DummyDB returns a persistent DummyContact instance
    mixin.repository = DummyRepo()  # Now returns two endorsements with rating 4.0
    # Set up a dummy notification service.
    mixin._notification_service = MagicMock()
    mixin._notification_service.send_notification = AsyncMock()

    contact_id = 1
    await mixin.recalculate_contact_ratings(contact_id)
    # Retrieve the persistent dummy contact.
    contact = await mixin.db.get(Contact, contact_id)
    # Two endorsements, each with a weighted rating of 4.0, yield an average of 4.0.
    assert contact.average_rating == pytest.approx(4.0)
    # Verify that commit was called.
    assert mixin.db.committed is True
    # Verify that a notification was sent with the correct data.
    mixin._notification_service.send_notification.assert_called_once()
    args, _ = mixin._notification_service.send_notification.call_args
    assert args[0] == NotificationType.RATING_UPDATED
    assert args[1] == contact.user_id
    data = args[2]
    assert data["contact_id"] == contact.id
    assert data["new_rating"] == contact.average_rating
    assert data["total_ratings"] == 2


@pytest.mark.asyncio
async def test_recalculate_contact_ratings_no_endorsements():
    """
    Test that recalculate_contact_ratings does not update the contact or send a notification
    when there are no endorsements.
    """
    mixin = DummyRatingMixinForRecalc()
    mixin.db = DummyDB()
    mixin.repository = DummyRepoEmpty()
    mixin._notification_service = MagicMock()
    mixin._notification_service.send_notification = AsyncMock()

    contact_id = 1
    await mixin.recalculate_contact_ratings(contact_id)
    contact = await mixin.db.get(Contact, contact_id)
    # With no endorsements, the average rating remains unchanged (None).
    assert contact.average_rating is None
    # Commit should not be called.
    assert mixin.db.committed is False
    mixin._notification_service.send_notification.assert_not_called()


@pytest.mark.asyncio
async def test_recalculate_contact_ratings_contact_not_found():
    """
    Test that recalculate_contact_ratings raises a StateError when the contact is not found.
    """
    mixin = DummyRatingMixinForRecalc()
    mixin.db = DummyDBNoContact()
    mixin.repository = DummyRepo()
    with pytest.raises(StateError):
        await mixin.recalculate_contact_ratings(999)
