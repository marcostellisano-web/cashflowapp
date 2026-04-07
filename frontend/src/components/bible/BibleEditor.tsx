import { useCallback, useEffect, useRef, useState } from 'react';
import {
  createPresetFromEntries,
  deleteBreakoutBibleEntry,
  getBreakoutBible,
  getBreakoutBibleExcelUrl,
  upsertBreakoutBibleEntry,
} from '../../lib/api';
import type { BreakoutBibleEntry } from '../../types/tax_credit';
import BiblePresetSelector from './BiblePresetSelector';

interface BibleEditorProps {
  onBack: () => void;
}

function PctInput({
  value,
  onChange,
}: {
  value: number;
  onChange: (v: number) => void;
}) {
  const [raw, setRaw] = useState(String(Math.round(value * 10000) / 100));

  useEffect(() => {
    setRaw(String(Math.round(value * 10000) / 100));
  }, [value]);

  return (
    <input
      type="number"
      step="0.01"
      min="0"
      max="100"
      value={raw}
      onChange={(e) => setRaw(e.target.value)}
      onBlur={() => {
        const n = parseFloat(raw);
        if (!isNaN(n)) onChange(Math.min(100, Math.max(0, n)) / 100);
        else setRaw(String(Math.round(value * 10000) / 100));
      }}
      className="w-16 text-right text-xs px-1 py-0.5 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-400"
    />
  );
}

export default function BibleEditor({ onBack }: BibleEditorProps) {
  const [entries, setEntries] = useState<BreakoutBibleEntry[]>([]);
  const [dirty, setDirty] = useState<Record<string, BreakoutBibleEntry>>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const saveCountRef = useRef(0);

  // Save-as-preset
  const [showSaveAs, setShowSaveAs] = useState(false);
  const [saveAsName, setSaveAsName] = useState('');
  const [saveAsError, setSaveAsError] = useState<string | null>(null);
  const [saveAsSuccess, setSaveAsSuccess] = useState<string | null>(null);
  const [presetRefreshKey, setPresetRefreshKey] = useState(0);

  // Add account form
  const [newCode, setNewCode] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [addError, setAddError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);

  const loadEntries = useCallback(() => {
    setLoading(true);
    getBreakoutBible()
      .then((data: BreakoutBibleEntry[]) => setEntries(data))
      .catch((e: any) => setSaveError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { loadEntries(); }, [loadEntries]);

  const displayed = entries.filter((e) => {
    if (!filter) return true;
    const q = filter.toLowerCase();
    return (
      e.account_code.toLowerCase().includes(q) ||
      e.description.toLowerCase().includes(q)
    );
  });

  const getEntry = (code: string) =>
    dirty[code] ?? entries.find((e) => e.account_code === code)!;

  const patch = (code: string, updates: Partial<BreakoutBibleEntry>) => {
    const base = getEntry(code);
    setDirty((prev) => ({ ...prev, [code]: { ...base, ...updates } }));
  };

  const handleSaveAsPreset = async () => {
    const name = saveAsName.trim();
    if (!name) { setSaveAsError('Please enter a name for this bible version'); return; }
    setSaving(true);
    setSaveAsError(null);
    setSaveAsSuccess(null);
    const id = ++saveCountRef.current;
    try {
      // Merge dirty changes into the displayed entries to get the full current state
      const allEntries = entries.map((e) =>
        dirty[e.account_code] ? { ...dirty[e.account_code], is_customized: true } : e,
      );
      await createPresetFromEntries(name, allEntries);
      if (id !== saveCountRef.current) return;
      // Apply dirty changes locally and clear
      setEntries(allEntries);
      setDirty({});
      setSaveAsSuccess(`Saved as "${name}". You can activate it from the Bible Presets panel above.`);
      setSaveAsName('');
      setShowSaveAs(false);
      setPresetRefreshKey((k) => k + 1); // triggers BiblePresetSelector to reload its list
    } catch (e: any) {
      if (id === saveCountRef.current) setSaveAsError(e.message || 'Save failed');
    } finally {
      if (id === saveCountRef.current) setSaving(false);
    }
  };

  const handleReset = async (code: string) => {
    setSaveError(null);
    try {
      await deleteBreakoutBibleEntry(code);
      setDirty((prev) => {
        const next = { ...prev };
        delete next[code];
        return next;
      });
      const entry = entries.find((e) => e.account_code === code);
      if (entry?.is_standard) {
        const fresh = await getBreakoutBible();
        setEntries(fresh);
      } else {
        setEntries((prev) => prev.filter((e) => e.account_code !== code));
      }
    } catch (e: any) {
      setSaveError(e.message || 'Reset failed');
    }
  };

  const handleAddAccount = async () => {
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
      setEntries((prev) =>
        [...prev, saved].sort((a, b) => a.account_code.localeCompare(b.account_code)),
      );
      setNewCode('');
      setNewDesc('');
      setShowAddForm(false);
    } catch (e: any) {
      setAddError(e.message || 'Failed to add account');
    } finally {
      setAdding(false);
    }
  };

  const dirtyCount = Object.keys(dirty).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Breakout Bible Editor</h2>
          <p className="text-sm text-gray-500">
            Edit global OUT flags, descriptions, and tax credit percentages. Changes apply to all projects.
          </p>
        </div>
        <button
          onClick={onBack}
          className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
        >
          Back
        </button>
      </div>

      {/* Preset selector */}
      <BiblePresetSelector onBibleChanged={loadEntries} refreshTrigger={presetRefreshKey} />

      {/* ── Toolbar ─────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 flex-wrap">
        <input
          type="text"
          placeholder="Filter by code or description…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 w-64"
        />
        <button
          onClick={() => { setShowAddForm(v => !v); setAddError(null); }}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 transition-colors"
        >
          {showAddForm ? '✕ Cancel' : '+ Add Account'}
        </button>
        <div className="flex-1" />
        <a
          href={getBreakoutBibleExcelUrl()}
          download="breakout_bible.xlsx"
          className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 inline-flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download Excel
        </a>
        <button
          onClick={() => { setShowSaveAs(true); setSaveAsSuccess(null); }}
          disabled={dirtyCount === 0 || saving}
          className="px-5 py-2 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium rounded-lg transition-colors"
        >
          {dirtyCount > 0
            ? `Save ${dirtyCount} change${dirtyCount !== 1 ? 's' : ''}…`
            : 'No changes'}
        </button>
      </div>

      {/* Add account – expandable form */}
      {showAddForm && (
        <div className="flex items-end gap-2 p-3 bg-gray-50 border border-gray-200 rounded-lg flex-wrap">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500 font-medium">Account Code</label>
            <input
              value={newCode}
              onChange={(e) => setNewCode(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && void handleAddAccount()}
              placeholder="e.g. 1234"
              className="w-28 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex flex-col gap-1 flex-1 min-w-40">
            <label className="text-xs text-gray-500 font-medium">Description</label>
            <input
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && void handleAddAccount()}
              placeholder="Account description"
              className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={() => void handleAddAccount()}
            disabled={adding}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm font-medium rounded transition-colors"
          >
            {adding ? 'Adding…' : '+ Add Account'}
          </button>
          {addError && <p className="w-full text-xs text-red-600 mt-1">{addError}</p>}
        </div>
      )}

      {/* Save-as-preset panel */}
      {showSaveAs && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg space-y-2">
          <p className="text-xs text-blue-700 font-medium">
            Save current edits as a new bible version (your active preset will not be changed).
          </p>
          <div className="flex items-center gap-2 flex-wrap">
            <input
              type="text"
              value={saveAsName}
              onChange={(e) => setSaveAsName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && void handleSaveAsPreset()}
              placeholder="e.g. Full Telefilm CoA v2"
              className="flex-1 min-w-48 px-2 py-1.5 border border-blue-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            <button
              onClick={() => void handleSaveAsPreset()}
              disabled={saving}
              className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm font-medium rounded transition-colors"
            >
              {saving ? 'Saving…' : 'Save'}
            </button>
            <button
              onClick={() => { setShowSaveAs(false); setSaveAsError(null); }}
              className="px-3 py-1.5 border border-gray-300 text-gray-600 text-sm rounded hover:bg-white transition-colors"
            >
              Cancel
            </button>
          </div>
          {saveAsError && <p className="text-xs text-red-600">{saveAsError}</p>}
        </div>
      )}

      {saveAsSuccess && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700 flex items-start justify-between gap-2">
          <span>{saveAsSuccess}</span>
          <button onClick={() => setSaveAsSuccess(null)} className="text-green-500 hover:text-green-700 shrink-0">✕</button>
        </div>
      )}

      {saveError && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {saveError}
        </div>
      )}

      {/* ── Accounts table ──────────────────────────────────────────────── */}
      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="overflow-x-auto overflow-y-auto max-h-[calc(100vh-280px)]">
            <table className="w-full text-xs">
              <thead className="sticky top-0 z-10">
                <tr className="bg-gray-50 border-b border-gray-200 text-gray-600 uppercase tracking-wide">
                  <th className="text-left px-4 py-3 font-semibold w-24">Account</th>
                  <th className="text-left px-3 py-3 font-semibold">Description</th>
                  <th className="text-center px-3 py-3 font-semibold w-16">OUT</th>
                  <th className="text-center px-3 py-3 font-semibold">Prov Labour %</th>
                  <th className="text-center px-3 py-3 font-semibold">Fed Labour %</th>
                  <th className="text-center px-3 py-3 font-semibold">Prov Svc %</th>
                  <th className="text-center px-3 py-3 font-semibold">Svc Prop %</th>
                  <th className="text-center px-3 py-3 font-semibold">Fed Svc %</th>
                  <th className="text-center px-3 py-3 font-semibold w-20">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {displayed.map((baseEntry) => {
                  const e = getEntry(baseEntry.account_code);
                  const isDirty = !!dirty[e.account_code];
                  const rowBg = isDirty
                    ? 'bg-yellow-50'
                    : e.is_customized
                    ? 'bg-blue-50/40'
                    : e.is_from_preset
                    ? 'bg-green-50/50'
                    : '';
                  return (
                    <tr
                      key={e.account_code}
                      className={`${rowBg} hover:bg-gray-50 transition-colors`}
                    >
                      <td className="px-4 py-2 font-mono font-semibold text-gray-800 whitespace-nowrap">
                        {e.account_code}
                        {!e.is_standard && (
                          <span className="ml-1.5 text-[10px] font-normal px-1 py-0.5 rounded bg-purple-100 text-purple-700">
                            custom
                          </span>
                        )}
                        {isDirty && (
                          <span className="ml-1.5 text-[10px] font-normal px-1 py-0.5 rounded bg-yellow-200 text-yellow-800">
                            edited
                          </span>
                        )}
                        {!isDirty && e.is_customized && e.is_standard && (
                          <span className="ml-1.5 text-[10px] font-normal px-1 py-0.5 rounded bg-blue-100 text-blue-700">
                            custom
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        <input
                          type="text"
                          value={e.description}
                          onChange={(ev) => patch(e.account_code, { description: ev.target.value })}
                          placeholder="—"
                          className="w-full min-w-32 px-1.5 py-0.5 border border-gray-200 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
                        />
                      </td>
                      <td className="px-3 py-2 text-center">
                        <input
                          type="checkbox"
                          checked={e.is_non_prov}
                          onChange={(ev) => patch(e.account_code, { is_non_prov: ev.target.checked })}
                          className="w-4 h-4 accent-red-500"
                        />
                      </td>
                      <td className="px-3 py-2 text-center">
                        <PctInput
                          value={e.prov_labour_pct}
                          onChange={(v) => patch(e.account_code, { prov_labour_pct: v })}
                        />
                      </td>
                      <td className="px-3 py-2 text-center">
                        <PctInput
                          value={e.fed_labour_pct}
                          onChange={(v) => patch(e.account_code, { fed_labour_pct: v })}
                        />
                      </td>
                      <td className="px-3 py-2 text-center">
                        <PctInput
                          value={e.prov_svc_labour_pct}
                          onChange={(v) => patch(e.account_code, { prov_svc_labour_pct: v })}
                        />
                      </td>
                      <td className="px-3 py-2 text-center">
                        <PctInput
                          value={e.svc_property_pct}
                          onChange={(v) => patch(e.account_code, { svc_property_pct: v })}
                        />
                      </td>
                      <td className="px-3 py-2 text-center">
                        <PctInput
                          value={e.fed_svc_labour_pct}
                          onChange={(v) => patch(e.account_code, { fed_svc_labour_pct: v })}
                        />
                      </td>
                      <td className="px-3 py-2 text-center whitespace-nowrap">
                        {e.is_customized && !isDirty && (
                          <button
                            onClick={() => void handleReset(e.account_code)}
                            className={`text-xs hover:underline ${
                              e.is_standard
                                ? 'text-orange-500 hover:text-orange-700'
                                : 'text-red-500 hover:text-red-700'
                            }`}
                          >
                            {e.is_standard ? 'Reset' : 'Delete'}
                          </button>
                        )}
                        {isDirty && (
                          <button
                            onClick={() =>
                              setDirty((prev) => {
                                const next = { ...prev };
                                delete next[e.account_code];
                                return next;
                              })
                            }
                            className="text-xs text-gray-500 hover:text-gray-700 hover:underline"
                          >
                            Undo
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-2 border-t border-gray-100 text-xs text-gray-400 flex items-center gap-4">
            <span>{displayed.length} accounts shown</span>
            <span className="inline-flex items-center gap-1.5">
              <span className="w-3 h-3 bg-green-100 rounded-sm inline-block border border-green-200" /> From active preset
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="w-3 h-3 bg-blue-100 rounded-sm inline-block border border-blue-200" /> Manual override
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="w-3 h-3 bg-yellow-100 rounded-sm inline-block border border-yellow-200" /> Unsaved edit
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
