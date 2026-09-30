import {useEffect, useMemo, useRef, useState} from 'react';
import {AlertCircle, Check, CheckCircle2, Download, Edit3, FilePlus2, ListFilter, Moon, Sun, Table2, Trash2, X} from 'lucide-react';
import {api} from './api';
import {modules, months} from './config';
import type {Field, Module} from './types';

const currentMonth = months[new Date().getMonth()];
const dateOnly = (value: unknown) => String(value ?? '').split(/[T ]/)[0];
const displayDate = (value: unknown) => {
  const [year, month, day] = dateOnly(value).split('-');
  return year && month && day ? `${day}/${month}/${year}` : String(value ?? '');
};
const displayMonth = (value: unknown) => {
  const match = String(value ?? '').match(/^(\d{4})-(\d{2})/);
  if (!match) return String(value ?? '');
  const month = Number(match[2]);
  if (month < 1 || month > 12) return String(value ?? '');
  return `${new Date(Date.UTC(Number(match[1]), month - 1)).toLocaleString('en-US', {month: 'short', timeZone: 'UTC'})}-${match[1].slice(2)}`;
};
const lastEdited = (value: unknown) => value
  ? `Last edited ${new Date(String(value)).toLocaleString('en-IN', {dateStyle: 'medium', timeStyle: 'short'})}`
  : 'Last edited date unavailable';
const currencyFields = new Set(['Value (₹)', 'Deal Value']);
const displayValue = (field: Field, value: unknown) => {
  if (field.type === 'date') return displayDate(value);
  if (field.type === 'month') return displayMonth(value);
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

function initialData(module: Module, owner: string | null) {
  return Object.fromEntries(module.fields.map(field => [field.name,
    field.name === 'Presales' && owner ? owner : field.name === 'Month' && module.id !== 'weekly-meeting' ? currentMonth : '']));
}

const meetingMonth = (value: unknown) => {
  const month = Number(dateOnly(value).split('-')[1]);
  return month >= 1 && month <= 12 ? months[month - 1] : '';
};

function NamePicker({field, value, names, onChange}: {field: Field; value: unknown; names: string[]; onChange: (value: string) => void}) {
  const selected = String(value ?? '');
  const [query, setQuery] = useState(selected);
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  useEffect(() => setQuery(selected), [selected]);
  useEffect(() => {
    inputRef.current?.setCustomValidity(query !== selected ? 'Select a name from the list, or choose Enter if new name.' : field.required && !selected ? 'Select a name.' : '');
  }, [query, selected, field.required]);
  const matches = names.filter(name => name.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()));
  const allowNewName = field.name !== 'Presales';
  const choose = (name: string) => {onChange(name); setQuery(name); setOpen(false);};
  return <div className="name-picker">
    <input ref={inputRef} role="combobox" aria-label={field.label || field.name} aria-expanded={open} aria-autocomplete="list"
      value={query} required={field.required} placeholder={allowNewName ? 'Search names; enter if new name' : 'Choose a Presales team member'}
      onFocus={() => setOpen(true)} onBlur={() => {setTimeout(() => setOpen(false), 150); if (query !== selected) setQuery(selected);}}
      onChange={event => {setQuery(event.target.value); setOpen(true);}}/>
    {open && <div className="name-options" role="listbox">
      {matches.map(name => <button type="button" role="option" aria-selected={selected === name} key={name}
        onMouseDown={event => event.preventDefault()} onClick={() => choose(name)}>{name}</button>)}
      {allowNewName && query.trim() && matches.length === 0 && <button type="button" className="new-name" role="option"
        aria-selected={false} onMouseDown={event => event.preventDefault()} onClick={() => choose(query.trim())}>Enter if new name: {query.trim()}</button>}
    </div>}
  </div>;
}

function FieldControl({field, value, onChange, names, locked = false}: {field: Field; value: unknown; onChange: (value: string) => void; names: {am: string[]; presales: string[]}; locked?: boolean}) {
  if (field.name === 'Presales' && locked)
    return <input value={String(value ?? '')} readOnly aria-readonly="true" required={field.required}/>;
  if (field.name === 'AM' || field.name === 'Client Manager' || field.name === 'Presales')
    return <NamePicker field={field} value={value} names={field.name === 'Presales' ? names.presales : names.am} onChange={onChange}/>;
  const common = {value: field.type === 'date' ? dateOnly(value) : field.type === 'month' ? dateOnly(value).slice(0, 7) : String(value ?? ''), required: field.required, onChange: (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => onChange(event.target.value)};
  if (field.type === 'select') return <select {...common} disabled={locked}><option value="">Select</option>{field.options?.map(option => <option key={option}>{option}</option>)}</select>;
  if (field.type === 'textarea') return <textarea {...common} rows={3} placeholder="Add details…"/>;
  return <input {...common} type={field.type || 'text'} min={field.type === 'number' ? 0 : undefined}/>;
}

function EntryForm({module, notify, names, refreshNames, owner}: {module: Module; notify: (message: string, error?: boolean) => void; names: {am: string[]; presales: string[]}; refreshNames: () => void; owner: string | null}) {
  const [data, setData] = useState<Record<string, unknown>>(() => initialData(module, owner));
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  useEffect(() => { setData(initialData(module, owner)); setDirty(false); }, [module.id, owner]);
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => { if (dirty) event.preventDefault(); };
    addEventListener('beforeunload', warn); return () => removeEventListener('beforeunload', warn);
  }, [dirty]);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true);
    try {
      await api.add(module.id, data); setData(initialData(module, owner)); setDirty(false); refreshNames(); notify(`${module.label} entry added`);
    } catch (error: any) { notify(error.message, true); } finally { setBusy(false); }
  };
  const sections = [...new Set(module.fields.map(field => field.section || 'Details'))];
  return <form onSubmit={submit}>
    {sections.map(section => <section className="form-card" key={section}>
      <div className="section-title"><div><h2>{section}</h2><p>Complete what is known. Empty cells are highlighted red in Excel.</p></div><span>* Required fields</span></div>
      <div className="form-grid">{module.fields.filter(field => (field.section || 'Details') === section).map(field =>
        <label key={field.name} className={field.type === 'textarea' ? 'wide' : ''}>
          <span>{field.label || field.name}{field.required && <b> *</b>}</span>
          <FieldControl field={field} value={data[field.name]} names={names} locked={(module.id === 'weekly-meeting' && field.name === 'Month') || (field.name === 'Presales' && owner !== null)} onChange={value => {setData({...data, [field.name]: value, ...(module.id === 'weekly-meeting' && field.name === 'Date' ? {Month: meetingMonth(value)} : {})}); setDirty(true);}}/>
        </label>)}</div>
    </section>)}
    <div className="save-bar"><span>{dirty ? 'Unsaved entry' : 'Ready for a new entry'}</span><button className="primary" disabled={busy}>{busy ? 'Saving…' : <><FilePlus2/> Add entry</>}</button></div>
  </form>;
}

function EditDialog({module, row, onClose, onSaved, notify, names, owner}: {module: Module; row: any; onClose: () => void; onSaved: () => void; notify: (m: string, e?: boolean) => void; names: {am: string[]; presales: string[]}; owner: string | null}) {
  const [data, setData] = useState<Record<string, unknown>>(() => ({
    ...Object.fromEntries(module.fields.map(field => [field.name, row[field.name] ?? ''])),
    ...(module.id === 'weekly-meeting' ? {Month: meetingMonth(row.Date)} : {}),
    ...(owner ? {Presales: owner} : {}),
  }));
  const [busy, setBusy] = useState(false);
  const save = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true);
    try { await api.update(module.id, row._row, data, row._last_edited_at); notify('Entry updated'); onSaved(); }
    catch (error: any) { notify(error.message, true); setBusy(false); }
  };
  return <div className="dialog-backdrop" role="presentation" onMouseDown={event => event.target === event.currentTarget && onClose()}>
    <section className="dialog" role="dialog" aria-modal="true" aria-labelledby="edit-title">
      <div className="dialog-head"><div><span className="eyebrow">RECORD {row._row}</span><h2 id="edit-title">Edit {module.label}</h2><small className="edited-date">{lastEdited(row._last_edited_at)}</small></div><button className="icon-button" onClick={onClose} aria-label="Close"><X/></button></div>
      <form onSubmit={save}><div className="form-grid compact">{module.fields.map(field => <label key={field.name} className={field.type === 'textarea' ? 'wide' : ''}>
        <span>{field.label || field.name}{field.required && <b> *</b>}</span><FieldControl field={field} value={data[field.name]} names={names} locked={(module.id === 'weekly-meeting' && field.name === 'Month') || (field.name === 'Presales' && owner !== null)} onChange={value => setData({...data, [field.name]: value, ...(module.id === 'weekly-meeting' && field.name === 'Date' ? {Month: meetingMonth(value)} : {})})}/>
      </label>)}</div><div className="dialog-actions"><button type="button" className="secondary" onClick={onClose}>Cancel</button><button className="primary" disabled={busy}>{busy ? 'Saving…' : 'Save changes'}</button></div></form>
    </section>
  </div>;
}

function DeleteDialog({module, row, onClose, onDeleted, notify}: {module: Module; row: any; onClose: () => void; onDeleted: () => void; notify: (m: string, e?: boolean) => void}) {
  const [busy, setBusy] = useState(false);
  const remove = async () => {
    setBusy(true);
    try { await api.remove(module.id, row._row, row._last_edited_at); notify('Entry deleted'); onDeleted(); }
    catch (error: any) { notify(error.message, true); setBusy(false); }
  };
  return <div className="dialog-backdrop" role="presentation" onMouseDown={event => event.target === event.currentTarget && onClose()}>
    <section className="dialog confirm-dialog" role="alertdialog" aria-modal="true" aria-labelledby="delete-title" aria-describedby="delete-description">
      <div className="dialog-head"><div><span className="eyebrow danger-eyebrow">DELETE ENTRY</span><h2 id="delete-title">Delete this {module.label} entry?</h2></div><button className="icon-button" onClick={onClose} aria-label="Close"><X/></button></div>
      <p id="delete-description">This removes the entry from the tracker and future Excel downloads. An administrator can restore it if needed.</p>
      <div className="dialog-actions"><button type="button" className="secondary" onClick={onClose} disabled={busy}>Keep entry</button><button type="button" className="danger-button" onClick={remove} disabled={busy}>{busy ? 'Deleting…' : <><Trash2/> Delete entry</>}</button></div>
    </section>
  </div>;
}

function DataPage({module, notify, names, refreshNames, owner}: {module: Module; notify: (m: string, e?: boolean) => void; names: {am: string[]; presales: string[]}; refreshNames: () => void; owner: string | null}) {
  const [rows, setRows] = useState<any[]>([]);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<any | null>(null);
  const [deleting, setDeleting] = useState<any | null>(null);
  const loadRequest = useRef(0);
  const load = () => {
    refreshNames();
    const request = ++loadRequest.current;
    setLoading(true);
    api.allEntries(module.id)
      .then(result => {if (request === loadRequest.current) setRows(result);})
      .catch((error: Error) => {if (request === loadRequest.current) notify(error.message, true);})
      .finally(() => {if (request === loadRequest.current) setLoading(false);});
  };
  useEffect(() => {setFilters({}); setEditing(null); setDeleting(null); load();}, [module.id]);
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
    <div className="data-toolbar"><div><h2>{module.label} data</h2><p><strong>{filtered.length}</strong> of {rows.length} records shown <span className="desktop-hint">· filter from any column header</span></p></div><button className="secondary" onClick={load}>Refresh data</button>{Object.values(filters).some(Boolean) && <button className="secondary" onClick={() => setFilters({})}>Clear filters</button>}</div>
    <details className="mobile-filters"><summary><span className="filter-summary-label"><ListFilter/> Filter columns</span><span className="filter-count">{Object.keys(filters).filter(key => key !== '_all' && filters[key]).length || ''}</span></summary><div className="mobile-filter-grid">
      {module.fields.map(field => <label key={field.name}><span>{field.label || field.name}{field.required && <b> *</b>}</span><select value={filters[field.name] || ''} onChange={e => setFilters({...filters, [field.name]: e.target.value})}><option value="">All</option>{valuesFor(field).map(value => <option key={value} value={value === '(Blanks)' ? '__BLANKS__' : value}>{value}</option>)}</select></label>)}
      <button className="secondary" onClick={() => setFilters({})}>Clear all filters</button>
    </div></details>
    {loading ? <div className="empty">Loading workbook data…</div> : !rows.length ? <div className="empty">No entries in this sheet yet.</div> : <div className="table-wrap"><table className="data-table"><thead><tr><th className="action-column">Action</th>{module.fields.map(field => <th key={field.name}><div className="column-heading"><span>{field.label || field.name}{field.required && <b> *</b>}</span><details className="column-filter"><summary aria-label={`Filter ${field.name}`} title={`Filter ${field.name}`} className={filters[field.name] ? 'filtered' : ''}><ListFilter/></summary><div className="filter-menu"><button onClick={e => {setFilters({...filters, [field.name]: ''}); e.currentTarget.closest('details')?.removeAttribute('open');}}><span>All</span>{!filters[field.name] && <Check/>}</button>{valuesFor(field).map(value => {const actual = value === '(Blanks)' ? '__BLANKS__' : value; return <button key={value} onClick={e => {setFilters({...filters, [field.name]: actual}); e.currentTarget.closest('details')?.removeAttribute('open');}}><span>{value}</span>{filters[field.name] === actual && <Check/>}</button>;})}</div></details></div></th>)}</tr></thead><tbody>{filtered.map((row, index) => <tr key={row._row}><td className="action-column"><div className="record-identity"><span>Record</span><b>{index + 1}</b><small>{row._source_sheet ? `${row._source_sheet} row ${row._source_row}` : `Record ${row._row}`}</small></div><small className="edited-date">{lastEdited(row._last_edited_at)}</small><div className="row-actions"><button className="edit-button" onClick={() => setEditing(row)} aria-label={`Edit record ${index + 1}`}><Edit3/> Edit</button><button className="delete-button" onClick={() => setDeleting(row)} aria-label={`Delete record ${index + 1}`}><Trash2/> Delete</button></div></td>{module.fields.map(field => <td key={field.name} data-label={field.label || field.name} className={!displayValue(field, row[field.name]) ? 'empty-value' : ''}><span className="cell-value">{displayValue(field, row[field.name]) || 'Not provided'}</span></td>)}</tr>)}</tbody></table></div>}
    {editing && <EditDialog module={module} row={editing} names={names} owner={owner} onClose={() => setEditing(null)} notify={notify} onSaved={() => {setEditing(null); load();}}/>}
    {deleting && <DeleteDialog module={module} row={deleting} onClose={() => setDeleting(null)} notify={notify} onDeleted={() => {setDeleting(null); load();}}/>}
  </section>;
}

export default function App({viewer, onSignOut}: {viewer: {name: string; email: string; role: 'admin' | 'presales'; presales: string | null}; onSignOut: () => void}) {
  const [view, setView] = useState<'entry' | 'data'>('entry');
  const [sheet, setSheet] = useState(modules[0].id);
  const [theme, setTheme] = useState(() => localStorage.getItem('tracker-theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  const [toast, setToast] = useState<{message: string; error?: boolean} | null>(null);
  const [names, setNames] = useState<{am: string[]; presales: string[]}>({am: [], presales: viewer.presales ? [viewer.presales] : []});
  const refreshNames = () => {api.names().then(setNames).catch((error: Error) => notify(error.message, true));};
  const module = modules.find(item => item.id === sheet)!;
  useEffect(() => {document.documentElement.dataset.theme = theme; localStorage.setItem('tracker-theme', theme);}, [theme]);
  useEffect(() => {refreshNames();}, []);
  const notify = (message: string, error?: boolean) => {setToast({message, error}); setTimeout(() => setToast(null), 4000);};
  return <div className="app-shell"><a className="skip" href="#main">Skip to main content</a>
    <header className="topbar"><div className="brand"><div className="brand-mark">P</div><div><b>Presales Tracker</b><span>Shared team workbook</span></div></div>
      <nav className="view-switch" aria-label="Primary navigation"><button className={view === 'entry' ? 'active' : ''} onClick={() => setView('entry')}><FilePlus2/> Add entries</button><button className={view === 'data' ? 'active' : ''} onClick={() => setView('data')}><Table2/> View & edit data</button></nav>
      <div className="top-actions"><span className="viewer-name">{viewer.name}</span><ThemeToggle theme={theme} onToggle={() => setTheme(theme === 'dark' ? 'light' : 'dark')}/><button className="download" onClick={() => api.download().catch((error: Error) => notify(error.message, true))}><Download/><span>Download Excel</span></button><button className="secondary" onClick={onSignOut}>Sign out</button></div>
    </header>
    <main id="main"><div className="page-head"><div><span className="eyebrow">{view === 'entry' ? 'TEAM ENTRY' : 'WORKBOOK DATA'}</span><h1>{view === 'entry' ? 'Add weekly details' : 'Review and update entries'}</h1><p>{view === 'entry' ? (viewer.presales ? `Submitting under ${viewer.presales}.` : 'Choose a sheet and submit details for any team member.') : (viewer.presales ? `Your ${viewer.presales} records.` : 'Filter every column and correct existing workbook records.')}</p></div></div>
      <SheetTabs active={sheet} onChange={setSheet}/>
      {view === 'entry' ? <EntryForm module={module} notify={notify} names={names} owner={viewer.presales} refreshNames={refreshNames}/> : <DataPage module={module} notify={notify} names={names} owner={viewer.presales} refreshNames={refreshNames}/>}</main>
    {toast && <Toast message={toast.message} error={toast.error}/>}</div>;
}
