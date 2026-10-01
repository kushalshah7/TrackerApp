import {createAuthClient} from '@neondatabase/neon-js/auth';
import {BetterAuthVanillaAdapter} from '@neondatabase/neon-js/auth/vanilla/adapters';

const authUrl = new URL('/api/auth/neon', window.location.origin).toString();
export const authConfigured = true;
export const authClient = authConfigured
  ? createAuthClient(authUrl, {adapter: BetterAuthVanillaAdapter({fetchOptions: {credentials: 'include'}})})
  : null;

export {apiAccessToken, clearAuthToken} from './session-token';
