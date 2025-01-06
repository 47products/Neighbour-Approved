"""
Example implementations of transaction management in the Neighbour Approved application.

This module demonstrates proper usage of transaction management patterns for
various database operations. It serves as a reference for implementing
transactions throughout the application.
"""

from typing import List, Optional
from fastapi import logger
from sqlalchemy.orm import Session
from app.db.models.user import User
from app.db.models.community import Community
from app.db.models.contact import Contact
from app.core.transaction import (
    transactional,
    async_transactional,
    TransactionManager,
    NestedTransactionManager,
)


class UserService:
    """Example service demonstrating transaction management patterns."""

    @transactional
    def create_user_with_contacts(
        self, db: Session, user_data: dict, contacts_data: List[dict]
    ) -> User:
        """
        Create a user with multiple contacts in a single transaction.

        This example demonstrates a basic transaction that ensures both the user
        and their contacts are created atomically.
        """
        # Create user
        user = User.create(user_data)
        db.add(user)
        db.flush()  # Flush to get the user ID

        # Create contacts
        for contact_data in contacts_data:
            contact_data["user_id"] = user.id
            contact = Contact.create(contact_data)
            db.add(contact)

        return user

    @async_transactional
    async def create_community_with_members(
        self, db: Session, community_data: dict, member_ids: List[int]
    ) -> Community:
        """
        Create a community and add members in a single transaction.

        This example demonstrates an async transaction with multiple operations
        that must succeed or fail together.
        """
        # Create community
        community = Community.create(community_data)
        db.add(community)
        db.flush()

        # Add members
        for user_id in member_ids:
            user = db.query(User).get(user_id)
            if user:
                community.add_member(user)

        return community

    def transfer_contacts(
        self, db: Session, from_user_id: int, to_user_id: int, contact_ids: List[int]
    ) -> None:
        """
        Transfer contacts between users using nested transactions.

        This example demonstrates using nested transactions to handle complex
        operations that may need partial rollback capabilities.
        """
        transaction_manager = TransactionManager(db)
        nested_manager = NestedTransactionManager(db)

        with transaction_manager.transaction() as session:
            from_user = session.query(User).get(from_user_id)
            to_user = session.query(User).get(to_user_id)

            if not from_user or not to_user:
                raise ValueError("Invalid user IDs")

            for contact_id in contact_ids:
                with nested_manager.nested_transaction():
                    contact = session.query(Contact).get(contact_id)
                    if contact and contact.user_id == from_user_id:
                        contact.user_id = to_user_id
                    else:
                        # This will rollback just this contact's transaction
                        raise ValueError(f"Invalid contact transfer: {contact_id}")

    def bulk_update_contacts(self, db: Session, updates: List[dict]) -> None:
        """
        Update multiple contacts with transaction savepoints.

        This example shows how to handle bulk operations where some operations
        might fail without affecting others.
        """
        transaction_manager = TransactionManager(db)
        nested_manager = NestedTransactionManager(db)

        with transaction_manager.transaction() as session:
            for update in updates:
                try:
                    with nested_manager.nested_transaction():
                        contact = session.query(Contact).get(update.get("id"))
                        if contact:
                            for key, value in update.items():
                                if key != "id":
                                    setattr(contact, key, value)
                        else:
                            raise ValueError(f"Contact not found: {update.get('id')}")
                except Exception as e:
                    # Log the error but continue with other updates
                    logger.error(
                        "contact_update_failed",
                        contact_id=update.get("id"),
                        error=str(e),
                    )
                    continue
