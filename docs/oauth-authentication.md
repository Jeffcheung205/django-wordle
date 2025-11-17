# OAuth Authentication & Account Linking

## Overview

This document describes how OAuth social authentication (Google) works in this Django application,
including account linking behavior, email verification, and edge cases.

## Table of Contents

- [Architecture](#architecture)
- [Authentication Flows](#authentication-flows)
- [Email Verification Behavior](#email-verification-behavior)
- [Account Linking Logic](#account-linking-logic)
- [Edge Cases & Security Considerations](#edge-cases--security-considerations)
- [Testing Strategy](#testing-strategy)

---

## Architecture

### Components

1. **Django-Allauth**: Third-party package handling OAuth flows
2. **MySocialAccountAdapter**: Custom adapter in `users/custom_allauth.py`
3. **Database Models**:
   - `User`: Django user model (regular account)
   - `SocialAccount`: Links social provider accounts to users (one-to-one relationship to `User`)
   - `EmailAddress`: Tracks email addresses and verification status

### Custom Adapter Hook

The `MySocialAccountAdapter.pre_social_login()` method intercepts the OAuth flow to implement custom logic:

- Block signup when email is missing
- Link social accounts to existing users by email
- Log authentication attempts

---

## Authentication Flows

### Flow 1: New User Sign Up via OAuth

**Scenario:** User has no account, signs up with Google.

```
1. User clicks "Sign in with Google"
2. Google OAuth → returns email: newuser@gmail.com
3. pre_social_login() runs:
   - No existing user found with this email
   - Passes through to default allauth behavior
4. New User created
5. SocialAccount created and linked
6. EmailAddress created (verified=True)
```

**Database State:**
- `User.objects.count()`: 0 → 1
- `SocialAccount.objects.count()`: 0 → 1
- `EmailAddress.objects.count()`: 0 → 1

---

### Flow 2: Account Linking (Matching Email)

**Scenario:** User previously registered with email/password (regular account),
now logs in with Google using same email.

```
1. Existing user: user@gmail.com (registered via email/password)
   - `User.objects.count()`: 1 (unchanged)
   - `SocialAccount.objects.count()`: 0
2. User logs out
3. User clicks "Sign in with Google"
4. Google OAuth → returns email: user@gmail.com (same email!)
5. pre_social_login() runs:
   - User is anonymous (logged out)
   - Finds existing user with matching email
   - Calls sociallogin.connect(request, user)
6. SocialAccount created and linked to existing user
   - `SocialAccount.objects.count()`: 0 → 1
7. User is logged in, while user@gmail.com in EmailAddress remains verified=False
```

---

### Flow 3: Connecting OAuth While Logged In

**Scenario:** User is logged in with email/password, wants to connect Google account.

```
1. User logged in: user1@example.com
2. User clicks "Connect Google Account"
3. Google OAuth → returns email: user1@gmail.com (different email!)
4. Default django-allauth behavior takes over
   (how it works?, still through pre_social_login? the entry endpoint is google/login/callback/)
5. Google account linked to logged-in user
6. SocialAccount created
```

**Key Behavior:**
- User's primary email remains: `user1@example.com`
- Google OAuth email: `user1@gmail.com` is stored in SocialAccount
- **No email match validation occurs**
- User can have multiple social accounts with different emails

**Database State:**
- User has primary email: `user1@example.com`
- SocialAccount linked with OAuth email: `user1@gmail.com`
- Both emails associated with same user

---

### Flow 4: Missing Email from OAuth

**Scenario:** OAuth provider doesn't return email (privacy settings).

```
1. User clicks "Sign in with Google"
2. Google OAuth → no email returned (user privacy settings)
3. pre_social_login() runs:
   - Detects missing email
   - Raises ImmediateHttpResponse
   - Redirects to login page with error message
4. Signup blocked
```

**Error Message:**
```
"Your Google account must provide an email address to sign up.
Please check your Google account settings."
```

---

## Email Verification Behavior

### Important Discovery (Tested)

**Django-Allauth Default Behavior:**

Even when a user signs up or links an account via OAuth (Google), the `EmailAddress` record in the
database has `verified=False`.

```python
# Tested behavior:
user = User.objects.create_user(username='test', email='test@example.com')
# User signs in via Google OAuth with same email
email_record = EmailAddress.objects.get(email='test@example.com')
assert email_record.verified == False  # ✓ Confirmed
```

### Why OAuth Emails Are Not Auto-Verified

1. **Django-Allauth Philosophy**:
   - Email verification is a separate concern from authentication
   - OAuth verifies identity, not email ownership in the app's context

2. **Flexibility**:
   - Allows apps to implement custom verification flows
   - Users may need to explicitly verify email for certain features

3. **Consistency**:
   - All email addresses follow same verification flow
   - Regardless of how user signed up (password vs OAuth)

### Implications

**For OAuth Sign Up:**
- User can log in immediately via OAuth ✓
- But may need email verification for:
  - Password reset
  - Email notifications
  - Account recovery
  - Certain app features requiring verified email

**For Account Linking:**
- Linking OAuth account doesn't verify existing email
- User's email verification status remains unchanged

---

## Account Linking Logic

### Linking Conditions

Account linking occurs when **ALL** conditions are met:

```python
if not sociallogin.is_existing and request.user.is_anonymous:
    # Linking logic runs
```

1. `not sociallogin.is_existing`: Social account doesn't already exist
2. `request.user.is_anonymous`: User is not logged in

### Linking Process

1. **Email Lookup**: `User.objects.get(email=email)`
2. **Connect**: `sociallogin.connect(request, user)`
3. **Log**: Record the linking event

### When Linking Does NOT Occur

| Scenario                       | Linking? | Reason                    |
|----------                      |----------|--------                   |
| User logged in                 | No       | `is_anonymous == False`   |
| Social account already exists  | No       | `is_existing == True`     |
| No matching email found        | No       | `User.DoesNotExist`       |
| Multiple users with same email | No       | `MultipleObjectsReturned` |

Social account connection can be removed if the account was created as regular account before

---

## Edge Cases & Security Considerations

### 1. Email Mismatch During Connection

**Scenario:**
- User account email: `user1@example.com`
- User logged in
- Connects Google with: `user1@gmail.com`

**Current Behavior:**
- Connection succeeds ✓
- No email validation ✓
- User has two different emails

**Security Implication:**
- User could theoretically connect someone else's Google account
- Mitigated by OAuth requiring login to Google account

**Recommendation:**
- Current behavior is acceptable
- Google OAuth ensures user owns the Google account
- Email mismatch is user's choice

---

### 2. Account Takeover Risk (Unverified Emails)

**Scenario:**
- User A registers with `test@example.com` (email unverified)
- User B authenticates via Google with `test@example.com`
- System links User B to User A's account

**Current Behavior:**
- Linking occurs based on email match
- No verification status check

**Risk Level:** Low-Medium
- Requires attacker to control an unverified email in the system
- Requires victim to not verify their email

**Mitigation:**
- Consider requiring email verification before allowing linking
- Or: Check `EmailAddress.verified` status before linking

**Potential Fix:**
```python
# In custom_allauth.py
user = User.objects.get(email=email)
email_obj = EmailAddress.objects.get(user=user, email=email)
if not email_obj.verified:
    # Reject linking or require verification
    logger.warning(f'Rejected linking to unverified email: {email}')
    return
sociallogin.connect(request, user)
```

---

## Future Enhancements

### Recommended

1. **Email Verification Check**: Don't link to unverified emails
2. **Email Match Validation**: Warn when connecting OAuth with different email
3. **Admin Interface**: Show all linked accounts for a user
4. **Email Sync**: Update email when provider email changes
5. **Comprehensive Tests**: Cover all edge cases documented above

### Considerations

1. **Multiple OAuth Providers**: Support Facebook, GitHub, etc.
2. **Unlinking Flow**: Allow users to disconnect OAuth accounts
3. **Primary Email Logic**: Which email should be primary?
4. **Email Uniqueness**: Enforce database constraints

---

## References

- [Django-Allauth Documentation](https://django-allauth.readthedocs.io/)
- Custom Adapter: `christmax/users/custom_allauth.py`
- Tests: `christmax/users/test_social_auth.py`
- Models: Django-Allauth `SocialAccount`, `EmailAddress`

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-11-17 | Initial documentation | - |
| 2025-11-17 | Email verification behavior confirmed through testing | - |
