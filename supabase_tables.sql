-- Enhanced Supabase Schema for PaperVault
-- Includes improvements for better SaaS functionality

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm; -- For fuzzy text search

-- Enhanced Profiles Table with SaaS features
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    full_name TEXT,
    avatar_url TEXT,
    billing_info JSONB,
    subscription_tier TEXT DEFAULT 'free' CHECK (subscription_tier IN ('free', 'pro', 'enterprise')),
    subscription_status TEXT DEFAULT 'active' CHECK (subscription_status IN ('active', 'cancelled', 'expired', 'trial')),
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    document_quota INTEGER DEFAULT 100, -- Based on subscription tier
    storage_quota_bytes BIGINT DEFAULT 1073741824, -- 1GB default
    usage_stats JSONB DEFAULT '{"documents_uploaded": 0, "storage_used_bytes": 0, "searches_performed": 0}'::jsonb,
    preferences JSONB DEFAULT '{}'::jsonb, -- UI preferences, notification settings
    onboarding_completed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Enhanced Documents Table
CREATE TABLE public.documents (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    mime_type TEXT,
    file_size BIGINT,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_status TEXT DEFAULT 'uploaded' NOT NULL
        CHECK (processing_status IN ('uploaded', 'queued', 'processing', 'completed', 'failed', 'archived')),
    processing_error JSONB, -- Store error details for failed processing
    original_file_url TEXT,
    thumbnail_url TEXT,
    document_type TEXT,
    document_subtype TEXT, -- More granular classification
    extracted_text TEXT,
    summary TEXT,
    key_insights JSONB, -- AI-generated key points, dates, amounts
    metadata JSONB,
    embedding VECTOR(1536),
    ocr_confidence REAL, -- Overall OCR confidence score
    language_detected TEXT,
    page_count INTEGER,
    is_sensitive BOOLEAN DEFAULT false, -- PII/sensitive data flag
    retention_policy TEXT, -- For compliance (e.g., '7_years', 'permanent')
    expires_at TIMESTAMP WITH TIME ZONE, -- Auto-deletion date
    version INTEGER DEFAULT 1, -- Document versioning
    parent_document_id UUID REFERENCES public.documents(id), -- For document versions
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

-- Document Sharing Table (for collaboration features)
CREATE TABLE public.document_shares (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    document_id UUID REFERENCES public.documents(id) ON DELETE CASCADE NOT NULL,
    shared_by_user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    shared_with_email TEXT NOT NULL, -- Can share with non-users
    shared_with_user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE, -- If recipient is a user
    permission_level TEXT NOT NULL CHECK (permission_level IN ('view', 'comment', 'edit')),
    expires_at TIMESTAMP WITH TIME ZONE,
    access_token UUID DEFAULT uuid_generate_v4(), -- For secure access without login
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.document_shares ENABLE ROW LEVEL SECURITY;

-- Enhanced Tags Table with hierarchies
CREATE TABLE public.tags (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    color TEXT, -- Hex color for UI
    parent_tag_id UUID REFERENCES public.tags(id), -- For tag hierarchies
    is_system_tag BOOLEAN DEFAULT false, -- AI-generated vs user-created
    usage_count INTEGER DEFAULT 0, -- Track tag popularity
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, name) -- User-scoped unique tag names
);
ALTER TABLE public.tags ENABLE ROW LEVEL SECURITY;

-- Document_Tags remains the same
CREATE TABLE public.document_tags (
    document_id UUID REFERENCES public.documents(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES public.tags(id) ON DELETE CASCADE,
    confidence_score REAL, -- For AI-suggested tags
    is_ai_suggested BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (document_id, tag_id)
);
ALTER TABLE public.document_tags ENABLE ROW LEVEL SECURITY;

-- Enhanced Entities Table
CREATE TABLE public.entities (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    document_id UUID REFERENCES public.documents(id) ON DELETE CASCADE NOT NULL,
    entity_type TEXT NOT NULL,
    entity_subtype TEXT, -- More specific classification
    entity_value TEXT NOT NULL,
    normalized_value TEXT, -- Standardized format (e.g., dates, amounts)
    start_offset INT,
    end_offset INT,
    page_number INT, -- For multi-page documents
    bounding_box JSONB, -- Coordinates in the document image
    confidence_score REAL,
    validation_status TEXT DEFAULT 'pending' CHECK (validation_status IN ('pending', 'confirmed', 'rejected')),
    validated_by_user BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.entities ENABLE ROW LEVEL SECURITY;

-- Document_Chunks with enhanced features
CREATE TABLE public.document_chunks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    document_id UUID REFERENCES public.documents(id) ON DELETE CASCADE NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_order INT NOT NULL,
    page_number INT,
    chunk_type TEXT DEFAULT 'text' CHECK (chunk_type IN ('text', 'table', 'header', 'footer', 'caption')),
    embedding VECTOR(1536),
    token_count INTEGER, -- For LLM context management
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;

-- Workflows Table (for document processing automation)
CREATE TABLE public.workflows (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    trigger_conditions JSONB NOT NULL, -- e.g., document_type, folder, tags
    actions JSONB NOT NULL, -- e.g., tag, categorize, notify, forward
    is_active BOOLEAN DEFAULT true,
    execution_count INTEGER DEFAULT 0,
    last_executed TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.workflows ENABLE ROW LEVEL SECURITY;

-- Workflow Executions Log
CREATE TABLE public.workflow_executions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    workflow_id UUID REFERENCES public.workflows(id) ON DELETE CASCADE NOT NULL,
    document_id UUID REFERENCES public.documents(id) ON DELETE SET NULL,
    execution_status TEXT NOT NULL CHECK (execution_status IN ('success', 'failed', 'partial')),
    actions_performed JSONB,
    error_details JSONB,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.workflow_executions ENABLE ROW LEVEL SECURITY;

-- Saved Searches/Queries
CREATE TABLE public.saved_searches (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    query JSONB NOT NULL, -- Store the search parameters
    alert_frequency TEXT CHECK (alert_frequency IN ('never', 'daily', 'weekly', 'monthly')),
    last_alert_sent TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.saved_searches ENABLE ROW LEVEL SECURITY;

-- Enhanced Categories Table
CREATE TABLE public.categories (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    icon TEXT, -- Icon identifier for UI
    color TEXT, -- Theme color
    parent_category_id UUID REFERENCES public.categories(id), -- Hierarchical categories
    is_system_category BOOLEAN DEFAULT true, -- System vs user-defined
    ai_keywords JSONB, -- Keywords for AI classification
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;

-- Document_Categories remains similar
CREATE TABLE public.document_categories (
    document_id UUID REFERENCES public.documents(id) ON DELETE CASCADE,
    category_id UUID REFERENCES public.categories(id) ON DELETE CASCADE,
    confidence_score REAL,
    is_ai_assigned BOOLEAN DEFAULT false,
    PRIMARY KEY (document_id, category_id)
);
ALTER TABLE public.document_categories ENABLE ROW LEVEL SECURITY;

-- Enhanced Audit Logs
CREATE TABLE public.audit_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    document_id UUID REFERENCES public.documents(id) ON DELETE SET NULL,
    action_type TEXT NOT NULL,
    action_category TEXT NOT NULL CHECK (action_category IN ('document', 'user', 'system', 'sharing', 'billing')),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    session_id TEXT,
    risk_level TEXT DEFAULT 'low' CHECK (risk_level IN ('low', 'medium', 'high')),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Notifications Table
CREATE TABLE public.notifications (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('info', 'warning', 'error', 'success')),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    action_url TEXT, -- Optional link for the notification
    is_read BOOLEAN DEFAULT false,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- API Keys Table (for third-party integrations)
CREATE TABLE public.api_keys (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE, -- Store hashed version
    permissions JSONB NOT NULL DEFAULT '["read"]'::jsonb, -- e.g., ["read", "write", "delete"]
    last_used TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;

-- Enhanced Indexes
CREATE INDEX idx_documents_user_id ON public.documents (user_id);
CREATE INDEX idx_documents_processing_status ON public.documents (processing_status);
CREATE INDEX idx_documents_document_type ON public.documents (document_type);
CREATE INDEX idx_documents_last_accessed ON public.documents (last_accessed);
CREATE INDEX idx_documents_is_sensitive ON public.documents (is_sensitive);
CREATE INDEX idx_documents_expires_at ON public.documents (expires_at) WHERE expires_at IS NOT NULL;

-- Composite indexes for common queries
CREATE INDEX idx_documents_user_type_status ON public.documents (user_id, document_type, processing_status);
CREATE INDEX idx_documents_user_created ON public.documents (user_id, created_at DESC);

-- Text search indexes
CREATE INDEX idx_documents_file_name_trgm ON public.documents USING gin (file_name gin_trgm_ops);
CREATE INDEX idx_tags_name_trgm ON public.tags USING gin (name gin_trgm_ops);

-- Vector similarity index (if not automatically created)
CREATE INDEX idx_documents_embedding ON public.documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_document_chunks_embedding ON public.document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Full-text search indexes
ALTER TABLE public.documents ADD COLUMN fts_document_text TSVECTOR GENERATED ALWAYS AS (
    setweight(to_tsvector('english', COALESCE(file_name, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(summary, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(extracted_text, '')), 'C')
) STORED;
CREATE INDEX idx_documents_fts_document_text ON public.documents USING GIN (fts_document_text);

ALTER TABLE public.document_chunks ADD COLUMN fts_chunk_text TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', chunk_text)) STORED;
CREATE INDEX idx_document_chunks_fts_chunk_text ON public.document_chunks USING GIN (fts_chunk_text);

-- RLS Policies (Enhanced examples)
-- Profiles policies
CREATE POLICY "Users can view their own profile" ON public.profiles
  FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update their own profile" ON public.profiles
  FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert their own profile" ON public.profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

-- Documents policies
CREATE POLICY "Users can manage their own documents" ON public.documents
  FOR ALL USING (auth.uid() = user_id);

-- Shared documents policy
CREATE POLICY "Users can view shared documents" ON public.documents
  FOR SELECT USING (
    auth.uid() = user_id OR
    EXISTS (
      SELECT 1 FROM public.document_shares
      WHERE document_id = documents.id
      AND (shared_with_user_id = auth.uid() OR shared_with_email = auth.email())
      AND is_active = true
      AND (expires_at IS NULL OR expires_at > NOW())
    )
  );

-- Tags policies
CREATE POLICY "Users can manage their own tags" ON public.tags
  FOR ALL USING (auth.uid() = user_id OR user_id IS NULL);

-- Document tags policies
CREATE POLICY "Users can manage tags on accessible documents" ON public.document_tags
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM public.documents
      WHERE id = document_id
      AND (user_id = auth.uid() OR id IN (
        SELECT document_id FROM public.document_shares
        WHERE shared_with_user_id = auth.uid()
        AND is_active = true
        AND permission_level IN ('edit', 'comment')
      ))
    )
  );

-- Function to update usage stats
CREATE OR REPLACE FUNCTION update_usage_stats()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE public.profiles
    SET usage_stats = jsonb_set(
      usage_stats,
      '{documents_uploaded}',
      ((usage_stats->>'documents_uploaded')::int + 1)::text::jsonb
    ),
    usage_stats = jsonb_set(
      usage_stats,
      '{storage_used_bytes}',
      ((COALESCE(usage_stats->>'storage_used_bytes', '0'))::bigint + NEW.file_size)::text::jsonb
    )
    WHERE id = NEW.user_id;
  ELSIF TG_OP = 'DELETE' THEN
    UPDATE public.profiles
    SET usage_stats = jsonb_set(
      usage_stats,
      '{storage_used_bytes}',
      ((COALESCE(usage_stats->>'storage_used_bytes', '0'))::bigint - OLD.file_size)::text::jsonb
    )
    WHERE id = OLD.user_id;
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger to update usage stats
CREATE TRIGGER trigger_update_usage_stats
  AFTER INSERT OR DELETE ON public.documents
  FOR EACH ROW EXECUTE FUNCTION update_usage_stats();

-- Function to update tag usage count
CREATE OR REPLACE FUNCTION update_tag_usage_count()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE public.tags SET usage_count = usage_count + 1 WHERE id = NEW.tag_id;
  ELSIF TG_OP = 'DELETE' THEN
    UPDATE public.tags SET usage_count = usage_count - 1 WHERE id = OLD.tag_id;
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger for tag usage count
CREATE TRIGGER trigger_update_tag_usage_count
  AFTER INSERT OR DELETE ON public.document_tags
  FOR EACH ROW EXECUTE FUNCTION update_tag_usage_count();
