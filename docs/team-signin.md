# Team tracker sign-in

The tracker uses its existing Neon Auth service for email/password accounts and
browser sessions. These are separate tracker passwords; employees must not reuse
their Microsoft work passwords. Neon Auth stores password hashes and manages
session cookies. Only approved work emails with verified ownership can access
the API. Roles and Presales names come from the approved email mapping.

## First use

1. Open the tracker and select **New user? Sign up**.
2. Enter your approved work email and a new tracker password of at least
   12 characters. Confirm ownership using the verification sent to that email.
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
`VITE_NEON_AUTH_URL`, `TRACKER_ADMIN_EMAILS`, and
`TRACKER_PRESALES_EMAIL_MAP`. These are configured on the Vercel project.
The Vite URL is embedded in the frontend build, so changing it requires a
new deployment.

Production uses Vercel **Standard Protection** to keep historical deployment
URLs private while the current production alias uses tracker sign-in. Before
team rollout, complete live signup as an administrator and a Presales member,
verify their different record access, and reopen the app on the same device to
check that the session is retained.
