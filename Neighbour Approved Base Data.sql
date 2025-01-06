-- Database Reset and Seed Script
-- This script provides options to reset and populate the database with sample data

-- Function to safely drop all data
CREATE OR REPLACE FUNCTION drop_all_data() RETURNS void AS $$
BEGIN
    -- Disable triggers temporarily
    SET session_replication_role = 'replica';
    
    -- Truncate all tables in reverse order of dependencies
    TRUNCATE TABLE 
        contact_endorsements,
        contact_services,
        contact_categories,
        community_contacts,
        user_communities,
        user_roles,
        community_relationships,
        services,
        contacts,
        categories,
        communities,
        roles,
        users
    CASCADE;
    
    -- Re-enable triggers
    SET session_replication_role = 'origin';
END;
$$ LANGUAGE plpgsql;

-- Function to update existing data
CREATE OR REPLACE FUNCTION update_existing_data() RETURNS void AS $$
BEGIN
    -- Update timezone info for all timestamp columns
    UPDATE users 
    SET created_at = created_at AT TIME ZONE 'UTC',
        updated_at = COALESCE(updated_at AT TIME ZONE 'UTC', created_at AT TIME ZONE 'UTC'),
        last_login = last_login AT TIME ZONE 'UTC'
    WHERE created_at IS NOT NULL;

    UPDATE communities 
    SET created_at = created_at AT TIME ZONE 'UTC',
        updated_at = COALESCE(updated_at AT TIME ZONE 'UTC', created_at AT TIME ZONE 'UTC')
    WHERE created_at IS NOT NULL;

    UPDATE contacts 
    SET created_at = created_at AT TIME ZONE 'UTC',
        updated_at = COALESCE(updated_at AT TIME ZONE 'UTC', created_at AT TIME ZONE 'UTC')
    WHERE created_at IS NOT NULL;

    UPDATE services 
    SET created_at = created_at AT TIME ZONE 'UTC',
        updated_at = COALESCE(updated_at AT TIME ZONE 'UTC', created_at AT TIME ZONE 'UTC')
    WHERE created_at IS NOT NULL;

    -- Update verification info for endorsements
    UPDATE contact_endorsements 
    SET verification_method = 'system',
        verification_date = CURRENT_TIMESTAMP AT TIME ZONE 'UTC'
    WHERE is_verified = true AND verification_method IS NULL;

    -- Update categories hierarchy info
    WITH RECURSIVE category_tree AS (
        -- Base case: root categories
        SELECT 
            id,
            parent_id,
            slug,
            0 as depth,
            slug::text as path
        FROM categories
        WHERE parent_id IS NULL
        
        UNION ALL
        
        -- Recursive case: child categories
        SELECT 
            c.id,
            c.parent_id,
            c.slug,
            ct.depth + 1,
            ct.path || '/' || c.slug
        FROM categories c
        INNER JOIN category_tree ct ON c.parent_id = ct.id
    )
    UPDATE categories c
    SET 
        depth = ct.depth,
        path = ct.path
    FROM category_tree ct
    WHERE c.id = ct.id;

    -- Update endorsement counts
    UPDATE contacts c
    SET 
        endorsements_count = subquery.total_count,
        verified_endorsements_count = subquery.verified_count,
        average_rating = subquery.avg_rating
    FROM (
        SELECT 
            contact_id,
            COUNT(*) as total_count,
            COUNT(*) FILTER (WHERE is_verified) as verified_count,
            AVG(rating)::numeric(3,2) as avg_rating
        FROM contact_endorsements
        GROUP BY contact_id
    ) subquery
    WHERE c.id = subquery.contact_id;

    -- Update community member counts
    UPDATE communities c
    SET 
        total_count = subquery.total_members,
        active_count = subquery.active_members
    FROM (
        SELECT 
            community_id,
            COUNT(*) as total_members,
            COUNT(*) FILTER (WHERE u.is_active) as active_members
        FROM user_communities uc
        JOIN users u ON u.id = uc.user_id
        GROUP BY community_id
    ) subquery
    WHERE c.id = subquery.community_id;
END;
$$ LANGUAGE plpgsql;

-- Function to create sample data
CREATE OR REPLACE FUNCTION create_sample_data() RETURNS void AS $$
DECLARE
    admin_role_id integer;
    mod_role_id integer;
    user_role_id integer;
    admin_user_id integer;
    mod_user_id integer;
    regular_user_id integer;
    home_cat_id integer;
    prof_cat_id integer;
    cleaning_cat_id integer;
    legal_cat_id integer;
    community_id integer;
    contact_id integer;
BEGIN
    -- Create roles
    INSERT INTO roles (name, description, permissions, is_system_role, created_at)
    VALUES 
        ('admin', 'System administrator', '["manage_users", "manage_communities", "manage_system"]', true, CURRENT_TIMESTAMP)
    RETURNING id INTO admin_role_id;
    
    INSERT INTO roles (name, description, permissions, is_system_role, created_at)
    VALUES 
        ('moderator', 'Community moderator', '["manage_community", "moderate_content"]', true, CURRENT_TIMESTAMP)
    RETURNING id INTO mod_role_id;
    
    INSERT INTO roles (name, description, permissions, is_system_role, created_at)
    VALUES 
        ('user', 'Standard user', '["create_content", "join_communities"]', true, CURRENT_TIMESTAMP)
    RETURNING id INTO user_role_id;

    -- Create users
    INSERT INTO users (
        email, password, first_name, last_name, 
        email_verified, created_at
    )
    VALUES (
        'admin@example.com', 
        'hashed_admin_password', -- Use proper hashing in production
        'Admin',
        'User',
        true,
        CURRENT_TIMESTAMP
    )
    RETURNING id INTO admin_user_id;

    INSERT INTO users (
        email, password, first_name, last_name, 
        email_verified, created_at
    )
    VALUES (
        'mod@example.com',
        'hashed_mod_password',
        'Mod',
        'User',
        true,
        CURRENT_TIMESTAMP
    )
    RETURNING id INTO mod_user_id;

    INSERT INTO users (
        email, password, first_name, last_name, 
        email_verified, created_at
    )
    VALUES (
        'user@example.com',
        'hashed_user_password',
        'Regular',
        'User',
        true,
        CURRENT_TIMESTAMP
    )
    RETURNING id INTO regular_user_id;

    -- Assign roles
    INSERT INTO user_roles (user_id, role_id)
    VALUES 
        (admin_user_id, admin_role_id),
        (mod_user_id, mod_role_id),
        (regular_user_id, user_role_id);

    -- Create categories
    INSERT INTO categories (
        name, slug, description, created_at
    )
    VALUES (
        'Home Services',
        'home-services',
        'Services for home maintenance and improvement',
        CURRENT_TIMESTAMP
    )
    RETURNING id INTO home_cat_id;

    INSERT INTO categories (
        name, slug, description, created_at
    )
    VALUES (
        'Professional Services',
        'professional-services',
        'Professional consulting and business services',
        CURRENT_TIMESTAMP
    )
    RETURNING id INTO prof_cat_id;

    -- Create subcategories
    INSERT INTO categories (
        name, slug, description, parent_id, created_at
    )
    VALUES (
        'Cleaning',
        'cleaning',
        'Cleaning services',
        home_cat_id,
        CURRENT_TIMESTAMP
    )
    RETURNING id INTO cleaning_cat_id;

    INSERT INTO categories (
        name, slug, description, parent_id, created_at
    )
    VALUES (
        'Legal',
        'legal',
        'Legal services',
        prof_cat_id,
        CURRENT_TIMESTAMP
    )
    RETURNING id INTO legal_cat_id;

    -- Create a community
    INSERT INTO communities (
        name, description, owner_id, privacy_level, created_at
    )
    VALUES (
        'Local Services Network',
        'Community for local service providers',
        admin_user_id,
        'public',
        CURRENT_TIMESTAMP
    )
    RETURNING id INTO community_id;

    -- Create a contact
    INSERT INTO contacts (
        user_id, contact_name, email, contact_number,
        primary_contact_first_name, primary_contact_last_name,
        created_at
    )
    VALUES (
        regular_user_id,
        'Premium Cleaning Services',
        'contact@cleaning.example.com',
        '+1234567890',
        'John',
        'Cleaner',
        CURRENT_TIMESTAMP
    )
    RETURNING id INTO contact_id;

    -- Link contact to category
    INSERT INTO contact_categories (contact_id, category_id)
    VALUES (contact_id, cleaning_cat_id);

    -- Create a service
    INSERT INTO services (
        name, description, category_id, base_price,
        price_unit, minimum_hours, maximum_hours,
        requires_consultation, is_remote_available,
        created_at
    )
    VALUES (
        'Standard Cleaning',
        'Regular house cleaning service',
        cleaning_cat_id,
        50.00,
        'hour',
        2,
        8,
        false,
        false,
        CURRENT_TIMESTAMP
    );

    -- Create an endorsement
    INSERT INTO contact_endorsements (
        contact_id, user_id, community_id,
        endorsed, rating, comment,
        is_verified, verification_date,
        created_at
    )
    VALUES (
        contact_id,
        mod_user_id,
        community_id,
        true,
        5,
        'Excellent service, very thorough',
        true,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    );

    -- Update all computed fields
    PERFORM update_existing_data();
END;
$$ LANGUAGE plpgsql;

-- Main execution block
DO $$
BEGIN
    -- Uncomment the desired operations:
    
    -- To drop all data:
    PERFORM drop_all_data();
    
    -- To update existing data:
    -- PERFORM update_existing_data();
    
    -- To create sample data (only run after drop_all_data):
    -- PERFORM create_sample_data();
END $$;