# Modern Python Documentation Guide: Docstrings and Comments

## Overview

This document outlines modern best practices for writing documentation in Python code, focusing on docstrings and comments. These guidelines align with PEP 257 (Docstring Conventions) while incorporating contemporary patterns used in professional software engineering.

## Docstrings

### Module Docstrings

Module docstrings appear at the beginning of a file and describe the module's purpose and contents. They should include:

1. A brief description of the module's purpose
2. Key classes and functions contained within
3. Usage examples if appropriate
4. Any important dependencies or prerequisites
5. Version information if relevant

Example:
```python
"""
User authentication module for the Neighbour Approved application.

This module handles all aspects of user authentication, including password
verification, token management, and session handling. It provides a secure
authentication framework that integrates with the application's user model.

Key components:
- AuthenticationManager: Core class handling authentication logic
- TokenService: Handles JWT token generation and validation
- PasswordHasher: Manages secure password hashing

Typical usage example:
    auth_manager = AuthenticationManager()
    user = await auth_manager.authenticate_user("user@example.com", "password")
    token = await auth_manager.generate_token(user)

Dependencies:
    - PyJWT >=2.0.0
    - passlib >=1.7.4
"""
```

### Class Docstrings

Class docstrings describe a class's purpose, behavior, and attributes. They should include:

1. Class purpose and behavior
2. Key attributes
3. Important methods
4. Usage examples
5. Any base classes or interfaces implemented
6. Type parameters for generic classes

Example:
```python
class UserRepository:
    """
    Repository for managing user data in the database.

    This class implements the repository pattern for user-related operations,
    providing a clean interface for creating, retrieving, updating, and
    deleting user records. It includes comprehensive error handling and
    ensures transactional integrity for all operations.

    Attributes:
        db_session: Database session for executing queries
        logger: Structured logger instance
        cache_manager: Optional cache manager for query optimization

    Key Methods:
        create_user: Creates a new user record
        get_by_email: Retrieves a user by email
        update_user: Updates user information
        delete_user: Removes a user record

    Typical usage example:
        repository = UserRepository(db_session)
        user = await repository.create_user(user_data)
        await repository.update_user(user.id, update_data)
    """
```

### Method Docstrings

Method docstrings should describe what a method does, its parameters, return values, and any exceptions it may raise. They should include:

1. Clear description of the method's purpose
2. Parameters and their types
3. Return value and type
4. Exceptions that may be raised
5. Examples if the usage isn't obvious
6. Any important notes or warnings

Example:
```python
async def create_user(self, data: UserCreate) -> User:
    """
    Create a new user record in the database.

    This method validates the input data, checks for existing users with
    the same email, and creates a new user record. It handles password
    hashing and sets up any required default values.

    Args:
        data: UserCreate schema containing validated user data
            - email: User's email address
            - password: Plain text password
            - first_name: User's first name
            - last_name: User's last name

    Returns:
        User: Newly created user instance

    Raises:
        DuplicateRecordError: If a user with the same email exists
        ValidationError: If the provided data is invalid
        DatabaseError: If the database operation fails

    Example:
        user_data = UserCreate(
            email="user@example.com",
            password="secure_password",
            first_name="John",
            last_name="Doe"
        )
        user = await repository.create_user(user_data)

    Note:
        This method automatically hashes the password before storage.
        The original password is never stored in the database.
    """
```

### Property Docstrings

Property docstrings should be concise but clear about what the property represents:

Example:
```python
@property
def full_name(self) -> str:
    """
    User's full name, combining first and last names.

    Returns:
        str: Formatted full name in the format "First Last"
    """
    return f"{self.first_name} {self.last_name}"
```

## Comments

### Code Comments

While docstrings document the public interface, comments explain implementation details. They should be used to:

1. Explain complex algorithms or logic
2. Clarify non-obvious decisions
3. Mark important sections of code
4. Document temporary solutions or workarounds

Example:
```python
def calculate_rating_statistics(self, ratings: List[int]) -> Dict[str, float]:
    # Filter out invalid ratings (outside 1-5 range)
    valid_ratings = [r for r in ratings if 1 <= r <= 5]
    
    # Early return if no valid ratings
    if not valid_ratings:
        return {"average": 0.0, "median": 0.0}
    
    # Calculate statistics
    average = sum(valid_ratings) / len(valid_ratings)
    
    # Sort for median calculation
    # Using sorted() instead of .sort() to avoid modifying original list
    sorted_ratings = sorted(valid_ratings)
    
    # Handle even/odd number of ratings differently for median
    mid = len(sorted_ratings) // 2
    if len(sorted_ratings) % 2 == 0:
        median = (sorted_ratings[mid - 1] + sorted_ratings[mid]) / 2
    else:
        median = sorted_ratings[mid]
    
    return {
        "average": round(average, 2),
        "median": round(median, 2)
    }
```

### TODO Comments

Use TODO comments to mark pending work or future improvements:

```python
# TODO: Implement caching for frequently accessed users
# TODO(jsmith): Add validation for phone numbers
# TODO(issue-123): Fix race condition in concurrent updates
```

## Best Practices

### General Guidelines

1. Write documentation for the reader, not the writer
2. Keep docstrings and comments up to date with code changes
3. Use clear, concise language
4. Follow consistent formatting within a project
5. Document why rather than what (the code shows what)

### Documentation Don'ts

1. Don't repeat the code in comments
2. Avoid obvious comments that add no value
3. Don't leave outdated comments or docstrings
4. Avoid commenting out code (use version control)
5. Don't write excessive documentation for private methods

### Type Hints and Docstrings

When using type hints, docstrings should still include type information for clarity and documentation generation:

```python
def get_user_by_id(self, user_id: int) -> Optional[User]:
    """
    Retrieve a user by their unique identifier.

    Args:
        user_id: User's unique identifier

    Returns:
        User instance if found, None otherwise
    """
```

### Documentation Tools

Modern Python projects often use documentation tools that work with docstrings:

1. Sphinx: Comprehensive documentation generator
2. MkDocs: Markdown-based documentation generator
3. pydoc: Built-in Python documentation generator
4. doctest: Testing through documentation examples

Configure these tools to maintain consistent documentation standards across the project.

## Conclusion

Effective documentation through docstrings and comments is crucial for maintaining and scaling Python applications. Following these guidelines ensures that documentation remains valuable and maintainable throughout a project's lifecycle. Remember that documentation is a form of communication with future developers (including yourself), so clarity and accuracy should be prioritized over verbosity.