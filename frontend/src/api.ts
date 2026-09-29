import {apiAccessToken} from './auth';

const baseUrl = import.meta.env.VITE_API_BASE_URL || '';

export class ApiError extends Error {
  constructor(message: string, public status: number) {super(message);}
}

const request = async(path: string, init?: RequestInit) => {
  const token = await apiAccessToken();
  const headers = new Headers(init?.headers);
  headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${baseUrl}/api${path}`, {...init, headers});
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(body.detail || 'Something went wrong', response.status);
  return body;
};

export const api = {
  health: () => request('/health'),
  me: (): Promise<{name: string; email: string; role: 'admin' | 'presales'; presales: string | null}> => request('/me'),
  enroll: (code: string) => request('/auth/enroll', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({code})}),
  names: (): Promise<{am: string[]; presales: string[]}> => request('/names'),
  entries: (module: string, limit = 5000, beforeId?: number): Promise<any[]> => request(`/entries/${module}?limit=${limit}${beforeId ? `&before_id=${beforeId}` : ''}`),
  allEntries: async (module: string): Promise<any[]> => {
    const rows: any[] = [];
    while (true) {
      const beforeId = rows.length ? rows[rows.length - 1]._row : undefined;
      const batch = await request(`/entries/${module}?limit=5000${beforeId ? `&before_id=${beforeId}` : ''}`) as any[];
      rows.push(...batch);
      if (batch.length < 5000) return rows;
    }
  },
  add: (module: string, data: Record<string, unknown>) => request(`/entries/${module}`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({data})}),
  update: (module: string, recordId: string, data: Record<string, unknown>, expectedLastEditedAt: string | null) => request(`/entries/${module}/${encodeURIComponent(recordId)}`, {method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({data, expected_last_edited_at: expectedLastEditedAt})}),
  remove: (module: string, recordId: string, expectedLastEditedAt: string | null) => request(`/entries/${module}/${encodeURIComponent(recordId)}`, {method: 'DELETE', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({expected_last_edited_at: expectedLastEditedAt})}),
  download: async () => {
    const token = await apiAccessToken();
    const response = await fetch(`${baseUrl}/api/workbook/download`, {headers: {Authorization: `Bearer ${token}`}});
    if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || 'Download failed');
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'Presales_Weekly_Tracker.xlsx';
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  },
};
