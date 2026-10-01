# Team tracker sign-in

The tracker uses its existing Neon Auth service for email/password accounts and
browser sessions. These are separate tracker passwords; employees must not reuse
their Microsoft work passwords. Neon Auth stores password hashes and manages
session cookies. Only approved work emails with verified ownership can access
the API. Roles and Presales names come from the approved email mapping.

## First use

1. Open the tracker and select **Create account**. If already registered, use
   **Sign in** or **Forgot password?**, not Create account again.
2. Enter your approved work email and a new tracker password of at least
   8 characters. Confirm ownership using the verification sent to that email.
3. On the same device, the browser keeps your session while it remains valid.
   Signing out, clearing site data, or an expired session requires signing in
   again. Use **Forgot password?** to reset it by email if needed.

Only Kushal Shah and Javed Khan have access to all records. The eight active
Presales members can only see, edit, delete, and download their own rows. Their
Presales field is filled automatically with the exact approved name and is
read-only in both new-entry and edit forms. Admins can choose a team member.

## Administration

No private links or invitation codes are required. Legacy invitation endpoints
have been removed, and old invitation records are not used for access.

The production environment requires `NEON_AUTH_BASE_URL`,
`TRACKER_ADMIN_EMAILS`, and
`TRACKER_PRESALES_EMAIL_MAP`. These are configured on the Vercel project.
The browser uses `/api/auth/neon` on the tracker's own domain. The backend
proxies only the required authentication endpoints and forwards only Neon
cookies. Session cookies are Secure, HttpOnly, same-site, and never stored in
localStorage. Passwords are passed to managed Neon Auth, not saved by the tracker.
API tokens are cached only in memory until shortly before expiry, reducing
repeat requests. `VITE_NEON_AUTH_URL` is no longer needed.

Neon Auth's trusted-origin list must include
`https://tracker-app-two-swart.vercel.app`. A missing entry causes
`INVALID_ORIGIN` on signup and sign-in. The guarded
`backend/scripts/configure_auth_origin.py` script adds this exact production
origin while preserving the existing list. Unrelated origins stay blocked.

Production uses Vercel **Standard Protection** to keep historical deployment
URLs private while the current production alias uses tracker sign-in. Before
team rollout, complete live signup as an administrator and a Presales member,
verify their different record access, and reopen the app on the same device to
check that the session is retained.
