let cachedToken: {value: string; expires: number} | null = null;
export function clearAuthToken() {cachedToken = null;}

export async function apiAccessToken(): Promise<string> {
  if (cachedToken && cachedToken.expires > Date.now() + 60000) return cachedToken.value;
  // Neon SDK classifies /token as getSession and can return its cached session
  // object instead of {token}. Fetch this endpoint directly with first-party cookies.
  const response = await fetch('/api/auth/neon/token', {credentials: 'same-origin', cache: 'no-store'});
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok || !data || typeof data !== 'object' || !('token' in data)
      || typeof data.token !== 'string' || !data.token) {
    clearAuthToken();
    throw new Error(response.status === 401 ? 'Your session expired. Please sign in again.' :
      'Unable to load your session. Please try again.');
  }
  try {
    const payload = data.token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const expires = JSON.parse(atob(payload)).exp * 1000;
    if (Number.isFinite(expires)) cachedToken = {value: data.token, expires};
  } catch {clearAuthToken();}
  return data.token;
}
