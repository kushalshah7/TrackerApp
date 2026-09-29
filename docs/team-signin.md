# Team tracker sign-in

The tracker uses its existing Neon Auth service for email/password accounts and
browser sessions. These are separate tracker passwords; employees must not reuse
their Microsoft work passwords. Neon Auth stores password hashes and manages
session cookies. The tracker API also requires a one-time invitation tied to
the signed-in user's exact approved work email.

## First use

1. Get the invitation code for your work email privately from Kushal Shah.
2. Open the tracker, choose **Sign up**, and enter your approved work email,
   a new tracker password of at least 12 characters, and your invitation code.
3. On the same device, the browser keeps your session while it remains valid.
   Signing out, clearing site data, or an expired session requires signing in
   again. Use **Forgot password?** to reset it by email if needed.

Only Kushal Shah and Javed Khan have access to all records. The eight active
Presales members can only see, edit, delete, and download their own rows.

## Administration

The one-time codes are in a local, gitignored CSV under `backend/data/`.
Distribute each code only to its matching employee through a private channel.
The database stores SHA-256 hashes of the codes and binds a redeemed code to
one Neon Auth user ID. Do not commit or upload the CSV.

The production environment requires `NEON_AUTH_BASE_URL`,
`VITE_NEON_AUTH_URL`, `TRACKER_ADMIN_EMAILS`, and
`TRACKER_PRESALES_EMAIL_MAP`. These are configured on the Vercel project.
The Vite URL is embedded in the frontend build, so changing it requires a
new deployment.

Keep Vercel Authentication on **All Deployments** until an administrator and
a Presales member have completed live signup and verified their different
record access. Then use **Standard Protection** to keep historical deployment
URLs private while allowing the current production alias to use tracker sign-in.
