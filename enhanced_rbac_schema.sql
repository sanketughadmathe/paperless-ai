-- Enhanced RBAC Schema for PaperVault
-- Adds organizations, roles, and permissions for better SaaS functionality

-- Organizations Table (for multi-tenant SaaS)
CREATE TABLE public.organizations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL, -- URL-friendly identifier
    description TEXT,
    logo_url TEXT,
    billing_email TEXT,
    subscription_tier TEXT DEFAULT 'free' CHECK (subscription_tier IN ('free', 'starter', 'professional', 'enterprise')),
    subscription_status TEXT DEFAULT 'trial' CHECK (subscription_status IN ('trial', 'active', 'past_due', 'cancelled', 'expired')),
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    max_users INTEGER DEFAULT 5, -- Based on subscription
    max_documents INTEGER DEFAULT 1000,
    max_storage_bytes BIGINT DEFAULT 5368709120, -- 5GB default
    settings JSONB DEFAULT '{}'::jsonb, -- Org-level settings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;

-- Roles Table (system-wide role definitions)
CREATE TABLE public.roles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT true, -- System vs custom roles
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of permission strings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;

-- Insert default system roles
INSERT INTO public.roles (name, display_name, description, permissions) VALUES
('super_admin', 'Super Administrator', 'Full system access across all organizations', 
 '["system.manage", "org.create", "org.delete", "user.manage_all", "billing.manage_all"]'::jsonb),
('org_owner', 'Organization Owner', 'Full control over organization and all its resources',
 '["org.manage", "user.invite", "user.remove", "document.manage_all", "billing.manage", "role.assign"]'::jsonb),
('org_admin', 'Organization Administrator', 'Administrative access within organization',
 '["user.invite", "document.manage_all", "workflow.manage", "category.manage"]'::jsonb),
('document_manager', 'Document Manager', 'Can manage documents and workflows',
 '["document.create", "document.edit", "document.delete", "document.share", "workflow.manage"]'::jsonb),
('editor', 'Editor', 'Can create and edit documents',
 '["document.create", "document.edit", "document.share"]'::jsonb),
('viewer', 'Viewer', 'Read-only access to documents',
 '["document.view", "search.use"]'::jsonb);

-- Organization Members (many-to-many with roles)
CREATE TABLE public.organization_members (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    role_id UUID REFERENCES public.roles(id) NOT NULL,
    invited_by UUID REFERENCES auth.users(id),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    invitation_accepted_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(organization_id, user_id) -- One role per user per org
);
ALTER TABLE public.organization_members ENABLE ROW LEVEL SECURITY;

-- Custom Permissions (for fine-grained control)
CREATE TABLE public.permissions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE, -- e.g., "document.view", "user.invite"
    display_name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL, -- e.g., "document", "user", "organization"
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert common permissions
INSERT INTO public.permissions (name, display_name, description, category) VALUES
-- System permissions
('system.manage', 'System Management', 'Full system administration', 'system'),
-- Organization permissions
('org.create', 'Create Organizations', 'Create new organizations', 'organization'),
('org.manage', 'Manage Organization', 'Update organization settings', 'organization'),
('org.delete', 'Delete Organization', 'Delete organization', 'organization'),
('org.view', 'View Organization', 'View organization details', 'organization'),
-- User permissions
('user.invite', 'Invite Users', 'Invite new users to organization', 'user'),
('user.remove', 'Remove Users', 'Remove users from organization', 'user'),
('user.manage_all', 'Manage All Users', 'Manage users across all organizations', 'user'),
('role.assign', 'Assign Roles', 'Assign roles to users', 'user'),
-- Document permissions
('document.view', 'View Documents', 'View documents', 'document'),
('document.create', 'Create Documents', 'Upload and create documents', 'document'),
('document.edit', 'Edit Documents', 'Edit document metadata and content', 'document'),
('document.delete', 'Delete Documents', 'Delete documents', 'document'),
('document.share', 'Share Documents', 'Share documents with others', 'document'),
('document.manage_all', 'Manage All Documents', 'Full document management in organization', 'document'),
-- Workflow permissions
('workflow.create', 'Create Workflows', 'Create automation workflows', 'workflow'),
('workflow.manage', 'Manage Workflows', 'Manage all workflows', 'workflow'),
-- Category permissions
('category.manage', 'Manage Categories', 'Create and manage categories', 'category'),
-- Search permissions
('search.use', 'Use Search', 'Perform document searches', 'search'),
('search.advanced', 'Advanced Search', 'Use advanced search features', 'search'),
-- Billing permissions
('billing.view', 'View Billing', 'View billing information', 'billing'),
('billing.manage', 'Manage Billing', 'Manage billing and subscriptions', 'billing'),
('billing.manage_all', 'Manage All Billing', 'Manage billing across organizations', 'billing');

-- User Organization Context (tracks current active organization)
CREATE TABLE public.user_organization_context (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    current_organization_id UUID REFERENCES public.organizations(id) ON DELETE SET NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.user_organization_context ENABLE ROW LEVEL SECURITY;

-- Modify existing profiles table to include organization reference
ALTER TABLE public.profiles ADD COLUMN default_organization_id UUID REFERENCES public.organizations(id);

-- Modify documents table to include organization
ALTER TABLE public.documents ADD COLUMN organization_id UUID REFERENCES public.organizations(id);

-- Update documents to be organization-scoped
CREATE INDEX idx_documents_organization_id ON public.documents (organization_id);
CREATE INDEX idx_documents_org_user ON public.documents (organization_id, user_id);

-- Helper Functions

-- Function to check if user has permission in organization
CREATE OR REPLACE FUNCTION user_has_permission(
    user_uuid UUID,
    org_uuid UUID,
    permission_name TEXT
) RETURNS BOOLEAN AS $$
DECLARE
    user_permissions JSONB;
BEGIN
    SELECT r.permissions INTO user_permissions
    FROM public.organization_members om
    JOIN public.roles r ON om.role_id = r.id
    WHERE om.user_id = user_uuid 
      AND om.organization_id = org_uuid 
      AND om.is_active = true;
    
    RETURN user_permissions ? permission_name;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user's current organization
CREATE OR REPLACE FUNCTION get_current_organization() RETURNS UUID AS $$
DECLARE
    org_id UUID;
BEGIN
    SELECT current_organization_id INTO org_id
    FROM public.user_organization_context
    WHERE user_id = auth.uid();
    
    -- If no context set, get their default or first organization
    IF org_id IS NULL THEN
        SELECT COALESCE(p.default_organization_id, om.organization_id) INTO org_id
        FROM public.profiles p
        LEFT JOIN public.organization_members om ON om.user_id = p.id
        WHERE p.id = auth.uid()
        LIMIT 1;
    END IF;
    
    RETURN org_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Enhanced RLS Policies

-- Organizations policies
CREATE POLICY "Users can view organizations they belong to" ON public.organizations
  FOR SELECT USING (
    id IN (
      SELECT organization_id FROM public.organization_members 
      WHERE user_id = auth.uid() AND is_active = true
    )
  );

CREATE POLICY "Organization owners can update their organization" ON public.organizations
  FOR UPDATE USING (
    user_has_permission(auth.uid(), id, 'org.manage')
  );

-- Organization members policies
CREATE POLICY "Users can view organization members" ON public.organization_members
  FOR SELECT USING (
    organization_id IN (
      SELECT organization_id FROM public.organization_members 
      WHERE user_id = auth.uid() AND is_active = true
    )
  );

CREATE POLICY "Users with user.invite permission can manage members" ON public.organization_members
  FOR ALL USING (
    user_has_permission(auth.uid(), organization_id, 'user.invite')
  );

-- Enhanced document policies
DROP POLICY IF EXISTS "Users can manage their own documents" ON public.documents;
DROP POLICY IF EXISTS "Users can view shared documents" ON public.documents;

CREATE POLICY "Users can view documents in their organizations" ON public.documents
  FOR SELECT USING (
    -- Own documents
    user_id = auth.uid() OR
    -- Organization documents they have access to
    (organization_id IN (
      SELECT organization_id FROM public.organization_members 
      WHERE user_id = auth.uid() AND is_active = true
    ) AND user_has_permission(auth.uid(), organization_id, 'document.view')) OR
    -- Shared documents
    id IN (
      SELECT document_id FROM public.document_shares 
      WHERE (shared_with_user_id = auth.uid() OR shared_with_email = auth.email())
      AND is_active = true
      AND (expires_at IS NULL OR expires_at > NOW())
    )
  );

CREATE POLICY "Users can create documents in their organizations" ON public.documents
  FOR INSERT WITH CHECK (
    user_id = auth.uid() AND
    (organization_id IS NULL OR user_has_permission(auth.uid(), organization_id, 'document.create'))
  );

CREATE POLICY "Users can update documents they own or have permission" ON public.documents
  FOR UPDATE USING (
    user_id = auth.uid() OR
    user_has_permission(auth.uid(), organization_id, 'document.edit') OR
    user_has_permission(auth.uid(), organization_id, 'document.manage_all')
  );

CREATE POLICY "Users can delete documents they own or have permission" ON public.documents
  FOR DELETE USING (
    user_id = auth.uid() OR
    user_has_permission(auth.uid(), organization_id, 'document.delete') OR
    user_has_permission(auth.uid(), organization_id, 'document.manage_all')
  );

-- Workflow policies (organization-scoped)
ALTER TABLE public.workflows ADD COLUMN organization_id UUID REFERENCES public.organizations(id);

CREATE POLICY "Users can manage workflows in their organizations" ON public.workflows
  FOR ALL USING (
    user_id = auth.uid() OR
    user_has_permission(auth.uid(), organization_id, 'workflow.manage')
  );

-- Usage stats update function for organizations
CREATE OR REPLACE FUNCTION update_organization_usage_stats()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE public.organizations 
    SET settings = jsonb_set(
      COALESCE(settings, '{}'::jsonb), 
      '{usage_stats,documents_count}', 
      (COALESCE((settings->'usage_stats'->>'documents_count')::int, 0) + 1)::text::jsonb
    ),
    settings = jsonb_set(
      COALESCE(settings, '{}'::jsonb),
      '{usage_stats,storage_used_bytes}',
      (COALESCE((settings->'usage_stats'->>'storage_used_bytes')::bigint, 0) + NEW.file_size)::text::jsonb
    )
    WHERE id = NEW.organization_id;
  ELSIF TG_OP = 'DELETE' THEN
    UPDATE public.organizations 
    SET settings = jsonb_set(
      COALESCE(settings, '{}'::jsonb),
      '{usage_stats,documents_count}',
      (COALESCE((settings->'usage_stats'->>'documents_count')::int, 0) - 1)::text::jsonb
    ),
    settings = jsonb_set(
      COALESCE(settings, '{}'::jsonb),
      '{usage_stats,storage_used_bytes}',
      (COALESCE((settings->'usage_stats'->>'storage_used_bytes')::bigint, 0) - OLD.file_size)::text::jsonb
    )
    WHERE id = OLD.organization_id;
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger for organization usage stats
CREATE TRIGGER trigger_update_organization_usage_stats
  AFTER INSERT OR DELETE ON public.documents
  FOR EACH ROW EXECUTE FUNCTION update_organization_usage_stats();

-- View for easy role and permission checking
CREATE VIEW public.user_permissions AS
SELECT 
    om.user_id,
    om.organization_id,
    o.name as organization_name,
    r.name as role_name,
    r.display_name as role_display_name,
    r.permissions
FROM public.organization_members om
JOIN public.organizations o ON om.organization_id = o.id
JOIN public.roles r ON om.role_id = r.id
WHERE om.is_active = true;