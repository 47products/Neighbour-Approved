# Neighbour Approved Database Design Documentation

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Data Models](#data-models)
4. [Database Schema](#database-schema)
5. [Relationships and Constraints](#relationships-and-constraints)
6. [Performance Optimization](#performance-optimization)
7. [Implementation Status](#implementation-status)

## Overview

The Neighbour Approved platform uses PostgreSQL as its primary database system, implementing a robust relational model for managing communities, users, service providers, and endorsements. The design prioritizes:

- Data integrity and consistency
- Query performance optimization
- Scalability and maintainability
- Security and access control
- Audit trail capabilities

### Core Features

- Role-based access control
- Hierarchical category management
- Community-based endorsement system
- Service provider verification
- Flexible service categorization

## System Architecture

### High-Level System View

```mermaid
graph TB
    subgraph Client Layer
        Web[Web Application]
        Mobile[Mobile Apps]
        API[API Clients]
    end

    subgraph Application Layer
        Auth[Authentication]
        Services[Service Layer]
        Cache[Cache Layer]
    end

    subgraph Database Layer
        DB[(PostgreSQL)]
        Search[Search Index]
        Analytics[Analytics Store]
    end

    Web --> Auth
    Mobile --> Auth
    API --> Auth
    Auth --> Services
    Services --> Cache
    Services --> DB
    DB --> Search
    DB --> Analytics
```

### Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant A as Auth Service
    participant R as Role Service
    participant D as Database

    U->>A: Login Request
    A->>D: Verify Credentials
    D-->>A: User Data
    A->>R: Get User Roles
    R->>D: Fetch Role Permissions
    D-->>R: Role Data
    R-->>A: Role Permissions
    A-->>U: Auth Token + Permissions
```

## Data Models

### Core Entity Relationships

```mermaid
erDiagram
    User ||--o{ Community : owns
    User ||--o{ Contact : creates
    User }|--|| Role : has
    
    Community ||--o{ Contact : contains
    Community ||--o{ ContactEndorsement : contextualizes
    Community ||--o{ Community : relates_to
    
    Contact ||--o{ ContactEndorsement : receives
    Contact }o--o{ Category : belongs_to
    Contact }o--o{ Service : offers
    
    Service }|--|| Category : categorized_in
```

### Category Hierarchy

```mermaid
graph TD
    R[Root Category] --> A[Category A]
    R --> B[Category B]
    A --> A1[Sub-Category A1]
    A --> A2[Sub-Category A2]
    B --> B1[Sub-Category B1]
    B --> B2[Sub-Category B2]
    A1 --> A1X[Sub-Sub-Category A1X]
    style R fill:#f9f,stroke:#333,stroke-width:4px
```

### Service Organization

```mermaid
graph LR
    subgraph Categories
        C1[Category 1]
        C2[Category 2]
    end
    
    subgraph Services
        S1[Service 1]
        S2[Service 2]
        S3[Service 3]
    end
    
    subgraph Contacts
        P1[Provider 1]
        P2[Provider 2]
    end
    
    C1 --> S1
    C1 --> S2
    C2 --> S3
    S1 --> P1
    S2 --> P1
    S2 --> P2
    S3 --> P2
```

## Database Schema

### User Management Schema

```mermaid
erDiagram
    User {
        int id PK
        string email UK
        string password
        string first_name
        string last_name
        string mobile_number
        bool email_verified
        datetime last_login
        bool is_active
    }
    
    Role {
        int id PK
        string name UK
        string permissions
        bool is_system_role
        bool is_active
    }
    
    user_roles {
        int user_id FK
        int role_id FK
    }
    
    User ||--o{ user_roles : has
    Role ||--o{ user_roles : assigned_to
```

### Community and Contact Schema

```mermaid
erDiagram
    Community {
        int id PK
        string name
        int owner_id FK
        enum privacy_level
        int total_count
        bool is_active
    }
    
    Contact {
        int id PK
        int user_id FK
        string contact_name
        string email UK
        float average_rating
        int verified_count
    }
    
    ContactEndorsement {
        int id PK
        int contact_id FK
        int user_id FK
        int community_id FK
        int rating
        bool is_verified
    }
    
    Community ||--o{ Contact : contains
    Contact ||--o{ ContactEndorsement : receives
    Community ||--o{ ContactEndorsement : contextualizes
```

## Relationships and Constraints

### Foreign Key Relationships

- All relationships use `ON DELETE CASCADE` where appropriate
- Soft deletes implemented via `is_active` flags
- Hierarchical relationships tracked via self-referential foreign keys

### Data Integrity Constraints

1. Primary Key Constraints
   - All tables use auto-incrementing integer IDs
   - Composite keys used for junction tables

2. Unique Constraints
   - Email addresses (users, contacts)
   - Role names
   - Category slugs within parent

3. Check Constraints
   - Rating ranges (1-5)
   - Valid email formats
   - Valid phone numbers
   - Price validations

## Performance Optimization

### Current Indices

1. Primary Indices

   ```sql
   -- Example of primary indices
   CREATE UNIQUE INDEX idx_users_email ON users(email);
   CREATE INDEX idx_contacts_user ON contacts(user_id);
   ```

2. Composite Indices

   ```sql
   -- Example of composite indices
   CREATE INDEX idx_category_hierarchy ON categories(parent_id, path, is_active);
   CREATE INDEX idx_endorsement_context ON contact_endorsements(contact_id, community_id);
   ```

3. Partial Indices

   ```sql
   -- Example of partial indices
   CREATE INDEX idx_active_services ON services(category_id) WHERE is_active = true;
   ```

### Query Optimization

- Implemented covering indices for common queries
- Used materialized views for complex aggregations
- Optimized category tree traversal

## Implementation Status

### Completed Items

- ✅ Base schema implementation
- ✅ Core relationships
- ✅ Primary indices
- ✅ Basic constraints

### Pending Improvements

1. Critical
   - Add additional indices for name searching
   - Implement remaining check constraints
   - Complete validation rules

2. Important
   - Add materialized views for reporting
   - Implement table partitioning
   - Add performance monitoring

3. Future Considerations
   - Analytics optimizations
   - Full-text search integration
   - Caching strategy implementation

This document reflects the current state of the database design and highlights both implemented features and planned improvements. The system is designed to be extensible while maintaining data integrity and query performance.
