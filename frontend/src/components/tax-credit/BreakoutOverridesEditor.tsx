import { useEffect, useRef, useState } from 'react';
import { getBreakoutTemplateOverrides, saveBreakoutTemplateOverrides } from '../../lib/api';
import type { ParsedBudget } from '../../types/budget';
import type { BreakoutOverride } from '../../types/tax_credit';

interface Props {
  budget: ParsedBudget;
  templateName: string;
  onChange: (overrides: BreakoutOverride[]) => void;
}

type PctField =
  | 'fed_labour_pct'
  | 'fed_svc_labour_pct'
  | 'prov_labour_pct'
  | 'prov_svc_labour_pct'
  | 'svc_property_pct';

const PCT_FIELDS: { key: PctField; label: string }[] = [
  { key: 'fed_labour_pct',       label: 'Fed Labour %' },
  { key: 'fed_svc_labour_pct',   label: 'Fed Svc Labour %' },
  { key: 'prov_labour_pct',      label: 'Prov Labour %' },
  { key: 'prov_svc_labour_pct',  label: 'Prov Svc Labour %' },
  { key: 'svc_property_pct',     label: 'Svc Property %' },
];

/** Format a nullable float as a percentage string for display (e.g. 0.65 → "65%") */
function fmtPct(v: number | null): string {
  if (v === null || v === undefined) return '';
  return `${Math.round(v * 10000) / 100}%`;
}

/** Parse a user-typed percentage string back to a 0–1 float, or null if empty/invalid */
function parsePct(s: string): number | null {
  const trimmed = s.trim().replace('%', '');
  if (trimmed === '' || trimmed === '-') return null;
  const n = parseFloat(trimmed);
  if (isNaN(n)) return null;
  // Accept values entered as decimals (0.65) or as percentages (65)
  return n > 1 ? n / 100 : n;
}

export default function BreakoutOverridesEditor({ budget, templateName, onChange }: Props) {
  const [overrides, setOverrides] = useState<BreakoutOverride[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saved' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);

  // Derive unique account codes + descriptions from the budget
  const accountEntries = useRef<{ code: string; description: string }[]>([]);
  useEffect(() => {
    const seen = new Set<string>();
    const entries: { code: string; description: string }[] = [];
    for (const item of budget.line_items) {
      const code = item.code?.toString().trim() ?? '';
      if (code && !seen.has(code)) {
        seen.add(code);
        entries.push({ code, description: item.description ?? '' });
      }
    }
    accountEntries.current = entries;
  }, [budget]);

  // Load overrides whenever templateName becomes non-empty
  useEffect(() => {
    if (!templateName.trim()) return;
    const entries = accountEntries.current;
    if (!entries.length) return;

    setLoading(true);
    setError(null);
    getBreakoutTemplateOverrides(
      templateName,
      entries.map((e) => e.code),
      entries.map((e) => e.description),
    )
      .then((resp) => {
        setOverrides(resp.overrides);
        onChange(resp.overrides);
      })
      .catch((e) => setError(e.message || 'Failed to load overrides'))
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [templateName]);

  const handleBoolToggle = (code: string, field: 'is_foreign' | 'is_non_prov', checked: boolean) => {
    setOverrides((prev) =>
      prev.map((ov) =>
        ov.account_code === code ? { ...ov, [field]: checked } : ov,
      ),
    );
    setSaveStatus('idle');
  };

  const handlePctChange = (code: string, field: PctField, raw: string) => {
    const value = parsePct(raw);
    setOverrides((prev) =>
      prev.map((ov) =>
        ov.account_code === code ? { ...ov, [field]: value } : ov,
      ),
    );
    setSaveStatus('idle');
  };

  const handleSave = async () => {
    if (!templateName.trim()) return;
    setSaving(true);
    setSaveStatus('idle');
    try {
      await saveBreakoutTemplateOverrides(templateName, overrides);
      onChange(overrides);
      setSaveStatus('saved');
    } catch (e: any) {
      setSaveStatus('error');
      setError(e.message || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  if (!templateName.trim()) {
    return (
      <p className="text-sm text-gray-400 italic">
        Select or create a template above to load and edit breakout parameters.
      </p>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500 py-4">
        <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full" />
        Loading parameters…
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
        {error}
      </div>
    );
  }

  if (!overrides.length) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-700">Breakout Parameters</h3>
          <p className="text-xs text-gray-400">
            Override bible defaults per account code. Checkboxes force FOR / OUT flags; leave % fields blank to use the bible default.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {saveStatus === 'saved' && (
            <span className="text-xs text-green-600 font-medium">Saved</span>
          )}
          {saveStatus === 'error' && (
            <span className="text-xs text-red-600 font-medium">Save failed</span>
          )}
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium rounded-lg transition-colors"
          >
            {saving ? (
              <>
                <div className="animate-spin h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full" />
                Saving…
              </>
            ) : (
              'Save Overrides'
            )}
          </button>
        </div>
      </div>

      {/* Scrollable table */}
      <div className="overflow-x-auto overflow-y-auto max-h-[60vh] rounded-xl border border-gray-200">
        <table className="min-w-full text-xs">
          <thead className="sticky top-0 z-20">
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="sticky left-0 z-30 bg-gray-50 px-3 py-2.5 text-left font-semibold text-gray-600 whitespace-nowrap">
                Account
              </th>
              <th className="bg-gray-50 px-3 py-2.5 text-left font-semibold text-gray-600 whitespace-nowrap min-w-[160px]">
                Description
              </th>
              <th className="bg-gray-50 px-3 py-2.5 text-center font-semibold text-gray-600 whitespace-nowrap">
                FOR
              </th>
              <th className="bg-gray-50 px-3 py-2.5 text-center font-semibold text-gray-600 whitespace-nowrap">
                OUT
              </th>
              {PCT_FIELDS.map((f) => (
                <th
                  key={f.key}
                  className="bg-gray-50 px-3 py-2.5 text-center font-semibold text-gray-600 whitespace-nowrap"
                >
                  {f.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {overrides.map((ov, idx) => (
              <tr key={ov.account_code} className={`transition-colors ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'} hover:bg-blue-50`}>
                {/* Account code */}
                <td className={`sticky left-0 z-10 px-3 py-2 font-mono text-gray-800 whitespace-nowrap ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                  {ov.account_code}
                </td>
                {/* Description */}
                <td className="px-3 py-2 text-gray-600 max-w-[200px] truncate" title={ov.description}>
                  {ov.description}
                </td>
                {/* FOR checkbox */}
                <td className="px-3 py-2 text-center">
                  <input
                    type="checkbox"
                    checked={ov.is_foreign === true}
                    onChange={(e) =>
                      handleBoolToggle(ov.account_code, 'is_foreign', e.target.checked)
                    }
                    className="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    title={
                      ov.is_foreign === null
                        ? 'Auto (currency-based)'
                        : ov.is_foreign
                        ? 'Forced: FOR'
                        : 'Forced: not foreign'
                    }
                  />
                </td>
                {/* OUT checkbox */}
                <td className="px-3 py-2 text-center">
                  <input
                    type="checkbox"
                    checked={ov.is_non_prov === true}
                    onChange={(e) =>
                      handleBoolToggle(ov.account_code, 'is_non_prov', e.target.checked)
                    }
                    className="h-3.5 w-3.5 rounded border-gray-300 text-orange-500 focus:ring-orange-400"
                  />
                </td>
                {/* Percentage fields */}
                {PCT_FIELDS.map((f) => (
                  <td key={f.key} className="px-2 py-1.5 text-center">
                    <input
                      type="text"
                      defaultValue={fmtPct(ov[f.key])}
                      key={`${ov.account_code}-${f.key}-${ov[f.key]}`}
                      onBlur={(e) => handlePctChange(ov.account_code, f.key, e.target.value)}
                      placeholder="—"
                      className="w-16 text-center text-xs px-1.5 py-1 border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-blue-400 focus:border-blue-400 bg-white"
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
