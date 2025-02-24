# Neighbour Approved API Design Document

## 1. Overview

This document outlines an API design for the Neighbour Approved application, following an **XP (Extreme Programming)** approach with a strong emphasis on early and continuous testing. The API exposes endpoints for managing users, communities, contacts (service providers), endorsements, categories, and roles/permissions (if applicable). Key objectives include:

- **Rapid Iterations & TDD**: Fast implementation cycles with extensive automated tests.
- **Security**: Strict authentication, authorization checks, and compliance with best practices.
- **Performance**: Efficient data access and caching for scalability.
- **Maintainability**: Well-defined service layer and repository pattern, along with consistent documentation.

## 2. Architectural Approach

1. **Layered Architecture**  
   - **API Layer**: FastAPI routes handle HTTP requests, request/response serialization, and basic validations.
   - **Service Layer**: Centralizes business logic. API handlers call service methods rather than directly manipulating data.
   - **Repository Layer**: Manages database operations (CRUD). Each repository focuses on a single entity (e.g., User, Community).
   - **Domain Models**: SQLAlchemy models for persistence; Pydantic schemas for request/response validation.

2. **Design Patterns**  
   - **Service Layer Pattern**: Organizes business rules and domain workflows in dedicated services.
   - **Repository Pattern**: Clearly separates data-access concerns.
   - **Possibility** of using **Factory/Builder** patterns for complex object creation and **Observer** for events or notifications.

3. **Security**  
   - **JWT** (or OAuth2) for authentication; roles/permissions enforced by the service layer or endpoint dependencies.
   - **Data Validation** at the API boundary (Pydantic) and in the service layer (custom checks).
   - **Encryption & Best Practices**: Secure password hashing, HTTPS, and limited data exposure in responses.

4. **Performance**  
   - **FastAPI** for asynchronous I/O and high concurrency.
   - **Caching** frequently accessed entities (e.g., using Redis).
   - **Bulk Operations** to reduce overhead when updating or creating multiple records.

5. **Testing (XP & TDD)**  
   - **Unit Tests** targeting the service layer (business logic).
   - **Integration Tests** validating repository/database interactions.
   - **E2E Tests** covering API endpoints and user flows.
   - **CI/CD** pipeline to run tests on every commit, ensuring fast feedback loops.

## 3. Endpoint Specification

Listed below are proposed endpoints. The **order** (1, 2, 3…) indicates a suggested build sequence to maintain a working API early while expanding functionality over time.

### 3.1 Authentication & User Management

1. **POST** `/auth/login`  
   - **Description**: User login with email/password. Returns JWT.
   - **Order**: *Build first* (secure everything else).

2. **POST** `/auth/refresh`  
   - **Description**: Refresh a valid but expiring JWT.
   - **Order**: *Next step*.

3. **POST** `/users`  
   - **Description**: Create (register) a new user.
   - **Order**: *Essential for new accounts*.

4. **GET** `/users/{user_id}`  
   - **Description**: Retrieve user details.
   - **Order**: Following user creation.

5. **PATCH** `/users/{user_id}`  
   - **Description**: Update user info (profile, email verified, etc.).
   - **Order**: Next iteration.

6. **DELETE** `/users/{user_id}`  
   - **Description**: Deactivate or remove a user.
   - **Order**: Built once core user flows are stable.

### 3.2 Community Management

1. **POST** `/communities`  
   - **Description**: Create a new community (public, private, or invitation-only).

2. **GET** `/communities/{community_id}`  
   - **Description**: Retrieve community details.

3. **PATCH** `/communities/{community_id}`  
   - **Description**: Update community data (name, privacy, etc.).

4. **DELETE** `/communities/{community_id}`  
    - **Description**: Remove/close a community.

#### Membership

1. **POST** `/communities/{community_id}/members`  
    - **Description**: Add a user to the community.

2. **DELETE** `/communities/{community_id}/members/{user_id}`  
    - **Description**: Remove a user from the community.

3. **GET** `/communities/{community_id}/members`  
    - **Description**: List community members, possibly with roles.

### 3.3 Contact (Service Provider) Management

1. **POST** `/contacts`  
    - **Description**: Create a new contact record.

2. **GET** `/contacts/{contact_id}`  
    - **Description**: Retrieve a single contact’s details.

3. **PATCH** `/contacts/{contact_id}`  
    - **Description**: Update contact info.

4. **DELETE** `/contacts/{contact_id}`  
    - **Description**: Remove a contact from the system.

### 3.4 Endorsements

1. **POST** `/contacts/{contact_id}/endorsements`  
    - **Description**: Endorse a contact (rating, comment).

2. **GET** `/contacts/{contact_id}/endorsements`  
    - **Description**: List all endorsements for a contact.

3. **GET** `/endorsements/{endorsement_id}`  
    - **Description**: Fetch a specific endorsement.

4. **PATCH** `/endorsements/{endorsement_id}`  
    - **Description**: Update an endorsement’s rating/comment.

5. **DELETE** `/endorsements/{endorsement_id}`  
    - **Description**: Remove an endorsement.

### 3.5 Category Management

1. **POST** `/categories`  
    - **Description**: Create a new category (e.g., "Plumbing").

2. **GET** `/categories/{category_id}`  
    - **Description**: Retrieve category details.

3. **PATCH** `/categories/{category_id}`  
    - **Description**: Update a category.

4. **DELETE** `/categories/{category_id}`  
    - **Description**: Remove a category.

### 3.6 Role & Permission Management (Optional)

1. **POST** `/roles`  
    - **Description**: Create a role.

2. **GET** `/roles/{role_id}`  
    - **Description**: Retrieve role details.

3. **PATCH** `/roles/{role_id}`  
    - **Description**: Update role permissions.

4. **DELETE** `/roles/{role_id}`  
    - **Description**: Delete a role.

#### Assigning/Removing Roles

1. **POST** `/users/{user_id}/roles/{role_id}`  
    - **Description**: Assign a role to a user.

2. **DELETE** `/users/{user_id}/roles/{role_id}`  
    - **Description**: Remove a role from a user.

### 3.7 Health & Monitoring

- **GET** `/health`  
  - **Description**: A basic health check endpoint.

## 4. Order of Implementation & Testing

1. **Auth & Basic User Flows**: Build the login/registration process first.  
2. **Communities & Membership**: Create and manage communities.  
3. **Contacts & Endorsements**: Introduce service providers and endorsements.  
4. **Categories**: Categorize contacts.  
5. **Roles & Permissions**: If you need RBAC, handle it once core flows work.  
6. **Full End-to-End Tests**: Validate entire user stories (e.g., user logs in, endorses a contact, etc.).  
7. **Performance & Security Testing**: Use load testing tools (Locust/JMeter) and security scans (OWASP ZAP).

## 5. XP & TDD Notes

- **Pair Programming** on each feature.  
- **User Stories** guide each endpoint’s creation.  
- **Test-Driven**: Write tests first, then the minimal implementation to pass them.  
- **Continuous Refactoring**: Clean up code once tests pass.  
- **Frequent Commits & CI**: Continuous integration runs the test suite on every commit.

## 6. Documentation & Docstrings

- Follow the best practices from the docstring guidelines:
  - Module docstrings: Summaries, usage examples, dependencies.
  - Method docstrings: Parameters, returns, exceptions.
- **API Docs** auto-generated by FastAPI under `/docs` or `/redoc`.
- Ensure docstrings remain up to date with each iteration.

## 7. Conclusion

By following this API design under an XP methodology:

1. **Develop endpoints in minimal increments** with robust tests.  
2. **Validate** changes immediately through TDD and CI.  
3. **Refactor** for clarity, performance, and security as new features emerge.  
4. **Document** thoroughly, ensuring docstrings and generated docs reflect reality.  

This approach ensures a **secure**, **performant**, and **maintainable** API that evolves naturally with your business needs.
