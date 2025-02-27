# Neighbour Approved API Design Document

## 1. Introduction

This document outlines the design and implementation plan for the Neighbour Approved application's REST API. The API will provide a comprehensive interface for managing users, communities, contacts, endorsements, and related resources, following modern API design principles and documentation standards.

### 1.1 Purpose

The Neighbour Approved API serves as the primary interface between the frontend application and the backend services. It enables users to create and manage community-based endorsements for service providers, facilitating trust and reputation within local communities.

### 1.2 Scope

This API design covers all core functionality of the Neighbour Approved application, including:

- User management and authentication
- Community creation and membership
- Contact management
- Endorsement creation and verification
- Service and category management
- Role-based access control

### 1.3 Design Principles

The API follows these key design principles:

- **RESTful Architecture**: Resource-oriented design with appropriate HTTP methods
- **Consistent Patterns**: Uniform resource naming and response structures
- **Comprehensive Documentation**: Detailed Sphinx-compatible docstrings for all endpoints
- **Proper Error Handling**: Standardized error responses with appropriate status codes
- **Versioning**: API versioning through URL paths to support future evolution
- **Security**: Robust authentication and authorization mechanisms

## 2. API Overview

### 2.1 Base URL

All API endpoints will be prefixed with:

```text
/api/v1/
```

### 2.2 Authentication

The API uses JWT-based authentication. Clients must include a valid JWT token in the Authorization header:

```text
Authorization: Bearer <token>
```

Tokens are obtained through the authentication endpoint:

```text
POST /api/v1/authentication/login
```

### 2.3 Response Format

All API responses follow a consistent JSON format:

```json
{
  "data": {
    // Resource data or collection
  },
  "meta": {
    "pagination": {
      "total": 100,
      "page": 1,
      "per_page": 20,
      "pages": 5
    }
  }
}
```

Error responses use a standard format:

```json
{
  "error_code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    // Optional additional error details
  }
}
```

## 3. Resource Endpoints

### 3.1 Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/authentication/login | Authenticate user and get access token |
| POST | /api/v1/authentication/refresh | Refresh access token |
| POST | /api/v1/authentication/logout | Invalidate token |

### 3.2 User Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/users | Create new user account |
| GET | /api/v1/users/{user_id} | Get user by ID |
| PUT | /api/v1/users/{user_id} | Update user information |
| DELETE | /api/v1/users/{user_id} | Delete user account |
| GET | /api/v1/users/{user_id}/communities | Get user's communities |
| GET | /api/v1/users/{user_id}/contacts | Get user's contacts |
| GET | /api/v1/users/{user_id}/endorsements | Get user's endorsements |
| POST | /api/v1/users/{user_id}/verify-email | Verify user's email |
| GET | /api/v1/users/me | Get current authenticated user |

### 3.3 Community Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/communities | Create new community |
| GET | /api/v1/communities | List communities |
| GET | /api/v1/communities/{community_id} | Get community by ID |
| PUT | /api/v1/communities/{community_id} | Update community |
| DELETE | /api/v1/communities/{community_id} | Delete community |
| GET | /api/v1/communities/{community_id}/members | List community members |
| POST | /api/v1/communities/{community_id}/members | Add member to community |
| DELETE | /api/v1/communities/{community_id}/members/{user_id} | Remove member from community |
| PUT | /api/v1/communities/{community_id}/members/{user_id}/role | Update member's role |
| GET | /api/v1/communities/{community_id}/contacts | List community contacts |
| POST | /api/v1/communities/{community_id}/relationships/{related_id} | Create relationship with another community |
| DELETE | /api/v1/communities/{community_id}/relationships/{related_id} | Remove relationship with another community |
| PUT | /api/v1/communities/{community_id}/privacy | Update community privacy level |

### 3.4 Contact Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/contacts | Create new contact |
| GET | /api/v1/contacts | List contacts |
| GET | /api/v1/contacts/{contact_id} | Get contact by ID |
| PUT | /api/v1/contacts/{contact_id} | Update contact |
| DELETE | /api/v1/contacts/{contact_id} | Delete contact |
| GET | /api/v1/contacts/{contact_id}/endorsements | Get contact endorsements |
| POST | /api/v1/contacts/{contact_id}/verify | Verify contact |
| POST | /api/v1/contacts/{contact_id}/services/{service_id} | Add service to contact |
| DELETE | /api/v1/contacts/{contact_id}/services/{service_id} | Remove service from contact |
| POST | /api/v1/contacts/{contact_id}/categories/{category_id} | Add category to contact |
| DELETE | /api/v1/contacts/{contact_id}/categories/{category_id} | Remove category from contact |
| GET | /api/v1/contacts/search | Search contacts |

### 3.5 Endorsement Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/endorsements | Create new endorsement |
| GET | /api/v1/endorsements | List endorsements |
| GET | /api/v1/endorsements/{endorsement_id} | Get endorsement by ID |
| PUT | /api/v1/endorsements/{endorsement_id} | Update endorsement |
| DELETE | /api/v1/endorsements/{endorsement_id} | Delete endorsement |
| POST | /api/v1/endorsements/{endorsement_id}/verify | Verify endorsement |

### 3.6 Category Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/categories | Create new category |
| GET | /api/v1/categories | List categories |
| GET | /api/v1/categories/{category_id} | Get category by ID |
| PUT | /api/v1/categories/{category_id} | Update category |
| DELETE | /api/v1/categories/{category_id} | Delete category |
| GET | /api/v1/categories/{category_id}/contacts | Get contacts in category |
| GET | /api/v1/categories/{category_id}/services | Get services in category |

### 3.7 Service Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/services | Create new service |
| GET | /api/v1/services | List services |
| GET | /api/v1/services/{service_id} | Get service by ID |
| PUT | /api/v1/services/{service_id} | Update service |
| DELETE | /api/v1/services/{service_id} | Delete service |
| GET | /api/v1/services/{service_id}/contacts | Get contacts offering service |

### 3.8 Role Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/roles | Create new role |
| GET | /api/v1/roles | List roles |
| GET | /api/v1/roles/{role_id} | Get role by ID |
| PUT | /api/v1/roles/{role_id} | Update role |
| DELETE | /api/v1/roles/{role_id} | Delete role |
| GET | /api/v1/roles/{role_id}/users | Get users with role |
| POST | /api/v1/roles/{role_id}/permissions | Add permission to role |
| DELETE | /api/v1/roles/{role_id}/permissions/{permission_id} | Remove permission from role |

### 3.9 System Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/system/health | System health check |
| GET | /api/v1/system/info | System information |

## 4. Implementation Guidelines

### 4.1 Endpoint Documentation Standard

All endpoints must be documented following this Sphinx-compatible format:

```python
@router.method(
    "/path",
    response_model=ResponseSchema,
    status_code=status.HTTP_XXX_XXX,
    responses={
        200: {"description": "Success description"},
        400: {"description": "Error description"},
        # Other status codes
    },
)
async def endpoint_function(
    path_param: Type = Path(..., description="Parameter description"),
    query_param: Type = Query(default, description="Parameter description"),
    service: ServiceType = Depends(get_service),
) -> ResponseSchema:
    """
    Short summary of endpoint function.

    Detailed description explaining the endpoint's purpose, functionality,
    and any specific business rules or constraints that apply.

    Args:
        path_param: Description of path parameter
        query_param: Description of query parameter
        service: Injected service dependency

    Returns:
        ResponseSchema: Description of response data

    Raises:
        HTTPException (400): When bad request conditions occur
        HTTPException (404): When resource not found
        HTTPException (409): When conflict occurs
        # Other potential exceptions

    Example:
        ```
        METHOD /api/v1/path/to/resource
        {
            "example": "request body"
        }
        ```
    """
```

### 4.2 Error Handling

Implement consistent error handling across all endpoints:

1. Use appropriate HTTP status codes
2. Provide clear error messages
3. Include error_code for machine-readable identification
4. Add relevant details for debugging when appropriate
5. Map service exceptions to HTTP exceptions correctly

### 4.3 Input Validation

Leverage Pydantic schemas for input validation:

1. Define comprehensive validation rules in schemas
2. Include descriptive error messages for validation failures
3. Use appropriate field types (e.g., EmailStr for emails)
4. Implement custom validators for complex business rules

### 4.4 Authentication and Authorization

Implement robust security measures:

1. Use OAuth2PasswordBearer for JWT token authentication
2. Verify user permissions for each protected endpoint
3. Implement proper token expiration and refresh mechanisms
4. Use dependency injection for user context and authorization

### 4.5 Testing Strategy

Follow these testing principles:

1. Create unit tests for each endpoint's success and failure cases
2. Test validation rules thoroughly
3. Mock service layer dependencies for isolated testing
4. Implement integration tests for critical workflows
5. Verify error responses match expected formats

## 5. Implementation Plan

### 5.1 Implementation Phases

1. **Phase 1**: Core Authentication and User Management
   - Authentication endpoints
   - User CRUD operations
   - Email verification

2. **Phase 2**: Community Management
   - Community CRUD operations
   - Membership management
   - Privacy and relationship endpoints

3. **Phase 3**: Contact and Category Management
   - Contact CRUD operations
   - Category management
   - Service assignment endpoints

4. **Phase 4**: Endorsement System
   - Endorsement creation and management
   - Verification workflows
   - Rating and statistics endpoints

5. **Phase 5**: Advanced Features
   - Search and filtering
   - Analytics endpoints
   - Notification systems

### 5.2 Development Guidelines

1. Create endpoint modules in the existing FastAPI structure
2. Implement endpoint functions with full documentation
3. Add request validation and error handling
4. Write unit tests covering success and failure cases
5. Integrate with existing service layer
6. Perform manual testing with API client
7. Update interactive documentation (Swagger UI and ReDoc)

## 6. Implementation Checklist

### 6.1 Authentication Endpoints

- [ ] Implement POST /api/v1/authentication/login
- [ ] Implement POST /api/v1/authentication/refresh
- [ ] Implement POST /api/v1/authentication/logout
- [ ] Create authentication middleware
- [ ] Write unit tests for authentication flows

### 6.2 User Management Endpoints

- [ ] Implement POST /api/v1/users
- [ ] Implement GET /api/v1/users/{user_id}
- [ ] Implement PUT /api/v1/users/{user_id}
- [ ] Implement DELETE /api/v1/users/{user_id}
- [ ] Implement GET /api/v1/users/{user_id}/communities
- [ ] Implement GET /api/v1/users/{user_id}/contacts
- [ ] Implement GET /api/v1/users/{user_id}/endorsements
- [ ] Implement POST /api/v1/users/{user_id}/verify-email
- [ ] Implement GET /api/v1/users/me
- [ ] Write user endpoint unit tests

### 6.3 Community Management Endpoints

- [ ] Implement POST /api/v1/communities
- [ ] Implement GET /api/v1/communities
- [ ] Implement GET /api/v1/communities/{community_id}
- [ ] Implement PUT /api/v1/communities/{community_id}
- [ ] Implement DELETE /api/v1/communities/{community_id}
- [ ] Implement GET /api/v1/communities/{community_id}/members
- [ ] Implement POST /api/v1/communities/{community_id}/members
- [ ] Implement DELETE /api/v1/communities/{community_id}/members/{user_id}
- [ ] Implement PUT /api/v1/communities/{community_id}/members/{user_id}/role
- [ ] Implement GET /api/v1/communities/{community_id}/contacts
- [ ] Implement POST /api/v1/communities/{community_id}/relationships/{related_id}
- [ ] Implement DELETE /api/v1/communities/{community_id}/relationships/{related_id}
- [ ] Implement PUT /api/v1/communities/{community_id}/privacy
- [ ] Write community endpoint unit tests

### 6.4 Contact Management Endpoints

- [ ] Implement POST /api/v1/contacts
- [ ] Implement GET /api/v1/contacts
- [ ] Implement GET /api/v1/contacts/{contact_id}
- [ ] Implement PUT /api/v1/contacts/{contact_id}
- [ ] Implement DELETE /api/v1/contacts/{contact_id}
- [ ] Implement GET /api/v1/contacts/{contact_id}/endorsements
- [ ] Implement POST /api/v1/contacts/{contact_id}/verify
- [ ] Implement POST /api/v1/contacts/{contact_id}/services/{service_id}
- [ ] Implement DELETE /api/v1/contacts/{contact_id}/services/{service_id}
- [ ] Implement POST /api/v1/contacts/{contact_id}/categories/{category_id}
- [ ] Implement DELETE /api/v1/contacts/{contact_id}/categories/{category_id}
- [ ] Implement GET /api/v1/contacts/search
- [ ] Write contact endpoint unit tests

### 6.5 Endorsement Management Endpoints

- [ ] Implement POST /api/v1/endorsements
- [ ] Implement GET /api/v1/endorsements
- [ ] Implement GET /api/v1/endorsements/{endorsement_id}
- [ ] Implement PUT /api/v1/endorsements/{endorsement_id}
- [ ] Implement DELETE /api/v1/endorsements/{endorsement_id}
- [ ] Implement POST /api/v1/endorsements/{endorsement_id}/verify
- [ ] Write endorsement endpoint unit tests

### 6.6 Category Management Endpoints

- [ ] Implement POST /api/v1/categories
- [ ] Implement GET /api/v1/categories
- [ ] Implement GET /api/v1/categories/{category_id}
- [ ] Implement PUT /api/v1/categories/{category_id}
- [ ] Implement DELETE /api/v1/categories/{category_id}
- [ ] Implement GET /api/v1/categories/{category_id}/contacts
- [ ] Implement GET /api/v1/categories/{category_id}/services
- [ ] Write category endpoint unit tests

### 6.7 Service Management Endpoints

- [ ] Implement POST /api/v1/services
- [ ] Implement GET /api/v1/services
- [ ] Implement GET /api/v1/services/{service_id}
- [ ] Implement PUT /api/v1/services/{service_id}
- [ ] Implement DELETE /api/v1/services/{service_id}
- [ ] Implement GET /api/v1/services/{service_id}/contacts
- [ ] Write service endpoint unit tests

### 6.8 Role Management Endpoints

- [ ] Implement POST /api/v1/roles
- [ ] Implement GET /api/v1/roles
- [ ] Implement GET /api/v1/roles/{role_id}
- [ ] Implement PUT /api/v1/roles/{role_id}
- [ ] Implement DELETE /api/v1/roles/{role_id}
- [ ] Implement GET /api/v1/roles/{role_id}/users
- [ ] Implement POST /api/v1/roles/{role_id}/permissions
- [ ] Implement DELETE /api/v1/roles/{role_id}/permissions/{permission_id}
- [ ] Write role endpoint unit tests

### 6.9 System Endpoints

- [ ] Implement GET /api/v1/system/health
- [ ] Implement GET /api/v1/system/info
- [ ] Write system endpoint unit tests

## 7. Unit Testing Plan

### 7.1 Authentication Tests

- [ ] Test successful authentication with valid credentials
- [ ] Test failed authentication with invalid credentials
- [ ] Test token refresh
- [ ] Test token validation
- [ ] Test token expiration
- [ ] Test logout functionality

### 7.2 User Management Tests

- [ ] Test user creation success
- [ ] Test user creation with duplicate email
- [ ] Test user retrieval with valid ID
- [ ] Test user retrieval with invalid ID
- [ ] Test user update with valid data
- [ ] Test user update with invalid data
- [ ] Test user deletion
- [ ] Test email verification
- [ ] Test password update

### 7.3 Community Management Tests

- [ ] Test community creation success
- [ ] Test community creation with validation errors
- [ ] Test community retrieval
- [ ] Test community update
- [ ] Test community deletion
- [ ] Test member addition
- [ ] Test member removal
- [ ] Test role update
- [ ] Test privacy level update
- [ ] Test relationship management

### 7.4 Contact Management Tests

- [ ] Test contact creation success
- [ ] Test contact creation with validation errors
- [ ] Test contact retrieval
- [ ] Test contact update
- [ ] Test contact deletion
- [ ] Test service assignment
- [ ] Test category assignment
- [ ] Test contact verification
- [ ] Test contact search functionality

### 7.5 Endorsement Management Tests

- [ ] Test endorsement creation success
- [ ] Test endorsement creation with validation errors
- [ ] Test endorsement retrieval
- [ ] Test endorsement update
- [ ] Test endorsement deletion
- [ ] Test endorsement verification
- [ ] Test rating calculation

### 7.6 Authorization Tests

- [ ] Test role-based access control
- [ ] Test permission checking
- [ ] Test resource ownership validation
- [ ] Test community membership access

## 8. Conclusion

This design document outlines a comprehensive plan for implementing the Neighbour Approved API. By following the guidelines, standards, and checklists provided, the development team can create a well-structured, well-documented, and robust API that meets all application requirements while maintaining high standards of code quality and documentation.

The implementation should proceed in phases as outlined, with a focus on thorough testing and documentation at each stage. Regular reviews of the API design and implementation will ensure alignment with business requirements and technical standards.

## Appendix A: Example Endpoint Implementation

```python
@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Bad request"},
        409: {"description": "Email already registered"},
        422: {"description": "Validation error"},
    },
)
async def create_user(
    user_data: UserCreate,
    user_service: UserManagementService = Depends(get_user_service),
) -> UserResponse:
    """
    Create a new user account.

    This endpoint handles the complete user registration process. It validates
    the input data, creates a new user record, and returns the created user
    information. The password is automatically hashed before storage.

    Args:
        user_data: User creation schema containing:
            - email: Valid email address
            - password: Password with minimum 8 characters
            - first_name: User's first name
            - last_name: User's last name
            - mobile_number: Optional mobile number in E.164 format
            - postal_address: Optional postal address
            - physical_address: Optional physical address
            - country: Optional country name
        user_service: Injected user management service

    Returns:
        UserResponse: Newly created user (excluding password)

    Raises:
        HTTPException (409): If email is already registered
        HTTPException (422): If data validation fails

    Example:
        ```
        POST /api/v1/users
        {
            "email": "john.doe@example.com",
            "password": "SecurePass123",
            "first_name": "John",
            "last_name": "Doe",
            "mobile_number": "+12345678901",
            "country": "Canada"
        }
        ```
    """
    try:
        new_user = await user_service.create_user(user_data)
        return new_user
    except DuplicateResourceError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )
```
