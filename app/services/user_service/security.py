"""
Security Service Module.

This module provides the SecurityService class, responsible for managing
password hashing and verification processes to ensure secure user authentication.

Classes:
    SecurityService: Handles password hashing and verification.
"""

import bcrypt
import structlog
from typing import Dict

from app.services.service_exceptions import ValidationError


class SecurityService:
    """Service for managing password security operations.

    This service handles password-related security operations including hashing,
    verification, and strength validation. It implements secure password policies
    and maintains consistent security practices.

    Methods:
        hash_password: Hashes a plaintext password using bcrypt.
        verify_password: Verifies a plaintext password against a stored hash.
        _validate_password_strength: Validates password against security policies.
    """

    # Password policy constants
    MIN_LENGTH = 8
    SPECIAL_CHARS = "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~"

    def __init__(self):
        """Initialize the security service."""
        self._logger = structlog.get_logger(__name__)

    def hash_password(self, password: str) -> str:
        """Hash a plaintext password using bcrypt.

        This method validates the password strength and generates a secure
        hash using bcrypt with a random salt.

        Args:
            password: The plaintext password to hash

        Returns:
            The bcrypt hash of the password

        Raises:
            ValidationError: If password doesn't meet security requirements

        Example:
            hashed = security_service.hash_password("SecureP@ssw0rd")
        """
        try:
            validation_result = self._validate_password_strength(password)
            if not validation_result["valid"]:
                raise ValidationError(
                    "Password does not meet security requirements",
                    details=validation_result["failures"],
                )

            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode(), salt)

            self._logger.debug("password_hashed_successfully")
            return hashed.decode()

        except ValidationError:
            raise

        except Exception as e:
            self._logger.error(
                "password_hashing_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ValueError("Password hashing failed") from e

    def verify_password(self, stored_hash: str, password: str) -> bool:
        """Verify a plaintext password against a stored hash.

        Args:
            stored_hash: The bcrypt hash to check against
            password: The plaintext password to verify

        Returns:
            True if the password matches the hash, False otherwise

        Example:
            matches = security_service.verify_password(stored_hash, "SecureP@ssw0rd")
        """
        try:
            matches = bcrypt.checkpw(password.encode(), stored_hash.encode())

            self._logger.debug(
                "password_verification_completed",
                matches=matches,
            )
            return matches

        except Exception as e:
            self._logger.error(
                "password_verification_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    def _validate_password_strength(self, password: str) -> Dict[str, any]:
        """Validate password strength against security policies.

        This method checks the password against multiple security criteria:
        - Minimum length (8 characters)
        - Contains uppercase letters
        - Contains lowercase letters
        - Contains numbers
        - Contains special characters

        Args:
            password: The password to validate

        Returns:
            Dictionary containing validation result and any failures:
            {
                "valid": bool,
                "failures": List[str]
            }

        Example:
            result = security_service._validate_password_strength("SecureP@ssw0rd")
            if result["valid"]:
                print("Password meets requirements")
            else:
                print("Failures:", result["failures"])
        """
        failures = []

        if len(password) < self.MIN_LENGTH:
            failures.append(f"Password must be at least {self.MIN_LENGTH} characters")

        if not any(char.isupper() for char in password):
            failures.append("Password must contain at least one uppercase letter")

        if not any(char.islower() for char in password):
            failures.append("Password must contain at least one lowercase letter")

        if not any(char.isdigit() for char in password):
            failures.append("Password must contain at least one number")

        if not any(char in self.SPECIAL_CHARS for char in password):
            failures.append("Password must contain at least one special character")

        return {
            "valid": len(failures) == 0,
            "failures": failures,
        }
