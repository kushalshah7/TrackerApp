import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {afterEach, test} from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/session-token.ts', import.meta.url), 'utf8');
const {outputText} = ts.transpileModule(source, {compilerOptions: {
  module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022,
}});
const {apiAccessToken, clearAuthToken} = await import('data:text/javascript;base64,' +
  Buffer.from(outputText).toString('base64'));
const originalFetch = globalThis.fetch;
afterEach(() => {globalThis.fetch = originalFetch; clearAuthToken();});
const jwt = expiry => 'test.' + Buffer.from(JSON.stringify({exp: expiry})).toString('base64url') + '.signature';

test('reproduces the installed SDK token-cache bug and verifies the direct-fetch fix', async () => {
  const {createAuthClient} = await import('@neondatabase/neon-js/auth');
  const {BetterAuthVanillaAdapter} = await import('@neondatabase/neon-js/auth/vanilla/adapters');
  const token = jwt(Date.now() / 1000 + 3600);
  const urls = [];
  globalThis.fetch = async url => {
    urls.push(String(url));
    if (String(url).endsWith('/get-session')) return Response.json({
      session: {id: 'test', userId: 'test', token: 'opaque-session',
        expiresAt: new Date(Date.now() + 3600000).toISOString()},
      user: {id: 'test', email: 'test@example.invalid', emailVerified: true, name: 'Test'},
    }, {headers: {'set-auth-jwt': token}});
    return Response.json({token});
  };
  const client = createAuthClient('https://test.example/api/auth/neon', {adapter: BetterAuthVanillaAdapter()});
  assert.ok((await client.getSession()).data?.session);
  const cached = await client.token();
  assert.equal(cached.data?.token, undefined);
  assert.ok(cached.data?.session);
  assert.equal(urls.length, 1, 'SDK /token never reached the server');
  assert.equal(await apiAccessToken(), token);
  assert.equal(urls.at(-1), '/api/auth/neon/token');
});

test('loads real token shape directly, even when the SDK has cached a session', async () => {
  const token = jwt(Date.now() / 1000 + 3600);
  let calls = 0;
  globalThis.fetch = async (url, options) => {
    calls++;
    assert.equal(url, '/api/auth/neon/token');
    assert.equal(options.credentials, 'same-origin');
    assert.equal(options.cache, 'no-store');
    return Response.json({token});
  };
  assert.equal(await apiAccessToken(), token);
  assert.equal(await apiAccessToken(), token);
  assert.equal(calls, 1);
  clearAuthToken();
  assert.equal(await apiAccessToken(), token);
  assert.equal(calls, 2);
});

test('refreshes nearly expired tokens', async () => {
  let calls = 0;
  globalThis.fetch = async () => {calls++; return Response.json({token: jwt(Date.now() / 1000 + 30)});};
  await apiAccessToken(); await apiAccessToken();
  assert.equal(calls, 2);
});

test('never mistakes a session object for an API token', async () => {
  globalThis.fetch = async () => Response.json({session: {token: 'opaque-session'}, user: {emailVerified: true}});
  await assert.rejects(apiAccessToken(), /Unable to load/);
});

test('rejects signed-out responses', async () => {
  globalThis.fetch = async () => Response.json({message: 'Unauthorized'}, {status: 401});
  await assert.rejects(apiAccessToken(), /session expired/);
});

test('handles a temporary upstream error without returning a token', async () => {
  globalThis.fetch = async () => new Response('Service unavailable', {status: 502});
  await assert.rejects(apiAccessToken(), /Unable to load/);
});
