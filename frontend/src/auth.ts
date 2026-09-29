import {createAuthClient} from '@neondatabase/neon-js/auth';
import {BetterAuthVanillaAdapter} from '@neondatabase/neon-js/auth/vanilla/adapters';

const authUrl = import.meta.env.VITE_NEON_AUTH_URL;
export const authConfigured = Boolean(authUrl && authUrl.startsWith('https://'));
export const authClient = authConfigured
  ? createAuthClient(authUrl, {adapter: BetterAuthVanillaAdapter({fetchOptions: {credentials: 'include'}})})
  : null;

export async function apiAccessToken(): Promise<string> {
  if (!authClient) throw new Error('Tracker sign-in is not configured.');
  const {data, error} = await authClient.token();
  if (error || !data?.token) throw new Error('Sign in to continue.');
  return data.token;
}
