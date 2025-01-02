-- Insert default roles
INSERT INTO roles (name) VALUES
    ('Administrator'),
    ('Moderator'),
    ('Member'),
    ('Guest');

-- Insert default communities
INSERT INTO communities (name, description, created_at) VALUES
    ('Emerald Estate', 'A gated residential community', NOW()),
    ('Greenstone Hill', 'Suburban neighborhoods sharing contacts', NOW()),
    ('Sebenza', 'Commercial zones with shared resources', NOW()),
    ('Linbro Park', 'A community of tech startups and enterprises', NOW());

-- Insert default users
INSERT INTO users (email, is_active, password, first_name, last_name, mobile_number, postal_address, physical_address, country, created_at, updated_at, role_id) VALUES
    ('admin@example.com', TRUE, 'hashed_admin_password', 'Admin', 'User', '+14155552671', '123 Admin St', '123 Admin St', 'USA', NOW(), NOW(), 1),
    ('moderator@example.com', TRUE, 'hashed_moderator_password', 'Moderator', 'User', '+14155552672', '456 Moderator St', '456 Moderator St', 'USA', NOW(), NOW(), 2),
    ('member@example.com', TRUE, 'hashed_member_password', 'Member', 'User', '+14155552673', '789 Member St', '789 Member St', 'USA', NOW(), NOW(), 3),
    ('guest@example.com', TRUE, 'hashed_guest_password', 'Guest', 'User', '+14155552674', '123 Guest St', '123 Guest St', 'USA', NOW(), NOW(), 4);

-- Assign users to communities
INSERT INTO user_communities (user_id, community_id) VALUES
    (1, 1), -- Admin in Emerald Estate
    (2, 2), -- Moderator in Greenstone Hill
    (3, 3), -- Member in Sebenza
    (4, 4); -- Guest in Linbro Park

-- Insert default contacts
INSERT INTO contacts (user_id, contact_name, email, contact_number, primary_contact_first_name, primary_contact_last_name, primary_contact_contact_number, categories, services, endorsements, added_by_user_id, endorsed_by_user_id) VALUES
    (1, 'Plumber Pro', 'plumber@example.com', '+14155552675', 'John', 'Doe', '+14155552676', 'Plumbing', 'Pipe Repair', 10, 1, 3),
    (2, 'Electrician Expert', 'electrician@example.com', '+14155552677', 'Jane', 'Doe', '+14155552678', 'Electrical', 'Wiring Repair', 15, 2, 4),
    (3, 'Gardening Guru', 'gardener@example.com', '+14155552679', 'Mark', 'Smith', '+14155552680', 'Gardening', 'Lawn Care', 5, 3, 1);

-- Link contacts to communities
INSERT INTO contact_communities (contact_id, community_id) VALUES
    (1, 1), -- Plumber Pro in Emerald Estate
    (2, 2), -- Electrician Expert in Greenstone Hill
    (3, 3); -- Gardening Guru in Sebenza

-- Assign additional roles to users (if applicable)
INSERT INTO user_roles (user_id, role_id) VALUES
    (1, 2), -- Admin also acts as Moderator
    (2, 3), -- Moderator also acts as Member
    (3, 4); -- Member also acts as Guest
