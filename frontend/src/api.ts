const baseUrl = import.meta.env.VITE_API_BASE_URL || '';

const request = async(path: string, init?: RequestInit) => {
  const response = await fetch(`${baseUrl}/api${path}`, init);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || 'Something went wrong');
  return body;
};

export const api = {
  health: () => request('/health'),
  names: (): Promise<{am: string[]; presales: string[]}> => request('/names'),
  entries: (module: string, limit = 100) => request(`/entries/${module}?limit=${limit}`),
  add: (module: string, data: Record<string, unknown>) => request(`/entries/${module}`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({data})}),
  update: (module: string, recordId: string, data: Record<string, unknown>) => request(`/entries/${module}/${encodeURIComponent(recordId)}`, {method: 'PATCH', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({data})}),
  remove: (module: string, recordId: string) => request(`/entries/${module}/${encodeURIComponent(recordId)}`, {method: 'DELETE'}),
  download: async () => {
    const response = await fetch(`${baseUrl}/api/workbook/download`);
    if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || 'Download failed');
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'Presales_Weekly_Tracker.xlsx';
    anchor.click();
    URL.revokeObjectURL(url);
  },
};
