"""
Community Repository Queries Module.

This module provides the CommunityQueriesMixin class which encapsulates
all read-only operations for community data access. It includes methods to:
  - Retrieve a community by name
  - Retrieve a community with its relationships
  - Get a member's role and list members by role
  - Get communities a user belongs to
  - Get related communities
  - Search communities by name or description
  - Get pending membership requests
  - Get community member statistics

Usage Example:
    from app.db.repositories.community_repository.queries import CommunityQueriesMixin

    class MyCommunityRepository(CommunityQueriesMixin, BaseRepository):
         pass

Dependencies:
    - SQLAlchemy for query execution and error handling
    - Models: Community, CommunityMember, User, PrivacyLevel
    - Custom error: QueryError
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import select, and_, or_, func, case
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.community_model import Community, PrivacyLevel
from app.db.models.user_model import User
from app.db.models.community_member_model import CommunityMember
from app.db.errors import QueryError


class CommunityQueriesMixin:
    """
    Mixin class for community query operations.
    """

    async def get_by_name(self, name: str) -> Optional[Community]:
        """
        Retrieve a community by its name.

        Args:
            name (str): Community name.

        Returns:
            Optional[Community]: Community if found, None otherwise.

        Raises:
            QueryError: If database query fails.
        """
        try:
            query = select(self._model).where(self._model.name == name)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self._logger.error("get_by_name_failed", name=name, error=str(e))
            raise QueryError(
                message="Failed to retrieve community by name",
                details={"name": name, "error": str(e)},
            ) from e

    async def get_with_relationships(self, community_id: int) -> Optional[Community]:
        """
        Retrieve a community with its relationships loaded.

        Args:
            community_id (int): Community ID.

        Returns:
            Optional[Community]: Community with relationships if found.

        Raises:
            QueryError: If database query fails.
        """
        try:
            query = (
                select(self._model)
                .where(self._model.id == community_id)
                .options(
                    selectinload(self._model.members),
                    selectinload(self._model.contacts),
                    selectinload(self._model.related_communities),
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self._logger.error(
                "get_with_relationships_failed", community_id=community_id, error=str(e)
            )
            raise QueryError(
                message="Failed to retrieve community with relationships",
                details={"community_id": community_id, "error": str(e)},
            ) from e

    async def get_member_role(self, community_id: int, user_id: int) -> Optional[str]:
        """
        Get a user's role in a community.

        Args:
            community_id (int): Community ID.
            user_id (int): User ID.

        Returns:
            Optional[str]: Role name if member exists.

        Raises:
            QueryError: If database query fails.
        """
        try:
            query = select(CommunityMember.role).where(
                and_(
                    CommunityMember.community_id == community_id,
                    CommunityMember.user_id == user_id,
                    CommunityMember.is_active.is_(True),
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self._logger.error(
                "get_member_role_failed",
                community_id=community_id,
                user_id=user_id,
                error=str(e),
            )
            raise QueryError(
                message="Failed to retrieve member role",
                details={
                    "community_id": community_id,
                    "user_id": user_id,
                    "error": str(e),
                },
            ) from e

    async def get_members_by_role(self, community_id: int, role: str) -> List[User]:
        """
        Get all community members with a specific role.

        Args:
            community_id (int): Community ID.
            role (str): Role to filter by.

        Returns:
            List[User]: List of users with the role.

        Raises:
            QueryError: If database query fails.
        """
        try:
            query = (
                select(User)
                .join(CommunityMember)
                .where(
                    and_(
                        CommunityMember.community_id == community_id,
                        CommunityMember.role == role,
                        CommunityMember.is_active.is_(True),
                    )
                )
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self._logger.error(
                "get_members_by_role_failed",
                community_id=community_id,
                role=role,
                error=str(e),
            )
            raise QueryError(
                message="Failed to retrieve members by role",
                details={"community_id": community_id, "role": role, "error": str(e)},
            ) from e

    async def get_user_communities(
        self,
        user_id: int,
        *,
        active_only: bool = True,
        privacy_level: Optional[PrivacyLevel] = None,
    ) -> List[Community]:
        """
        Get all communities a user is a member of.

        Args:
            user_id (int): User ID.
            active_only (bool): Whether to include only active communities.
            privacy_level (Optional[PrivacyLevel]): Optional privacy level filter.

        Returns:
            List[Community]: List of communities.

        Raises:
            QueryError: If database query fails.
        """
        try:
            conditions = [CommunityMember.user_id == user_id]
            if active_only:
                conditions.extend(
                    [
                        self._model.is_active.is_(True),
                        CommunityMember.is_active.is_(True),
                    ]
                )
            if privacy_level:
                conditions.append(self._model.privacy_level == privacy_level)
            query = (
                select(self._model)
                .join(CommunityMember)
                .where(and_(*conditions))
                .order_by(self._model.name)
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self._logger.error(
                "get_user_communities_failed", user_id=user_id, error=str(e)
            )
            raise QueryError(
                message="Failed to retrieve user communities",
                details={"user_id": user_id, "error": str(e)},
            ) from e

    async def get_related_communities(
        self, community_id: int, active_only: bool = True
    ) -> List[Community]:
        """
        Get communities related to a specific community.

        Args:
            community_id (int): Community ID.
            active_only (bool): Whether to include only active communities.

        Returns:
            List[Community]: List of related communities.

        Raises:
            QueryError: If database query fails.
        """
        try:
            query = (
                select(self._model)
                .join(self._model.related_communities)
                .where(self._model.id == community_id)
            )
            if active_only:
                query = query.where(self._model.is_active.is_(True))
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self._logger.error(
                "get_related_communities_failed",
                community_id=community_id,
                error=str(e),
            )
            raise QueryError(
                message="Failed to retrieve related communities",
                details={"community_id": community_id, "error": str(e)},
            ) from e

    async def search_communities(
        self,
        search_term: str,
        *,
        skip: int = 0,
        limit: int = 100,
        privacy_level: Optional[PrivacyLevel] = None,
        active_only: bool = True,
    ) -> List[Community]:
        """
        Search communities by name or description.

        Args:
            search_term (str): Search term.
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.
            privacy_level (Optional[PrivacyLevel]): Optional privacy level filter.
            active_only (bool): Whether to include only active communities.

        Returns:
            List[Community]: List of matching communities.

        Raises:
            QueryError: If query fails.
        """
        try:
            conditions = [
                or_(
                    self._model.name.ilike(f"%{search_term}%"),
                    self._model.description.ilike(f"%{search_term}%"),
                )
            ]
            if privacy_level:
                conditions.append(self._model.privacy_level == privacy_level)
            if active_only:
                conditions.append(self._model.is_active.is_(True))
            query = (
                select(self._model)
                .where(and_(*conditions))
                .offset(skip)
                .limit(limit)
                .order_by(self._model.name)
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self._logger.error(
                "search_communities_failed", search_term=search_term, error=str(e)
            )
            raise QueryError(
                message="Failed to search communities",
                details={"search_term": search_term, "error": str(e)},
            ) from e

    async def get_pending_members(
        self, community_id: int
    ) -> List[Tuple[User, datetime]]:
        """
        Get pending membership requests for a community.

        Args:
            community_id (int): Community ID.

        Returns:
            List[Tuple[User, datetime]]: List of users and their request dates.

        Raises:
            QueryError: If query fails.
        """
        try:
            query = (
                select(User, CommunityMember.joined_at)
                .join(CommunityMember)
                .where(
                    and_(
                        CommunityMember.community_id == community_id,
                        CommunityMember.is_active.is_(False),
                    )
                )
                .order_by(CommunityMember.joined_at.desc())
            )
            result = await self.db.execute(query)
            return list(result.all())
        except SQLAlchemyError as e:
            self._logger.error(
                "get_pending_members_failed", community_id=community_id, error=str(e)
            )
            raise QueryError(
                message="Failed to retrieve pending members",
                details={"community_id": community_id, "error": str(e)},
            ) from e

    async def get_member_stats(self, community_id: int) -> Dict[str, int]:
        """
        Get member statistics for a community.

        Args:
            community_id (int): Community ID.

        Returns:
            Dict[str, int]: Dictionary of member statistics.

        Raises:
            QueryError: If query fails.
        """
        try:
            stats_query = select(
                func.count(CommunityMember.user_id).label("total_members"),
                func.sum(case((CommunityMember.is_active.is_(True), 1), else_=0)).label(
                    "active_members"
                ),
            ).where(CommunityMember.community_id == community_id)
            result = await self.db.execute(stats_query)
            row = result.one()
            return {
                "total_members": row.total_members or 0,
                "active_members": row.active_members or 0,
            }
        except SQLAlchemyError as e:
            self._logger.error(
                "get_member_stats_failed", community_id=community_id, error=str(e)
            )
            raise QueryError(
                message="Failed to retrieve member statistics",
                details={"community_id": community_id, "error": str(e)},
            ) from e
