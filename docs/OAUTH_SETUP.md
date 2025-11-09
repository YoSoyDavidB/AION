# OAuth Integration Setup Guide

This guide will walk you through setting up OAuth integrations with Google and Microsoft for AION.

## Table of Contents

- [Overview](#overview)
- [Google OAuth Setup](#google-oauth-setup)
- [Microsoft OAuth Setup](#microsoft-oauth-setup)
- [Environment Configuration](#environment-configuration)
- [Testing the Integration](#testing-the-integration)
- [Troubleshooting](#troubleshooting)

## Overview

AION integrates with Google and Microsoft services to access:

- **Google**: Calendar events and Gmail messages
- **Microsoft**: Outlook Calendar events and Email messages

Both integrations use OAuth 2.0 for secure authorization. Tokens are encrypted using Fernet encryption before being stored in the database.

## Google OAuth Setup

### Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name (e.g., "AION Integration")
4. Click "Create"

### Step 2: Enable Required APIs

1. In your project, go to "APIs & Services" → "Library"
2. Search for and enable the following APIs:
   - **Google Calendar API**
   - **Gmail API**
   - **Google+ API** (for user profile information)

### Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Select "External" user type (unless you have a Google Workspace organization)
3. Click "Create"
4. Fill in the required fields:
   - **App name**: AION
   - **User support email**: Your email
   - **Developer contact email**: Your email
5. Click "Save and Continue"
6. On the "Scopes" page, click "Add or Remove Scopes"
7. Add the following scopes:
   - `https://www.googleapis.com/auth/calendar.readonly`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/userinfo.profile`
   - `https://www.googleapis.com/auth/userinfo.email`
8. Click "Update" → "Save and Continue"
9. Add test users if needed (only required if app is not published)
10. Click "Save and Continue" → "Back to Dashboard"

### Step 4: Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Select "Web application"
4. Enter a name (e.g., "AION Web Client")
5. Under "Authorized redirect URIs", add:
   ```
   http://localhost:8000/api/v1/integrations/google/callback
   ```
   For production, add your production URL:
   ```
   https://your-domain.com/api/v1/integrations/google/callback
   ```
6. Click "Create"
7. **Save the Client ID and Client Secret** - you'll need these for your `.env` file

### Step 5: (Optional) Publish Your App

If you want to use the integration with any Google account (not just test users):

1. Go to "OAuth consent screen"
2. Click "Publish App"
3. Note: For production use, you may need to submit for verification if you're requesting sensitive scopes

## Microsoft OAuth Setup

### Step 1: Register an Application in Azure AD

1. Go to the [Azure Portal](https://portal.azure.com/)
2. Navigate to "Azure Active Directory" → "App registrations"
3. Click "New registration"
4. Fill in the details:
   - **Name**: AION Integration
   - **Supported account types**: Select based on your needs:
     - "Accounts in any organizational directory and personal Microsoft accounts" (recommended for most cases)
   - **Redirect URI**: Select "Web" and enter:
     ```
     http://localhost:8000/api/v1/integrations/microsoft/callback
     ```
5. Click "Register"

### Step 2: Configure API Permissions

1. In your app registration, go to "API permissions"
2. Click "Add a permission"
3. Select "Microsoft Graph"
4. Select "Delegated permissions"
5. Add the following permissions:
   - **Calendars.Read** - Read user calendars
   - **Mail.Read** - Read user mail
   - **User.Read** - Sign in and read user profile
   - **offline_access** - Maintain access to data you have given it access to
6. Click "Add permissions"
7. (Optional) Click "Grant admin consent" if you're an admin and want to grant consent for all users

### Step 3: Create a Client Secret

1. Go to "Certificates & secrets"
2. Click "New client secret"
3. Enter a description (e.g., "AION Secret")
4. Select an expiration period (recommend: 24 months)
5. Click "Add"
6. **Copy the secret value immediately** - you won't be able to see it again!

### Step 4: Get Your Application Details

From the app registration "Overview" page, copy:
- **Application (client) ID**
- **Directory (tenant) ID** (optional - defaults to "common" which works for most cases)

## Environment Configuration

Add the following variables to your `.env` file in the root of the AION project:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/integrations/google/callback

# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
MICROSOFT_TENANT_ID=common  # or your specific tenant ID
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/integrations/microsoft/callback

# OAuth Token Encryption (REQUIRED)
# Generate a Fernet key using: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
OAUTH_ENCRYPTION_KEY=your-generated-fernet-key
```

### Generating an Encryption Key

The `OAUTH_ENCRYPTION_KEY` is used to encrypt OAuth tokens in the database. Generate one using:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Important**: Keep this key secure and never commit it to version control. If you lose this key, you won't be able to decrypt existing tokens.

## Testing the Integration

### 1. Start the Backend

```bash
# Make sure containers are running
docker-compose up -d

# Or run locally
poetry run python -m src.main
```

### 2. Start the Frontend

```bash
cd frontend
npm run dev
```

### 3. Test Google Integration

1. Navigate to `http://localhost:5174/settings`
2. Find the "Google Integration" section
3. Click "Connect Google"
4. You'll be redirected to Google's OAuth consent screen
5. Sign in with your Google account
6. Grant the requested permissions
7. You'll be redirected back to the Settings page
8. You should see "Connected to Google" with your email

### 4. Test Microsoft Integration

1. In the same Settings page, find the "Microsoft Integration" section
2. Click "Connect Microsoft"
3. You'll be redirected to Microsoft's OAuth consent screen
4. Sign in with your Microsoft account
5. Grant the requested permissions
6. You'll be redirected back to the Settings page
7. You should see "Connected to Microsoft" with your email

### 5. Verify Data Access

You can test data access using the API endpoints:

```bash
# Get Google Calendar events
curl "http://localhost:8000/api/v1/integrations/google/calendar/events?user_id=david&max_results=10"

# Get Gmail messages
curl "http://localhost:8000/api/v1/integrations/google/gmail/messages?user_id=david&max_results=10"

# Get Microsoft Calendar events
curl "http://localhost:8000/api/v1/integrations/microsoft/calendar/events?user_id=david&max_results=10"

# Get Microsoft Email messages
curl "http://localhost:8000/api/v1/integrations/microsoft/email/messages?user_id=david&max_results=10"
```

## Troubleshooting

### Google OAuth Issues

**Error: "redirect_uri_mismatch"**
- Ensure the redirect URI in your `.env` file matches exactly what you configured in Google Cloud Console
- Check for trailing slashes - they must match exactly

**Error: "access_denied"**
- User declined the authorization
- Check if the user's email is added as a test user (if app is not published)

**Error: "invalid_grant"**
- The refresh token may have expired or been revoked
- User needs to reconnect by clicking "Connect Google" again

### Microsoft OAuth Issues

**Error: "AADSTS50011: The redirect URI specified in the request does not match"**
- Ensure the redirect URI in your `.env` matches what you configured in Azure AD
- Check for http vs https

**Error: "AADSTS65001: The user or administrator has not consented"**
- User needs to grant consent
- Or admin needs to grant tenant-wide consent in Azure AD

**Error: "AADSTS700016: Application not found in the directory"**
- Check your `MICROSOFT_CLIENT_ID` is correct
- Check your `MICROSOFT_TENANT_ID` - try using "common" if you're not sure

### General Issues

**Error: "Encryption key not configured"**
- Make sure `OAUTH_ENCRYPTION_KEY` is set in your `.env` file
- Generate one using the command in the Environment Configuration section

**Error: "Database error" when saving token**
- Ensure the `oauth_tokens` table exists
- Run the migration: `docker exec aion_postgres psql -U aion_user -d aion_db -f /migrations/001_create_oauth_tokens_table.sql`

**Tokens not persisting across restarts**
- Check database connectivity
- Verify the `oauth_tokens` table has data: `docker exec aion_postgres psql -U aion_user -d aion_db -c "SELECT * FROM oauth_tokens;"`

## Security Best Practices

1. **Never commit secrets**: Keep your `.env` file in `.gitignore`
2. **Use environment-specific credentials**: Use different OAuth apps for development and production
3. **Rotate secrets regularly**: Update client secrets and encryption keys periodically
4. **Monitor access**: Review OAuth consent grants regularly
5. **Use HTTPS in production**: Always use HTTPS for redirect URIs in production
6. **Implement token refresh**: The system automatically refreshes expired tokens, but ensure refresh tokens are valid
7. **Audit logs**: Monitor the `last_used_at` field in `oauth_tokens` table to track token usage

## Production Deployment Checklist

- [ ] Create separate OAuth apps for production
- [ ] Update redirect URIs to use production domain with HTTPS
- [ ] Generate new encryption key for production
- [ ] Set up secure secret management (e.g., AWS Secrets Manager, Azure Key Vault)
- [ ] Publish Google OAuth app and complete verification if needed
- [ ] Grant admin consent for Microsoft app if deploying to organization
- [ ] Set up monitoring and alerting for OAuth failures
- [ ] Document token refresh and expiration handling
- [ ] Test OAuth flow in production environment
- [ ] Set up backup for encryption keys

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Microsoft Identity Platform Documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
- [Google Calendar API Reference](https://developers.google.com/calendar/api/v3/reference)
- [Gmail API Reference](https://developers.google.com/gmail/api/reference/rest)
- [Microsoft Graph API Reference](https://docs.microsoft.com/en-us/graph/api/overview)
