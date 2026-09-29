import {InteractionRequiredAuthError, PublicClientApplication} from '@azure/msal-browser';

const tenantId = import.meta.env.VITE_ENTRA_TENANT_ID;
const clientId = import.meta.env.VITE_ENTRA_SPA_CLIENT_ID;
export const apiScope = import.meta.env.VITE_API_SCOPE;
export const authConfigured = Boolean(tenantId && clientId && apiScope);

export const msal = new PublicClientApplication({
  auth: {
    clientId,
    authority: `https://login.microsoftonline.com/${tenantId}`,
    redirectUri: window.location.origin,
  },
  cache: {cacheLocation: 'sessionStorage'},
});

let initialization: Promise<void> | null = null;
export function initializeAuth(): Promise<void> {
  if (!authConfigured) return Promise.reject(new Error('Microsoft work-account sign-in is not configured.'));
  initialization ??= msal.initialize().then(async () => {await msal.handleRedirectPromise();});
  return initialization;
}

export async function signIn() {
  await initializeAuth();
  const result = await msal.loginPopup({scopes: [apiScope]});
  msal.setActiveAccount(result.account);
  return result.account;
}

export async function signOut() {
  const account = msal.getActiveAccount() ?? msal.getAllAccounts()[0];
  if (account) await msal.logoutPopup({account, mainWindowRedirectUri: window.location.origin});
}

export async function apiAccessToken(): Promise<string> {
  await initializeAuth();
  const account = msal.getActiveAccount() ?? msal.getAllAccounts()[0];
  if (!account) throw new Error('Sign in with your Microsoft work account.');
  try {
    return (await msal.acquireTokenSilent({account, scopes: [apiScope]})).accessToken;
  } catch (error) {
    if (!(error instanceof InteractionRequiredAuthError)) throw error;
    return (await msal.acquireTokenPopup({account, scopes: [apiScope]})).accessToken;
  }
}
