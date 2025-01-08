"""
Example implementations of logging patterns in the Neighbour Approved application.

This module demonstrates proper usage of the logging infrastructure across
different scenarios and requirements. It serves as a reference for implementing
logging throughout the application.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models.user import User
from app.db.models.community import Community
from app.core.transaction import transactional


class UserActivityLogger:
    """Example service demonstrating logging patterns."""

    def __init__(self):
        self.logger = get_logger(__name__)

    @transactional
    def create_user_with_logging(
        self, db: Session, user_data: Dict[str, Any], request_id: str
    ) -> User:
        """
        Create a user with comprehensive logging.

        This example demonstrates proper logging patterns including context
        binding, error handling, and audit logging.
        """
        # Bind context for all logs in this operation
        self.logger.bind_context(request_id=request_id, operation="user_creation")

        try:
            # Log the start of the operation
            self.logger.info("user_creation_started", email=user_data.get("email"))

            # Create the user
            user = User.create(user_data)
            db.add(user)
            db.flush()

            # Audit log the successful creation
            self.logger.audit("user_created", user_id=user.id, email=user.email)

            # Log successful completion
            self.logger.info("user_creation_completed", user_id=user.id)

            return user

        except Exception as e:
            # Log the error with full context
            self.logger.error("user_creation_failed", error=e, user_data=user_data)
            raise
        finally:
            # Clear the context for future operations
            self.logger.clear_context()

    def process_community_invitation(
        self, db: Session, community_id: int, user_id: int, invitation_id: str
    ) -> None:
        """
        Process a community invitation with detailed logging.

        This example shows logging patterns for a multi-step process
        with potential failure points.
        """
        self.logger.bind_context(
            invitation_id=invitation_id, community_id=community_id, user_id=user_id
        )

        try:
            # Log the start of processing
            self.logger.info("invitation_processing_started")

            # Validate community
            community = db.query(Community).get(community_id)
            if not community:
                self.logger.warning("invitation_community_not_found", status="failed")
                raise HTTPException(status_code=404, detail="Community not found")

            # Validate user
            user = db.query(User).get(user_id)
            if not user:
                self.logger.warning("invitation_user_not_found", status="failed")
                raise HTTPException(status_code=404, detail="User not found")

            # Check if already a member
            if community.is_member(user):
                self.logger.debug("user_already_member", status="skipped")
                return

            # Add user to community
            community.add_member(user)
            db.commit()

            # Audit log the membership addition
            self.logger.audit(
                "community_member_added",
                user_id=user_id,
                community_id=community_id,
                added_by="invitation",
            )

            # Log successful completion
            self.logger.info("invitation_processing_completed", status="success")

        except Exception as e:
            # Log the error
            self.logger.error("invitation_processing_failed", error=e, status="failed")
            raise
        finally:
            self.logger.clear_context()

    def monitor_user_activity(
        self,
        user_id: int,
        activity_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Monitor and log user activity.

        This example demonstrates logging patterns for user activity
        monitoring and analytics.
        """
        self.logger.bind_context(user_id=user_id, activity_type=activity_type)

        try:
            # Log the activity
            self.logger.info("user_activity", metadata=metadata or {})

            # For specific high-value activities, create audit logs
            if activity_type in {"login", "password_change", "profile_update"}:
                self.logger.audit(
                    f"user_{activity_type}", user_id=user_id, metadata=metadata
                )

            # Log specific metrics for monitoring
            if metadata and "performance_metrics" in metadata:
                self.logger.debug(
                    "activity_performance_metrics",
                    metrics=metadata["performance_metrics"],
                )

        except Exception as e:
            self.logger.error("activity_monitoring_failed", error=e)
            raise
        finally:
            self.logger.clear_context()
