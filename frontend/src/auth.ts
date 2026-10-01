import {createAuthClient} from '@neondatabase/neon-js/auth';
import {BetterAuthVanillaAdapter} from '@neondatabase/neon-js/auth/vanilla/adapters';

const authUrl = new URL('/api/auth/neon', window.location.origin).toString();
export const authConfigured = true;
export const authClient = authConfigured
  ? createAuthClient(authUrl, {adapter: BetterAuthVanillaAdapter({fetchOptions: {credentials: 'include'}})})
  : null;

let cachedToken: {value: string; expires: number} | null = null;
export function clearAuthToken() {cachedToken = null;}

export async function apiAccessToken(): Promise<string> {
  if (!authClient) throw new Error('Tracker sign-in is not configured.');
  if (cachedToken && cachedToken.expires > Date.now() + 60000) return cachedToken.value;
  const {data, error} = await authClient.token();
  if (error || !data?.token) {
    clearAuthToken();
    throw new Error('Your session could not be loaded. Please sign in again.');
  }
  try {
    const payload = data.token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const expires = JSON.parse(atob(payload)).exp * 1000;
    if (Number.isFinite(expires)) cachedToken = {value: data.token, expires};
  } catch {clearAuthToken();}
  return data.token;
}
