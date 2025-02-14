"""
Community Repository Actions Module.

This module provides the CommunityActionsMixin class which encapsulates
all write operations for community data access. It includes methods for
adding, removing, and updating community members and member counts.

Key Methods:
  - add_member
  - remove_member
  - update_member_role
  - update_member_count

Usage Example:
    from app.db.repositories.community_repository.actions import CommunityActionsMixin

    class MyCommunityRepository(CommunityActionsMixin, BaseRepository):
         pass

Dependencies:
    - SQLAlchemy for transaction management
    - app.db.models.community_member_model.CommunityMember (membership model)
    - Custom error: IntegrityError
"""

from typing import Dict
from sqlalchemy import func, case, select
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.community_member_model import CommunityMember
from app.db.errors import IntegrityError


class CommunityActionsMixin:
    """
    Mixin class for community write operations.
    """

    async def add_member(
        self,
        community_id: int,
        user_id: int,
        role: str,
        assigned_by: int = None,
    ) -> CommunityMember:
        """
        Add a new member to a community.

        Args:
            community_id (int): Community ID.
            user_id (int): User ID.
            role (str): Member role.
            assigned_by (Optional[int]): ID of user assigning the role.

        Returns:
            CommunityMember: Created membership record.

        Raises:
            IntegrityError: If creation fails.
        """
        try:
            member = CommunityMember(
                community_id=community_id,
                user_id=user_id,
                role=role,
                role_assigned_by=assigned_by,
                is_active=True,
            )
            self.db.add(member)
            await self.db.commit()
            await self.db.refresh(member)
            return member
        except SQLAlchemyError as e:
            await self.db.rollback()
            self._logger.error(
                "add_member_failed",
                community_id=community_id,
                user_id=user_id,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to add community member",
                details={
                    "community_id": community_id,
                    "user_id": user_id,
                    "error": str(e),
                },
            ) from e

    async def remove_member(self, community_id: int, user_id: int) -> bool:
        """
        Remove a member from a community.

        Args:
            community_id (int): Community ID.
            user_id (int): User ID.

        Returns:
            bool: True if member was removed, False otherwise.

        Raises:
            IntegrityError: If removal fails.
        """
        try:
            stmt = (
                CommunityMember.__table__.update()
                .where(
                    (CommunityMember.community_id == community_id)
                    & (CommunityMember.user_id == user_id)
                )
                .values(is_active=False)
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await self.db.rollback()
            self._logger.error(
                "remove_member_failed",
                community_id=community_id,
                user_id=user_id,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to remove community member",
                details={
                    "community_id": community_id,
                    "user_id": user_id,
                    "error": str(e),
                },
            ) from e

    async def update_member_role(
        self,
        community_id: int,
        user_id: int,
        new_role: str,
        assigned_by: int = None,
    ) -> bool:
        """
        Update a member's role.

        Args:
            community_id (int): Community ID.
            user_id (int): User ID.
            new_role (str): New role to assign.
            assigned_by (Optional[int]): ID of user making the change.

        Returns:
            bool: True if role was updated, False otherwise.

        Raises:
            IntegrityError: If update fails.
        """
        try:
            stmt = (
                CommunityMember.__table__.update()
                .where(
                    (CommunityMember.community_id == community_id)
                    & (CommunityMember.user_id == user_id)
                    & (CommunityMember.is_active.is_(True))
                )
                .values(
                    role=new_role,
                    role_assigned_by=assigned_by,
                    role_assigned_at=func.now(),
                )
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await self.db.rollback()
            self._logger.error(
                "update_member_role_failed",
                community_id=community_id,
                user_id=user_id,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to update member role",
                details={
                    "community_id": community_id,
                    "user_id": user_id,
                    "error": str(e),
                },
            ) from e

    async def update_member_count(self, community_id: int) -> Dict[str, int]:
        """
        Update and return the member counts for a community.

        Args:
            community_id (int): Community ID.

        Returns:
            Dict[str, int]: Updated member counts.

        Raises:
            IntegrityError: If update fails.
        """
        try:
            stats_query = select(
                func.count(CommunityMember.user_id).label("total_count"),
                func.sum(case((CommunityMember.is_active.is_(True), 1), else_=0)).label(
                    "active_count"
                ),
            ).where(CommunityMember.community_id == community_id)
            result = await self.db.execute(stats_query)
            counts = result.one()

            stmt = (
                self._model.__table__.update()
                .where(self._model.id == community_id)
                .values(
                    total_count=counts.total_count or 0,
                    active_count=counts.active_count or 0,
                )
            )
            await self.db.execute(stmt)
            await self.db.commit()

            return {
                "total_count": counts.total_count or 0,
                "active_count": counts.active_count or 0,
            }
        except SQLAlchemyError as e:
            await self.db.rollback()
            self._logger.error(
                "update_member_count_failed",
                community_id=community_id,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to update member counts",
                details={"community_id": community_id, "error": str(e)},
            ) from e
