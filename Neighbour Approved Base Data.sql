-- Disable triggers
DO $$ 
DECLARE
    _table text;
BEGIN
    FOR _table IN 
        SELECT quote_ident(tablename)
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('ALTER TABLE %s DISABLE TRIGGER ALL', _table);
    END LOOP;
END $$;

-- Clear all tables
TRUNCATE TABLE 
    contact_endorsements, 
    user_roles, 
    contacts, 
    communities, 
    community_contacts, 
    community_relationships, 
    user_communities, 
    roles, 
    users
RESTART IDENTITY CASCADE;

-- Insert roles with enhanced RBAC
INSERT INTO roles (name, description, permissions, is_system_role, created_at) VALUES 
('Admin', 'System administrator with full access', '["all"]', TRUE, NOW()),
('Community Manager', 'Can manage community content and members', '["manage_community", "manage_members", "approve_contacts"]', TRUE, NOW()),
('User', 'Standard user privileges', '["create_contacts", "create_endorsements"]', TRUE, NOW());

-- Insert users with enhanced fields
INSERT INTO users (
    email, 
    is_active, 
    password, 
    first_name, 
    last_name, 
    mobile_number, 
    postal_address, 
    physical_address, 
    country, 
    created_at, 
    email_verified, 
    last_login
) VALUES
('admin@example.com', TRUE, 'hashed_password1', 'Admin', 'User', 
 '+14155552671', '123 Admin St', '123 Admin City', 'United States', 
 NOW(), TRUE, NOW()),
('manager@example.com', TRUE, 'hashed_password2', 'Community', 'Manager', 
 '+14155552672', '456 Manager St', '456 Manager City', 'United States', 
 NOW(), TRUE, NOW()),
('user@example.com', TRUE, 'hashed_password3', 'Regular', 'User', 
 '+14155552673', '789 User St', '789 User City', 'United States', 
 NOW(), TRUE, NOW());

-- Link users to roles
INSERT INTO user_roles (user_id, role_id) VALUES
(1, 1),  -- Admin user gets Admin role
(2, 2),  -- Manager gets Community Manager role
(3, 3);  -- Regular user gets User role

-- Create communities
INSERT INTO communities (
    name, 
    description, 
    created_at, 
    owner_id, 
    is_active, 
    privacy_level, 
    updated_at
) VALUES
('Tech Services Network', 'A community for technology service providers', 
 NOW(), 1, TRUE, 'public', NOW()),
('Home Improvement Pros', 'Professional home improvement contractors', 
 NOW(), 2, TRUE, 'public', NOW()),
('Exclusive Contractors', 'Invitation-only contractor network', 
 NOW(), 2, TRUE, 'invitation_only', NOW());

-- Create service provider contacts
INSERT INTO contacts (
    user_id, 
    community_id, 
    contact_name, 
    email, 
    contact_number, 
    primary_contact_first_name, 
    primary_contact_last_name, 
    primary_contact_contact_number, 
    categories, 
    services, 
    endorsements_count
) VALUES
(1, 1, 'TechFix Solutions', 'techfix@example.com', '+14155552674',
 'John', 'Smith', '+14155552675', 'IT Services, Computer Repair',
 'Computer Repair, Network Installation, Data Recovery', 0),
(2, 2, 'Elite Plumbing', 'elite@example.com', '+14155552676',
 'Sarah', 'Johnson', '+14155552677', 'Plumbing, Emergency Services',
 'Pipe Repair, Water Heater Installation, Emergency Plumbing', 0),
(3, 2, 'Master Electricians', 'master@example.com', '+14155552678',
 'Michael', 'Brown', '+14155552679', 'Electrical, Solar',
 'Electrical Wiring, Solar Panel Installation, Safety Inspections', 0);

-- Link contacts to communities
INSERT INTO community_contacts (contact_id, community_id) VALUES
(1, 1),
(2, 2),
(3, 2);

-- Establish community relationships
INSERT INTO community_relationships (community_a_id, community_b_id) VALUES
(1, 2),
(2, 1);

-- Create contact endorsements
INSERT INTO contact_endorsements (
    contact_id, 
    user_id, 
    community_id, 
    endorsed, 
    rating, 
    comment, 
    created_at, 
    updated_at,
    is_verified, 
    verification_date
) VALUES
(1, 2, 1, TRUE, 5, 'Excellent service, very professional', 
 NOW(), NOW(), TRUE, NOW()),
(2, 3, 2, TRUE, 4, 'Good work, completed on time', 
 NOW(), NOW(), TRUE, NOW()),
(3, 2, 2, TRUE, 5, 'Outstanding expertise and professionalism', 
 NOW(), NOW(), FALSE, NULL);

-- Establish community memberships
INSERT INTO user_communities (user_id, community_id) VALUES
(1, 1),
(2, 2),
(2, 3),
(3, 2);

-- Re-enable triggers
DO $$ 
DECLARE
    _table text;
BEGIN
    FOR _table IN 
        SELECT quote_ident(tablename)
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('ALTER TABLE %s ENABLE TRIGGER ALL', _table);
    END LOOP;
END $$;