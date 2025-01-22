# Neighbour Approved Database Design Document

## Table of Contents

1. [Overview](#overview)
2. [Design Principles](#design-principles)
3. [Database Schema](#database-schema)
4. [Entity Details](#entity-details)
5. [Relationships](#relationships)
6. [Indexing Strategy](#indexing-strategy)
7. [Security and Access Control](#security-and-access-control)
8. [Performance Optimisation](#performance-optimisation)

## Overview

The Neighbour Approved database is designed to support a community-driven platform for sharing and endorsing service providers. This document outlines the database architecture, focusing on scalability, performance, and data integrity.

## Design Principles

- **Data Integrity:** Enforce relationships and constraints at the database level
- **Performance:** Optimised query patterns and intelligent indexing
- **Scalability:** Support for growing communities and endorsements
- **Security:** Role-based access control and data protection
- **Auditability:** Track critical data changes and user actions

## Database Schema

### Core Tables

```sql
-- Users and Authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    mobile_number VARCHAR(20),
    email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ,
    last_login TIMESTAMPTZ
);

-- Communities
CREATE TABLE communities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    privacy_level VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ,
    total_members INTEGER DEFAULT 0,
    active_members INTEGER DEFAULT 0,
    CONSTRAINT valid_privacy_level CHECK (privacy_level IN ('public', 'private', 'invitation_only'))
);

-- Contacts (Service Providers)
CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    contact_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    contact_number VARCHAR(20),
    primary_contact_first_name VARCHAR(50) NOT NULL,
    primary_contact_last_name VARCHAR(50) NOT NULL,
    primary_contact_contact_number VARCHAR(20),
    endorsements_count INTEGER DEFAULT 0,
    verified_endorsements_count INTEGER DEFAULT 0,
    average_rating DECIMAL(3,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ
);

-- Categories
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ,
    UNIQUE(parent_id, slug)
);

-- Services
CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    base_price DECIMAL(10,2),
    price_unit VARCHAR(20),
    minimum_hours INTEGER,
    maximum_hours INTEGER,
    requires_consultation BOOLEAN DEFAULT FALSE,
    is_remote_available BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ
);

-- Endorsements
CREATE TABLE contact_endorsements (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    community_id INTEGER REFERENCES communities(id) ON DELETE CASCADE,
    endorsed BOOLEAN DEFAULT TRUE,
    rating INTEGER,
    comment TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_date TIMESTAMPTZ,
    verification_notes TEXT,
    is_public BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ,
    UNIQUE(contact_id, user_id, community_id),
    CONSTRAINT valid_rating CHECK (rating >= 1 AND rating <= 5)
);
```

### Junction Tables

```sql
-- Community Memberships
CREATE TABLE user_communities (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    community_id INTEGER REFERENCES communities(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, community_id)
);

-- Contact Categories
CREATE TABLE contact_categories (
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (contact_id, category_id)
);

-- Contact Services
CREATE TABLE contact_services (
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    service_id INTEGER REFERENCES services(id) ON DELETE CASCADE,
    PRIMARY KEY (contact_id, service_id)
);

-- Community Contacts
CREATE TABLE community_contacts (
    community_id INTEGER REFERENCES communities(id) ON DELETE CASCADE,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (community_id, contact_id)
);
```

## Entity Details

### Users

- Central entity for authentication and authorisation
- Stores personal information and account status
- Links to communities and contacts

### Communities

- Represents groups of users sharing contacts
- Supports different privacy levels
- Tracks membership counts and activity

### Contacts

- Represents service providers
- Maintains endorsement metrics
- Links to categories and services

### Categories

- Hierarchical structure for organising services
- Supports parent-child relationships
- Used for filtering and navigation

### Services

- Specific offerings within categories
- Includes pricing and availability details
- Links to contacts who provide the service

### Endorsements

- Records recommendations and ratings
- Includes verification status
- Links contacts to communities

## Relationships

### One-to-Many

- User → Contacts (creation)
- User → Communities (ownership)
- Category → Services
- Category → Subcategories (self-referential)

### Many-to-Many

- Users ↔ Communities (membership)
- Contacts ↔ Categories
- Contacts ↔ Services
- Communities ↔ Contacts

## Indexing Strategy

### Primary Indices

```sql
-- Email search optimisation
CREATE INDEX idx_users_email ON users(email);

-- Community search optimisation
CREATE INDEX idx_communities_name ON communities(name);
CREATE INDEX idx_communities_owner ON communities(owner_id);

-- Contact search optimisation
CREATE INDEX idx_contacts_name ON contacts(contact_name);
CREATE INDEX idx_contacts_email ON contacts(email);

-- Category hierarchy optimisation
CREATE INDEX idx_categories_parent ON categories(parent_id);
CREATE INDEX idx_categories_slug ON categories(slug);
```

### Composite Indices

```sql
-- Endorsement queries
CREATE INDEX idx_endorsements_contact_community 
ON contact_endorsements(contact_id, community_id);

-- Service categorisation
CREATE INDEX idx_services_category_active 
ON services(category_id, is_active);

-- Contact filtering
CREATE INDEX idx_contacts_metrics 
ON contacts(endorsements_count, average_rating, is_active);
```

## Security and Access Control

### Data Protection

- Passwords stored using bcrypt hashing
- Email addresses encrypted at rest
- Sensitive data access logged

### Access Controls

- Row-level security for community data
- Role-based access control
- Privacy level enforcement

## Performance Optimisation

### Query Optimisation

- Materialized views for metrics
- Partitioning for large tables
- Intelligent use of joins

### Caching Strategy

- Cache frequently accessed data
- Update cache on write operations
- Use Redis for session data

### Monitoring and Maintenance

#### Performance Monitoring

```sql
-- Track slow queries
CREATE TABLE query_logs (
    id SERIAL PRIMARY KEY,
    query_text TEXT,
    execution_time INTERVAL,
    rows_affected INTEGER,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Monitor table statistics
CREATE MATERIALIZED VIEW table_statistics AS
SELECT
    schemaname,
    relname,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables;
```

#### Maintenance Procedures

```sql
-- Regular VACUUM schedule
CREATE OR REPLACE PROCEDURE maintenance_vacuum()
LANGUAGE plpgsql
AS $
BEGIN
    VACUUM ANALYSE contacts;
    VACUUM ANALYSE contact_endorsements;
    VACUUM ANALYSE communities;
END;
$;

-- Index maintenance
CREATE OR REPLACE PROCEDURE rebuild_indexes()
LANGUAGE plpgsql
AS $
BEGIN
    REINDEX TABLE contacts;
    REINDEX TABLE contact_endorsements;
    REINDEX TABLE communities;
END;
$;
```

### Partitioning Strategy

For large tables like endorsements:

```sql
-- Create partitioned endorsements table
CREATE TABLE contact_endorsements (
    id SERIAL,
    contact_id INTEGER,
    user_id INTEGER,
    community_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    -- other fields...
) PARTITION BY RANGE (created_at);

-- Create partitions
CREATE TABLE endorsements_2024_q1 PARTITION OF contact_endorsements
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
CREATE TABLE endorsements_2024_q2 PARTITION OF contact_endorsements
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');
```

### Backup and Recovery

#### Backup Strategy

```bash
# Daily backup script
pg_dump -Fc -f "backup_$(date +%Y%m%d).dump" neighbour_approved

# Point-in-time recovery configuration
wal_level = replica
archive_mode = on
archive_command = 'cp %p /archive/%f'
```

#### Recovery Procedures

```sql
-- Create recovery testing procedure
CREATE OR REPLACE PROCEDURE test_recovery()
LANGUAGE plpgsql
AS $
BEGIN
    -- Verify data integrity
    ANALYSE VERBOSE;
    -- Check constraints
    -- Verify foreign keys
END;
$;
```

### Data Migration and Versioning

#### Version Control

```sql
-- Schema version tracking
CREATE TABLE schema_versions (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    script_name TEXT
);

-- Track migrations
INSERT INTO schema_versions (version, description, script_name)
VALUES (1, 'Initial schema', '001_initial_schema.sql');
```

#### Migration Procedures

```sql
-- Safe data migration procedure
CREATE OR REPLACE PROCEDURE migrate_data(
    p_source_table TEXT,
    p_target_table TEXT,
    p_batch_size INTEGER DEFAULT 1000
)
LANGUAGE plpgsql
AS $
DECLARE
    v_offset INTEGER := 0;
    v_total_rows INTEGER;
BEGIN
    -- Implementation details...
END;
$;
```

### Scaling Considerations

#### Read Replicas

```sql
-- Configure read-only user for replicas
CREATE ROLE readonly_user WITH
    LOGIN
    PASSWORD 'secure_password'
    CONNECTION LIMIT 100
    READONLY;

-- Grant necessary permissions
GRANT CONNECT ON DATABASE neighbour_approved TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
```

#### Connection Pooling

```ini
# pgbouncer configuration
[databases]
neighbour_approved = host=127.0.0.1 port=5432 dbname=neighbour_approved

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
```
