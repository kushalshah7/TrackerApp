import {useEffect, useMemo, useState} from 'react';
import {AlertCircle, Check, CheckCircle2, Download, Edit3, FilePlus2, ListFilter, Moon, Sun, Table2, X} from 'lucide-react';
import {api} from './api';
import {modules, months} from './config';
import type {Field, Module} from './types';

const currentMonth = months[new Date().getMonth()];
const currentWeek = String(Math.min(4, Math.ceil(new Date().getDate() / 7)));
const dateOnly = (value: unknown) => String(value ?? '').split(/[T ]/)[0];
const displayDate = (value: unknown) => {
  const [year, month, day] = dateOnly(value).split('-');
  return year && month && day ? `${day}/${month}/${year}` : String(value ?? '');
};
const currencyFields = new Set(['Value (₹)', 'Deal Value']);
const displayValue = (field: Field, value: unknown) => {
  if (field.type === 'date') return displayDate(value);
  if (value === null || value === undefined || value === '') return '';
  if (currencyFields.has(field.name)) {
    const amount = Number(value);
    return `₹${Number.isFinite(amount) ? amount.toLocaleString('en-IN') : String(value)}`;
  }
  return String(value);
};

function Toast({message, error}: {message: string; error?: boolean}) {
  return <div className={`toast ${error ? 'error' : 'success'}`} role="status">
    {error ? <AlertCircle/> : <CheckCircle2/>}{message}
  </div>;
}

function ThemeToggle({theme, onToggle}: {theme: string; onToggle: () => void}) {
  return <button className="icon-button" onClick={onToggle} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>
    {theme === 'dark' ? <Sun/> : <Moon/>}
  </button>;
}

function SheetTabs({active, onChange}: {active: string; onChange: (id: string) => void}) {
  return <div className="sheet-tabs" role="tablist" aria-label="Workbook sheets">
    {modules.map(module => <button key={module.id} role="tab" aria-selected={active === module.id}
      className={active === module.id ? 'active' : ''} onClick={() => onChange(module.id)}>{module.label}</button>)}
  </div>;
}

function initialData(module: Module) {
  return Object.fromEntries(module.fields.map(field => [field.name,
    field.name === 'Month' ? currentMonth : field.name === 'Week' ? currentWeek : '']));
}

function FieldControl({field, value, onChange}: {field: Field; value: unknown; onChange: (value: string) => void}) {
  const common = {value: field.type === 'date' ? dateOnly(value) : String(value ?? ''), onChange: (event: any) => onChange(event.target.value)};
  if (field.type === 'select') return <select {...common}><option value="">Select</option>{field.options?.map(option => <option key={option}>{option}</option>)}</select>;
  if (field.type === 'textarea') return <textarea {...common} rows={3} placeholder="Add details…"/>;
  return <input {...common} type={field.type || 'text'} min={field.type === 'number' ? 0 : undefined}/>;
}

function EntryForm({module, notify}: {module: Module; notify: (message: string, error?: boolean) => void}) {
  const [data, setData] = useState<Record<string, unknown>>(() => initialData(module));
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  useEffect(() => { setData(initialData(module)); setDirty(false); }, [module.id]);
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => { if (dirty) event.preventDefault(); };
    addEventListener('beforeunload', warn); return () => removeEventListener('beforeunload', warn);
  }, [dirty]);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true);
    try {
      await api.add(module.id, data); setData(initialData(module)); setDirty(false); notify(`${module.label} entry added`);
    } catch (error: any) { notify(error.message, true); } finally { setBusy(false); }
  };
  const sections = [...new Set(module.fields.map(field => field.section || 'Details'))];
  return <form onSubmit={submit}>
    {sections.map(section => <section className="form-card" key={section}>
      <div className="section-title"><div><h2>{section}</h2><p>Complete what is known. Empty cells are highlighted red in Excel.</p></div><span>All fields optional</span></div>
      <div className="form-grid">{module.fields.filter(field => (field.section || 'Details') === section).map(field =>
        <label key={field.name} className={field.type === 'textarea' ? 'wide' : ''}>
          <span>{field.label || field.name}</span>
          <FieldControl field={field} value={data[field.name]} onChange={value => {setData({...data, [field.name]: value}); setDirty(true);}}/>
        </label>)}</div>
    </section>)}
    <div className="save-bar"><span>{dirty ? 'Unsaved entry' : 'Ready for a new entry'}</span><button className="primary" disabled={busy}>{busy ? 'Saving…' : <><FilePlus2/> Add entry</>}</button></div>
  </form>;
}

function EditDialog({module, row, onClose, onSaved, notify}: {module: Module; row: any; onClose: () => void; onSaved: () => void; notify: (m: string, e?: boolean) => void}) {
  const [data, setData] = useState<Record<string, unknown>>(() => Object.fromEntries(module.fields.map(field => [field.name, row[field.name] ?? ''])));
  const [busy, setBusy] = useState(false);
  const save = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true);
    try { await api.update(module.id, row._row, data); notify('Entry updated'); onSaved(); }
    catch (error: any) { notify(error.message, true); setBusy(false); }
  };
  return <div className="dialog-backdrop" role="presentation" onMouseDown={event => event.target === event.currentTarget && onClose()}>
    <section className="dialog" role="dialog" aria-modal="true" aria-labelledby="edit-title">
      <div className="dialog-head"><div><span className="eyebrow">ROW {row._row}</span><h2 id="edit-title">Edit {module.label}</h2></div><button className="icon-button" onClick={onClose} aria-label="Close"><X/></button></div>
      <form onSubmit={save}><div className="form-grid compact">{module.fields.map(field => <label key={field.name} className={field.type === 'textarea' ? 'wide' : ''}>
        <span>{field.label || field.name}</span><FieldControl field={field} value={data[field.name]} onChange={value => setData({...data, [field.name]: value})}/>
      </label>)}</div><div className="dialog-actions"><button type="button" className="secondary" onClick={onClose}>Cancel</button><button className="primary" disabled={busy}>{busy ? 'Saving…' : 'Save changes'}</button></div></form>
    </section>
  </div>;
}

function DataPage({module, notify}: {module: Module; notify: (m: string, e?: boolean) => void}) {
  const [rows, setRows] = useState<any[]>([]);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<any | null>(null);
  const load = () => {setLoading(true); api.entries(module.id, 5000).then(setRows).catch((e: Error) => notify(e.message, true)).finally(() => setLoading(false));};
  useEffect(() => {setFilters({}); setEditing(null); load();}, [module.id]);
  const filtered = useMemo(() => rows.filter(row => {
    const matchesColumns = module.fields.every(field => {
      const filter = filters[field.name]?.trim().toLocaleLowerCase();
      const value = displayValue(field, row[field.name]).toLocaleLowerCase();
      return !filter || (filter === '__blanks__' ? !value : value === filter);
    });
    return matchesColumns;
  }), [rows, filters, module]);
  const valuesFor = (field: Field) => [...new Set(rows.map(row => displayValue(field, row[field.name]) || '(Blanks)'))].sort((a, b) => a.localeCompare(b));
  return <section className="data-card">
    <div className="data-toolbar"><div><h2>{module.label} data</h2><p><strong>{filtered.length}</strong> of {rows.length} records shown <span className="desktop-hint">· filter from any column header</span></p></div>{Object.values(filters).some(Boolean) && <button className="secondary" onClick={() => setFilters({})}>Clear filters</button>}</div>
    <details className="mobile-filters"><summary><span className="filter-summary-label"><ListFilter/> Filter columns</span><span className="filter-count">{Object.keys(filters).filter(key => key !== '_all' && filters[key]).length || ''}</span></summary><div className="mobile-filter-grid">
      {module.fields.map(field => <label key={field.name}><span>{field.label || field.name}</span><select value={filters[field.name] || ''} onChange={e => setFilters({...filters, [field.name]: e.target.value})}><option value="">All</option>{valuesFor(field).map(value => <option key={value} value={value === '(Blanks)' ? '__BLANKS__' : value}>{value}</option>)}</select></label>)}
      <button className="secondary" onClick={() => setFilters({})}>Clear all filters</button>
    </div></details>
    {loading ? <div className="empty">Loading workbook data…</div> : !rows.length ? <div className="empty">No entries in this sheet yet.</div> : <div className="table-wrap"><table className="data-table"><thead><tr><th className="action-column">Action</th>{module.fields.map(field => <th key={field.name}><div className="column-heading"><span>{field.label || field.name}</span><details className="column-filter"><summary aria-label={`Filter ${field.name}`} title={`Filter ${field.name}`} className={filters[field.name] ? 'filtered' : ''}><ListFilter/></summary><div className="filter-menu"><button onClick={e => {setFilters({...filters, [field.name]: ''}); e.currentTarget.closest('details')?.removeAttribute('open');}}><span>All</span>{!filters[field.name] && <Check/>}</button>{valuesFor(field).map(value => {const actual = value === '(Blanks)' ? '__BLANKS__' : value; return <button key={value} onClick={e => {setFilters({...filters, [field.name]: actual}); e.currentTarget.closest('details')?.removeAttribute('open');}}><span>{value}</span>{filters[field.name] === actual && <Check/>}</button>;})}</div></details></div></th>)}</tr></thead><tbody>{filtered.map((row, index) => <tr key={row._row}><td className="action-column"><div className="record-identity"><span>Record</span><b>{index + 1}</b><small>Excel row {row._row}</small></div><button className="edit-button" onClick={() => setEditing(row)} aria-label={`Edit record ${index + 1}`}><Edit3/> Edit</button></td>{module.fields.map(field => <td key={field.name} data-label={field.label || field.name} className={!displayValue(field, row[field.name]) ? 'empty-value' : ''}><span className="cell-value">{displayValue(field, row[field.name]) || 'Not provided'}</span></td>)}</tr>)}</tbody></table></div>}
    {editing && <EditDialog module={module} row={editing} onClose={() => setEditing(null)} notify={notify} onSaved={() => {setEditing(null); load();}}/>}
  </section>;
}

export default function App() {
  const [view, setView] = useState<'entry' | 'data'>('entry');
  const [sheet, setSheet] = useState(modules[0].id);
  const [theme, setTheme] = useState(() => localStorage.getItem('tracker-theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  const [toast, setToast] = useState<{message: string; error?: boolean} | null>(null);
  const module = modules.find(item => item.id === sheet)!;
  useEffect(() => {document.documentElement.dataset.theme = theme; localStorage.setItem('tracker-theme', theme);}, [theme]);
  const notify = (message: string, error?: boolean) => {setToast({message, error}); setTimeout(() => setToast(null), 4000);};
  return <div className="app-shell"><a className="skip" href="#main">Skip to main content</a>
    <header className="topbar"><div className="brand"><div className="brand-mark">P</div><div><b>Presales Tracker</b><span>Shared team workbook</span></div></div>
      <nav className="view-switch" aria-label="Primary navigation"><button className={view === 'entry' ? 'active' : ''} onClick={() => setView('entry')}><FilePlus2/> Add entries</button><button className={view === 'data' ? 'active' : ''} onClick={() => setView('data')}><Table2/> View & edit data</button></nav>
      <div className="top-actions"><ThemeToggle theme={theme} onToggle={() => setTheme(theme === 'dark' ? 'light' : 'dark')}/><a className="download" href="/api/workbook/download"><Download/><span>Download Excel</span></a></div>
    </header>
    <main id="main"><div className="page-head"><div><span className="eyebrow">{view === 'entry' ? 'TEAM ENTRY' : 'WORKBOOK DATA'}</span><h1>{view === 'entry' ? 'Add weekly details' : 'Review and update entries'}</h1><p>{view === 'entry' ? 'Choose a sheet and submit details for any team member.' : 'Filter every column and correct existing workbook records.'}</p></div></div>
      <SheetTabs active={sheet} onChange={setSheet}/>
      {view === 'entry' ? <EntryForm module={module} notify={notify}/> : <DataPage module={module} notify={notify}/>}</main>
    {toast && <Toast message={toast.message} error={toast.error}/>}</div>;
}
