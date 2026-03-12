import { useEffect, useRef, useState } from 'react';
import {
  getBreakoutBibleEntries,
  getBreakoutBibleExcelUrl,
  resetBreakoutBibleEntry,
  updateBreakoutBibleEntry,
} from '../../lib/api';
import type { BibleEntry } from '../../types/tax_credit';

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
  const [entries, setEntries] = useState<BibleEntry[]>([]);
  const [dirty, setDirty] = useState<Record<string, BibleEntry>>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const saveCountRef = useRef(0);

  useEffect(() => {
    getBreakoutBibleEntries()
      .then((data) => setEntries(data))
      .catch((e) => setSaveError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const displayed = entries.filter(
    (e) =>
      !filter ||
      e.account_code.toLowerCase().includes(filter.toLowerCase()),
  );

  const getEntry = (code: string) => dirty[code] ?? entries.find((e) => e.account_code === code)!;

  const patch = (code: string, updates: Partial<BibleEntry>) => {
    const base = getEntry(code);
    setDirty((prev) => ({ ...prev, [code]: { ...base, ...updates } }));
  };

  const handleSaveAll = async () => {
    const toSave = Object.values(dirty);
    if (toSave.length === 0) return;
    setSaving(true);
    setSaveError(null);
    const id = ++saveCountRef.current;
    try {
      await Promise.all(toSave.map((e) => updateBreakoutBibleEntry(e)));
      if (id !== saveCountRef.current) return;
      // Merge saved changes back into entries
      setEntries((prev) =>
        prev.map((e) => (dirty[e.account_code] ? { ...dirty[e.account_code], is_customized: true } : e)),
      );
      setDirty({});
    } catch (e: any) {
      if (id === saveCountRef.current) setSaveError(e.message || 'Save failed');
    } finally {
      if (id === saveCountRef.current) setSaving(false);
    }
  };

  const handleReset = async (code: string) => {
    setSaveError(null);
    try {
      await resetBreakoutBibleEntry(code);
      // Remove dirty state and mark as not-customized
      setDirty((prev) => {
        const next = { ...prev };
        delete next[code];
        return next;
      });
      setEntries((prev) =>
        prev.map((e) =>
          e.account_code === code ? { ...e, is_customized: false } : e,
        ),
      );
    } catch (e: any) {
      setSaveError(e.message || 'Reset failed');
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
            Edit global OUT flags and tax credit percentages for all 210 accounts.
          </p>
        </div>
        <button
          onClick={onBack}
          className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
        >
          Back
        </button>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-3 flex-wrap">
        <input
          type="text"
          placeholder="Filter by account code…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 w-56"
        />
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
          onClick={handleSaveAll}
          disabled={dirtyCount === 0 || saving}
          className="px-5 py-2 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium rounded-lg transition-colors"
        >
          {saving ? 'Saving…' : dirtyCount > 0 ? `Save ${dirtyCount} change${dirtyCount !== 1 ? 's' : ''}` : 'No changes'}
        </button>
      </div>

      {saveError && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {saveError}
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-gray-600 uppercase tracking-wide">
                  <th className="text-left px-4 py-3 font-semibold w-24">Account</th>
                  <th className="text-center px-3 py-3 font-semibold w-16">OUT</th>
                  <th className="text-center px-3 py-3 font-semibold">Prov Labour %</th>
                  <th className="text-center px-3 py-3 font-semibold">Fed Labour %</th>
                  <th className="text-center px-3 py-3 font-semibold">Prov Svc %</th>
                  <th className="text-center px-3 py-3 font-semibold">Svc Prop %</th>
                  <th className="text-center px-3 py-3 font-semibold">Fed Svc %</th>
                  <th className="text-center px-3 py-3 font-semibold w-20">Reset</th>
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
                    : '';
                  return (
                    <tr key={e.account_code} className={`${rowBg} hover:bg-gray-50 transition-colors`}>
                      <td className="px-4 py-2 font-mono font-semibold text-gray-800">
                        {e.account_code}
                        {(isDirty || e.is_customized) && (
                          <span className={`ml-1.5 text-[10px] font-normal px-1 py-0.5 rounded ${isDirty ? 'bg-yellow-200 text-yellow-800' : 'bg-blue-100 text-blue-700'}`}>
                            {isDirty ? 'edited' : 'custom'}
                          </span>
                        )}
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
                      <td className="px-3 py-2 text-center">
                        {e.is_customized && !isDirty && (
                          <button
                            onClick={() => handleReset(e.account_code)}
                            className="text-xs text-red-500 hover:text-red-700 hover:underline"
                          >
                            Reset
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
            <span className="inline-flex items-center gap-1.5"><span className="w-3 h-3 bg-blue-100 rounded-sm inline-block border border-blue-200" /> Customized</span>
            <span className="inline-flex items-center gap-1.5"><span className="w-3 h-3 bg-yellow-100 rounded-sm inline-block border border-yellow-200" /> Unsaved edit</span>
          </div>
        </div>
      )}
    </div>
  );
}
