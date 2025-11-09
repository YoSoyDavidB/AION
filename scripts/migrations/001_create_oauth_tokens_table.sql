-- Migration: Create oauth_tokens table
-- Description: Stores encrypted OAuth tokens for Google and Microsoft integrations
-- Date: 2025-11-09

CREATE TABLE IF NOT EXISTS oauth_tokens (
    token_id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    access_token TEXT NOT NULL,  -- Encrypted
    refresh_token TEXT,  -- Encrypted
    token_type VARCHAR(50) NOT NULL DEFAULT 'Bearer',
    expires_at TIMESTAMP NOT NULL,
    scopes TEXT NOT NULL,  -- JSON array
    provider_user_id VARCHAR(255),
    provider_user_email VARCHAR(255),
    provider_user_name VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP,

    -- Indexes for faster lookups
    CONSTRAINT oauth_tokens_user_provider_unique UNIQUE (user_id, provider)
);

CREATE INDEX IF NOT EXISTS idx_oauth_tokens_user_id ON oauth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_provider ON oauth_tokens(provider);
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_expires_at ON oauth_tokens(expires_at);

-- Add comment to table
COMMENT ON TABLE oauth_tokens IS 'Stores encrypted OAuth2 tokens for third-party integrations (Google, Microsoft)';
COMMENT ON COLUMN oauth_tokens.access_token IS 'Encrypted access token using Fernet';
COMMENT ON COLUMN oauth_tokens.refresh_token IS 'Encrypted refresh token using Fernet';
COMMENT ON COLUMN oauth_tokens.scopes IS 'JSON array of granted OAuth scopes';
