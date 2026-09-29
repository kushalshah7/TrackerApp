# Microsoft work-account access setup

The tracker uses a single Microsoft Entra tenant. The API checks a signed access
token on every data route and maps approved work emails to one of two roles:
administrators can read and edit all records; Presales members can read and edit
only records assigned to their name. A Presales Excel download includes only
that member's records.

## 1. Register the API

In the Microsoft Entra admin center, open **App registrations** and create
`Presales Tracker API` with **Accounts in this organizational directory only**.
Record its **Application (client) ID** and **Directory (tenant) ID**.

Under **Expose an API**, set the Application ID URI to `api://<API-client-ID>`.
Add an enabled delegated scope named `Tracker.Access`, with admin consent.
In the API app manifest, set `api.requestedAccessTokenVersion` to `2` so the
API receives version 2 access tokens.

## 2. Register the browser app

Create a second single-tenant registration named `Presales Tracker SPA`.
Under **Authentication**, add a **Single-page application** redirect URI:
`https://tracker-app-two-swart.vercel.app`. Add `http://localhost:5173` only
if local sign-in is needed. Record this app's Application (client) ID.

Under **API permissions**, add the `Tracker.Access` delegated permission from
`Presales Tracker API` and grant admin consent. Do not create a client secret
for the SPA.

## 3. Configure Vercel Production environment variables

Set these on the `tracker-app` project, scoped to **Production**:

| Variable | Value |
| --- | --- |
| `ENTRA_TENANT_ID` | Directory (tenant) ID |
| `ENTRA_API_AUDIENCE` | API Application (client) ID, the GUID |
| `ENTRA_API_SCOPE` | `api://<API-client-ID>/Tracker.Access` |
| `ENTRA_SPA_CLIENT_ID` | SPA Application (client) ID |
| `TRACKER_ADMIN_EMAILS` | Comma-separated approved administrator work emails |
| `TRACKER_PRESALES_EMAIL_MAP` | JSON object mapping each of the eight approved work emails to its exact Presales roster name |
| `VITE_ENTRA_TENANT_ID` | Same tenant ID |
| `VITE_ENTRA_SPA_CLIENT_ID` | Same SPA client ID |
| `VITE_API_SCOPE` | Same full API scope URI |

The email mapping must include each active Presales name exactly once. Do not
put a secret in any `VITE_` variable; those values are bundled into the browser
app. A new production deployment is required after changing these variables.

## 4. Verify before team rollout

1. Confirm anonymous `/api/entries/weekly-review` and `/api/workbook/download`
   requests are rejected.
2. Sign in as one Presales member; verify their list, edit, delete, and Excel
   download contain only their own rows.
3. Sign in as each administrator; verify both can see and edit all rows.
4. Sign in with an unlisted work account; verify access is denied.
5. Keep Vercel Authentication set to **All Deployments** until the Entra checks
   pass. Once they pass, **Standard Protection** can protect old and preview
   deployment URLs while the current production alias uses Entra sign-in.

See Microsoft's [API scope setup](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-configure-app-expose-web-apis)
and [SPA registration guide](https://learn.microsoft.com/en-us/entra/identity-platform/scenario-spa-app-registration).
