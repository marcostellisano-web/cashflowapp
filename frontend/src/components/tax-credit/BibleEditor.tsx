import { useEffect, useState } from 'react';
import { deleteBreakoutBibleEntry, getBreakoutBible, upsertBreakoutBibleEntry } from '../../lib/api';
import type { BreakoutBibleEntry } from '../../types/tax_credit';

type PctField =
  | 'prov_labour_pct'
  | 'fed_labour_pct'
  | 'prov_svc_labour_pct'
  | 'svc_property_pct'
  | 'fed_svc_labour_pct';

const PCT_FIELDS: { key: PctField; label: string }[] = [
  { key: 'prov_labour_pct',     label: 'Prov Labour %' },
  { key: 'fed_labour_pct',      label: 'Fed Labour %' },
  { key: 'prov_svc_labour_pct', label: 'Prov Svc %' },
  { key: 'svc_property_pct',    label: 'Svc Property %' },
  { key: 'fed_svc_labour_pct',  label: 'Fed Svc %' },
];

function fmtPct(v: number): string {
  return `${Math.round(v * 10000) / 100}%`;
}

function parsePct(s: string): number {
  const n = parseFloat(s.trim().replace('%', ''));
  if (isNaN(n)) return 0;
  return n > 1 ? n / 100 : n;
}

type EditState = Partial<Record<PctField, string>> & {
  is_non_prov?: boolean;
  description?: string;
};

export default function BibleEditor() {
  const [entries, setEntries] = useState<BreakoutBibleEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [edits, setEdits] = useState<Record<string, EditState>>({});
  const [saving, setSaving] = useState<Record<string, boolean>>({});
  const [saveStatus, setSaveStatus] = useState<Record<string, 'saved' | 'error'>>({});

  // New account form state
  const [newCode, setNewCode] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [addError, setAddError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  // Filter
  const [filter, setFilter] = useState('');

  useEffect(() => {
    setLoading(true);
    getBreakoutBible()
      .then(setEntries)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const visibleEntries = entries.filter((e) => {
    const q = filter.toLowerCase();
    return (
      e.account_code.toLowerCase().includes(q) ||
      e.description.toLowerCase().includes(q)
    );
  });

  function getField<K extends PctField>(entry: BreakoutBibleEntry, key: K, editState: EditState | undefined): string {
    if (editState && key in editState) return editState[key] as string;
    return fmtPct(entry[key]);
  }

  function getDesc(entry: BreakoutBibleEntry, editState: EditState | undefined): string {
    if (editState && 'description' in editState) return editState.description!;
    return entry.description;
  }

  function getNonProv(entry: BreakoutBibleEntry, editState: EditState | undefined): boolean {
    if (editState && 'is_non_prov' in editState) return editState.is_non_prov!;
    return entry.is_non_prov;
  }

  function isDirty(entry: BreakoutBibleEntry): boolean {
    const edit = edits[entry.account_code];
    if (!edit) return false;
    return Object.keys(edit).length > 0;
  }

  async function handleSave(entry: BreakoutBibleEntry) {
    const edit = edits[entry.account_code] ?? {};
    const updated: BreakoutBibleEntry = {
      ...entry,
      description: edit.description ?? entry.description,
      is_non_prov: edit.is_non_prov ?? entry.is_non_prov,
      prov_labour_pct:     parsePct(edit.prov_labour_pct     ?? fmtPct(entry.prov_labour_pct)),
      fed_labour_pct:      parsePct(edit.fed_labour_pct      ?? fmtPct(entry.fed_labour_pct)),
      prov_svc_labour_pct: parsePct(edit.prov_svc_labour_pct ?? fmtPct(entry.prov_svc_labour_pct)),
      svc_property_pct:    parsePct(edit.svc_property_pct    ?? fmtPct(entry.svc_property_pct)),
      fed_svc_labour_pct:  parsePct(edit.fed_svc_labour_pct  ?? fmtPct(entry.fed_svc_labour_pct)),
    };
    setSaving((s) => ({ ...s, [entry.account_code]: true }));
    try {
      const saved = await upsertBreakoutBibleEntry(updated);
      setEntries((prev) => prev.map((e) => e.account_code === entry.account_code ? saved : e));
      setEdits((prev) => { const next = { ...prev }; delete next[entry.account_code]; return next; });
      setSaveStatus((s) => ({ ...s, [entry.account_code]: 'saved' }));
      setTimeout(() => setSaveStatus((s) => { const n = { ...s }; delete n[entry.account_code]; return n; }), 2000);
    } catch {
      setSaveStatus((s) => ({ ...s, [entry.account_code]: 'error' }));
    } finally {
      setSaving((s) => { const n = { ...s }; delete n[entry.account_code]; return n; });
    }
  }

  async function handleReset(entry: BreakoutBibleEntry) {
    setSaving((s) => ({ ...s, [entry.account_code]: true }));
    try {
      await deleteBreakoutBibleEntry(entry.account_code);
      if (entry.is_standard) {
        // Reload so we get the hardcoded defaults back
        const fresh = await getBreakoutBible();
        setEntries(fresh);
      } else {
        setEntries((prev) => prev.filter((e) => e.account_code !== entry.account_code));
      }
      setEdits((prev) => { const n = { ...prev }; delete n[entry.account_code]; return n; });
    } catch {
      setSaveStatus((s) => ({ ...s, [entry.account_code]: 'error' }));
    } finally {
      setSaving((s) => { const n = { ...s }; delete n[entry.account_code]; return n; });
    }
  }

  async function handleAddAccount() {
    const code = newCode.trim();
    if (!code) { setAddError('Account code is required'); return; }
    if (entries.some((e) => e.account_code === code)) {
      setAddError('Account code already exists');
      return;
    }
    setAddError(null);
    setAdding(true);
    const newEntry: BreakoutBibleEntry = {
      account_code: code,
      description: newDesc.trim(),
      is_non_prov: false,
      prov_labour_pct: 0,
      fed_labour_pct: 0,
      prov_svc_labour_pct: 0,
      svc_property_pct: 0,
      fed_svc_labour_pct: 0,
      is_customized: true,
      is_standard: false,
    };
    try {
      const saved = await upsertBreakoutBibleEntry(newEntry);
      setEntries((prev) => [...prev, saved].sort((a, b) => a.account_code.localeCompare(b.account_code)));
      setNewCode('');
      setNewDesc('');
    } catch (e: any) {
      setAddError(e.message || 'Failed to add account');
    } finally {
      setAdding(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-gray-700">Breakout Bible</h3>
        <p className="text-xs text-gray-400 mt-0.5">
          Edit global default percentages for each account code. Changes apply to all new projects.
          Custom accounts (not in the standard bible) can be added below.
        </p>
      </div>

      {/* Add account form */}
      <div className="flex items-end gap-2 p-3 bg-gray-50 border border-gray-200 rounded-lg">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500 font-medium">Account Code</label>
          <input
            value={newCode}
            onChange={(e) => setNewCode(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddAccount()}
            placeholder="e.g. 1234"
            className="w-28 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex flex-col gap-1 flex-1">
          <label className="text-xs text-gray-500 font-medium">Description</label>
          <input
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddAccount()}
            placeholder="Account description"
            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          onClick={handleAddAccount}
          disabled={adding}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm font-medium rounded transition-colors"
        >
          {adding ? 'Adding…' : '+ Add Account'}
        </button>
        {addError && <p className="text-xs text-red-600">{addError}</p>}
      </div>

      {/* Filter */}
      <input
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Filter by code or description…"
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-3 py-2 text-left font-semibold text-gray-600 whitespace-nowrap">Code</th>
              <th className="px-3 py-2 text-left font-semibold text-gray-600">Description</th>
              <th className="px-3 py-2 text-center font-semibold text-gray-600 whitespace-nowrap">OUT</th>
              {PCT_FIELDS.map((f) => (
                <th key={f.key} className="px-3 py-2 text-center font-semibold text-gray-600 whitespace-nowrap">
                  {f.label}
                </th>
              ))}
              <th className="px-3 py-2 text-left font-semibold text-gray-600" />
            </tr>
          </thead>
          <tbody>
            {visibleEntries.map((entry, i) => {
              const edit = edits[entry.account_code];
              const dirty = isDirty(entry);
              const isSaving = saving[entry.account_code];
              const status = saveStatus[entry.account_code];
              return (
                <tr
                  key={entry.account_code}
                  className={`border-b border-gray-100 ${i % 2 === 0 ? 'bg-white' : 'bg-gray-50'} ${dirty ? 'ring-1 ring-inset ring-blue-200' : ''}`}
                >
                  {/* Code */}
                  <td className="px-3 py-1.5 font-mono text-gray-800 whitespace-nowrap">
                    {entry.account_code}
                    {!entry.is_standard && (
                      <span className="ml-1 px-1 py-0.5 text-[10px] bg-purple-100 text-purple-700 rounded">custom</span>
                    )}
                  </td>

                  {/* Description */}
                  <td className="px-3 py-1.5">
                    <input
                      value={getDesc(entry, edit)}
                      onChange={(e) =>
                        setEdits((prev) => ({
                          ...prev,
                          [entry.account_code]: { ...prev[entry.account_code], description: e.target.value },
                        }))
                      }
                      className="w-full min-w-32 px-1.5 py-0.5 border border-gray-200 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
                    />
                  </td>

                  {/* OUT (is_non_prov) checkbox */}
                  <td className="px-3 py-1.5 text-center">
                    <input
                      type="checkbox"
                      checked={getNonProv(entry, edit)}
                      onChange={(e) =>
                        setEdits((prev) => ({
                          ...prev,
                          [entry.account_code]: { ...prev[entry.account_code], is_non_prov: e.target.checked },
                        }))
                      }
                      className="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </td>

                  {/* % fields */}
                  {PCT_FIELDS.map((f) => (
                    <td key={f.key} className="px-2 py-1.5">
                      <input
                        value={getField(entry, f.key, edit)}
                        onChange={(e) =>
                          setEdits((prev) => ({
                            ...prev,
                            [entry.account_code]: { ...prev[entry.account_code], [f.key]: e.target.value },
                          }))
                        }
                        className="w-20 px-1.5 py-0.5 border border-gray-200 rounded text-xs text-right focus:outline-none focus:ring-1 focus:ring-blue-400"
                      />
                    </td>
                  ))}

                  {/* Actions */}
                  <td className="px-3 py-1.5 whitespace-nowrap">
                    <div className="flex items-center gap-1.5">
                      {dirty && (
                        <button
                          onClick={() => handleSave(entry)}
                          disabled={isSaving}
                          className="px-2 py-0.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-xs rounded transition-colors"
                        >
                          {isSaving ? '…' : 'Save'}
                        </button>
                      )}
                      {dirty && (
                        <button
                          onClick={() =>
                            setEdits((prev) => { const n = { ...prev }; delete n[entry.account_code]; return n; })
                          }
                          className="px-2 py-0.5 border border-gray-300 hover:bg-gray-100 text-gray-600 text-xs rounded"
                        >
                          Cancel
                        </button>
                      )}
                      {!dirty && entry.is_customized && (
                        <button
                          onClick={() => handleReset(entry)}
                          disabled={isSaving}
                          className={`px-2 py-0.5 border text-xs rounded transition-colors disabled:opacity-50 ${
                            entry.is_standard
                              ? 'border-orange-300 hover:bg-orange-50 text-orange-600'
                              : 'border-red-300 hover:bg-red-50 text-red-600'
                          }`}
                        >
                          {entry.is_standard ? 'Reset' : 'Delete'}
                        </button>
                      )}
                      {status === 'saved' && (
                        <span className="text-green-600 text-xs">✓</span>
                      )}
                      {status === 'error' && (
                        <span className="text-red-600 text-xs">Error</span>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {visibleEntries.length === 0 && (
          <p className="text-center text-gray-400 text-sm py-6">No entries match your filter.</p>
        )}
      </div>
    </div>
  );
}
