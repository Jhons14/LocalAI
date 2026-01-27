# Password Reset Implementation - Backend

This document describes the complete backend implementation for forgotten password functionality.

## ✅ Implementation Status

**All backend components have been implemented and tested:**

- ✅ Database model for password reset tokens
- ✅ Password reset service with security features
- ✅ Email service with HTML templates
- ✅ API endpoints for password reset flow
- ✅ Database migration script
- ✅ Configuration settings
- ✅ Comprehensive test suite
- ✅ API endpoint testing

## 🗄️ Database Changes

### New Table: `password_reset_tokens`

```sql
CREATE TABLE password_reset_tokens (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    token VARCHAR(64) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP WITH TIME ZONE NULL,
    requested_ip VARCHAR(45) NULL,
    requested_user_agent VARCHAR(500) NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

**To apply migration:**

```bash
python3 migrations/add_password_reset_tokens.py
```

## 🔌 API Endpoints

### 1. Request Password Reset

```
POST /auth/forgot-password
Content-Type: application/json

{
    "email": "user@example.com"
}

Response: 200 OK
{
    "message": "If your email is in our system, you will receive reset instructions shortly."
}
```

### 2. Verify Reset Token

```
GET /auth/verify-reset-token/{token}

Response: 200 OK (valid) / 400 Bad Request (invalid)
{
    "valid": true,
    "message": "Token is valid"
}
```

### 3. Reset Password

```
POST /auth/reset-password
Content-Type: application/json

{
    "token": "reset-token-here",
    "new_password": "NewStrongPassword123!"
}

Response: 200 OK
{
    "message": "Password has been reset successfully"
}
```

## ⚙️ Configuration

### Environment Variables

Add these to your `.env.development` or `.env.production`:

```bash
# Email Configuration
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USERNAME=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password
EMAIL_USE_TLS=true
EMAIL_FROM_EMAIL=noreply@localai.app
EMAIL_FROM_NAME=LocalAI
EMAIL_BASE_URL=http://localhost:4321
EMAIL_USE_SSL=false

# Security Settings
SECURITY_RESET_TOKEN_EXPIRE_HOURS=6
SECURITY_MAX_RESET_ATTEMPTS_PER_HOUR=5
```

### Gmail Setup

1. Enable 2-Step Verification in Google Account
2. Generate App Password for Mail
3. Use Gmail address as `EMAIL_SMTP_USERNAME`
4. Use App Password as `EMAIL_SMTP_PASSWORD`

## 🔒 Security Features

### Token Security

- **Cryptographically secure tokens**: 32-byte URL-safe random tokens
- **Time-limited expiration**: 6 hours (configurable)
- **One-time use**: Tokens invalidated after successful reset
- **Rate limiting**: 5 reset requests per hour per user

### Anti-Enumeration

- **Consistent responses**: Same message for valid/invalid emails
- **No user data leakage**: No indication if email exists

### Additional Protection

- **IP and User-Agent logging**: Track reset request origins
- **Account unlocking**: Reset clears failed login attempts
- **Token cleanup**: Automatic cleanup of expired tokens
- **Password validation**: Strong password requirements enforced

## 📧 Email Features

### HTML Email Template

- Professional responsive design
- Clear call-to-action button
- Security warnings and instructions
- Plain text fallback

### Development Mode

- **No SMTP required**: Prints debug info to console
- **Token visibility**: Shows generated tokens for testing
- **Safe testing**: No external dependencies

## 🧪 Testing

### Run Full Test Suite

```bash
python3 test_password_reset.py
```

**Tests include:**

- ✅ User creation and cleanup
- ✅ Email service configuration
- ✅ Token generation and validation
- ✅ Password reset flow
- ✅ Rate limiting
- ✅ Security features
- ✅ Edge cases and error handling

### Run API Endpoint Tests

```bash
# Start the server first
python3 main.py

# In another terminal
python3 test_api_endpoints.py
```

## 📁 New Files Created

```
backend/
├── database/models.py                      # Updated with PasswordResetToken
├── config/settings.py                      # Updated with EmailSettings
├── services/
│   ├── email_service.py                   # New: Email sending service
│   └── auth/
│       └── password_reset_service.py      # New: Password reset logic
├── routers/auth.py                        # Updated with reset endpoints
├── migrations/
│   └── add_password_reset_tokens.py       # New: Database migration
├── requirements.txt                       # Updated with fastapi-mail
├── test_password_reset.py                 # New: Comprehensive tests
├── test_api_endpoints.py                  # New: API endpoint tests
├── .env.example.password_reset           # New: Configuration examples
└── PASSWORD_RESET_IMPLEMENTATION.md      # New: This documentation
```

## 🔄 User Flow

1. **User forgets password** → Goes to login page, clicks "Forgot Password?"
2. **Enters email** → POST to `/auth/forgot-password`
3. **System generates token** → Creates secure token, sends email
4. **User receives email** → Clicks reset link with token
5. **Frontend verifies token** → GET to `/auth/verify-reset-token/{token}`
6. **User enters new password** → POST to `/auth/reset-password`
7. **Password updated** → Token invalidated, user can login

## ⚠️ Important Notes

### Production Checklist

- [ ] Configure real SMTP credentials
- [ ] Set secure `EMAIL_BASE_URL` to production domain
- [ ] Enable HTTPS for reset links
- [ ] Set appropriate CORS origins
- [ ] Consider shorter token expiration for high-security apps
- [ ] Set up monitoring for failed reset attempts

### Dependencies

- `fastapi-mail==1.4.1` (added to requirements.txt)
- All other dependencies already present

### Database Compatibility

- ✅ SQLite (development)
- ✅ PostgreSQL (production)
- Migration script handles both automatically

## 🚀 Ready for Frontend Integration

The backend is fully implemented and tested. Key endpoints:

- `POST /auth/forgot-password` - Request reset
- `GET /auth/verify-reset-token/{token}` - Verify token
- `POST /auth/reset-password` - Reset password

All security features, rate limiting, and error handling are in place.
The system is ready for frontend development!
