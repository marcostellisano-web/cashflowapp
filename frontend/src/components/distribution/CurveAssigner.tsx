import { useState, useEffect, useMemo } from 'react';
import type { BibleEntry } from '../../types/bible';
import type { BudgetLineItem, ParsedBudget } from '../../types/budget';
import type {
  LineItemDistribution,
  PhaseAssignment,
  CurveType,
} from '../../types/cashflow';
import {
  getDefaultDistributions,
  getTimingBible,
  getCustomBible,
  upsertCustomBibleEntry,
  deleteCustomBibleEntry,
} from '../../lib/api';
import { formatCurrency } from '../../lib/utils';

const PHASES: { value: PhaseAssignment; label: string }[] = [
  { value: 'prep', label: 'Pre-Production' },
  { value: 'production', label: 'Production' },
  { value: 'post', label: 'Post-Production' },
  { value: 'delivery', label: 'Delivery' },
  { value: 'full_span', label: 'Full Span' },
  { value: 'prep_and_production', label: 'Prep + Production' },
  { value: 'production_and_post', label: 'Production + Post' },
];

const CURVES: { value: CurveType; label: string }[] = [
  { value: 'flat', label: 'Flat (Even)' },
  { value: 'bell', label: 'Bell Curve' },
  { value: 'front_loaded', label: 'Front-loaded' },
  { value: 'back_loaded', label: 'Back-loaded' },
  { value: 's_curve', label: 'S-Curve' },
  { value: 'shoot_proportional', label: 'Shoot Proportional' },
  { value: 'milestone', label: 'Milestone' },
];

interface CurveAssignerProps {
  budget: ParsedBudget;
  savedDistributions?: LineItemDistribution[];
  onSubmit: (distributions: LineItemDistribution[]) => void;
  onBack: () => void;
}

export default function CurveAssigner({
  budget,
  savedDistributions,
  onSubmit,
  onBack,
}: CurveAssignerProps) {
  const [distributions, setDistributions] = useState<LineItemDistribution[]>(
    savedDistributions && savedDistributions.length > 0 ? savedDistributions : [],
  );
  const [bibleMap, setBibleMap] = useState<Record<string, BibleEntry>>({});
  const [loading, setLoading] = useState(
    !savedDistributions || savedDistributions.length === 0,
  );
  const [patternModeRows, setPatternModeRows] = useState<Set<string>>(new Set());
  const [savingCode, setSavingCode] = useState<string | null>(null);
  const [savedToast, setSavedToast] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Load official bible + custom bible + default distributions on mount
  useEffect(() => {
    const codes = budget.line_items.map((li) => li.code);

    // Fetch official bible and custom entries in parallel
    Promise.all([
      getTimingBible().catch(() => ({ entries: [] })),
      getCustomBible().catch(() => [] as BibleEntry[]),
    ]).then(([officialBible, customEntries]) => {
      const map: Record<string, BibleEntry> = {};
      officialBible.entries.forEach((e) => { map[e.account_code] = e; });
      // Custom entries override official ones for the same code
      customEntries.forEach((e) => { map[e.account_code] = { ...e, is_custom: true }; });
      setBibleMap(map);

      if (savedDistributions && savedDistributions.length > 0) {
        setLoading(false);
        return;
      }

      // Build a quick lookup to auto-apply custom timing overrides to distributions
      const customMap: Record<string, string> = {};
      customEntries.forEach((e) => { customMap[e.account_code] = e.timing_pattern; });

      getDefaultDistributions(codes)
        .then((defaults) => {
          const updated = defaults.map((d) => {
            if (customMap[d.budget_code]) {
              return {
                ...d,
                timing_pattern_override: customMap[d.budget_code],
                auto_assigned: false,
              };
            }
            return d;
          });
          setDistributions(updated);
        })
        .catch(() => {
          setDistributions(
            codes.map((code) => ({
              budget_code: code,
              phase: 'full_span' as PhaseAssignment,
              curve: 'flat' as CurveType,
              auto_assigned: true,
            })),
          );
        })
        .finally(() => setLoading(false));
    });
  }, [budget, savedDistributions]);

  // Unique timing options derived from the full bible (for override dropdowns)
  const timingOptions = useMemo(() => {
    const seen = new Set<string>();
    const options: { pattern: string; title: string; details: string }[] = [];
    Object.values(bibleMap).forEach((entry) => {
      if (!seen.has(entry.timing_pattern)) {
        seen.add(entry.timing_pattern);
        options.push({
          pattern: entry.timing_pattern,
          title: entry.timing_title,
          details: entry.timing_details,
        });
      }
    });
    return options.sort((a, b) => a.title.localeCompare(b.title));
  }, [bibleMap]);

  // Map from timing_pattern → timing_title for the Timing column display
  const patternTitles = useMemo(() => {
    const map: Record<string, string> = {};
    Object.values(bibleMap).forEach((e) => { map[e.timing_pattern] = e.timing_title; });
    return map;
  }, [bibleMap]);

  const updateDist = (
    idx: number,
    field: 'phase' | 'curve' | 'timing_pattern_override',
    value: string,
  ) => {
    const updated = [...distributions];
    updated[idx] = { ...updated[idx], [field]: value, auto_assigned: false };
    setDistributions(updated);
  };

  const enterPatternMode = (code: string) => {
    setPatternModeRows((prev) => new Set(prev).add(code));
  };

  const exitPatternMode = (idx: number, code: string) => {
    setPatternModeRows((prev) => {
      const next = new Set(prev);
      next.delete(code);
      return next;
    });
    setDistributions((prev) => {
      const updated = [...prev];
      if (updated[idx]) {
        updated[idx] = { ...updated[idx], timing_pattern_override: undefined };
      }
      return updated;
    });
  };

  const saveToBible = async (item: BudgetLineItem, dist: LineItemDistribution) => {
    if (!dist.timing_pattern_override) return;
    const pattern = dist.timing_pattern_override;
    const optionInfo = timingOptions.find((o) => o.pattern === pattern);
    const entry: BibleEntry = {
      account_code: item.code,
      description: item.description,
      timing_pattern: pattern,
      timing_title: optionInfo?.title ?? pattern,
      timing_details: optionInfo?.details ?? '',
      is_custom: true,
    };

    setSavingCode(item.code);
    setSaveError(null);
    try {
      await upsertCustomBibleEntry(entry);
      // Update live bibleMap so the row immediately renders as a custom entry
      setBibleMap((prev) => ({ ...prev, [item.code]: entry }));
      setPatternModeRows((prev) => {
        const next = new Set(prev);
        next.delete(item.code);
        return next;
      });
      setSavedToast(item.code);
      setTimeout(() => setSavedToast(null), 2500);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to save');
      setTimeout(() => setSaveError(null), 4000);
    } finally {
      setSavingCode(null);
    }
  };

  const removeFromBible = async (code: string) => {
    try {
      await deleteCustomBibleEntry(code);
      setBibleMap((prev) => {
        const next = { ...prev };
        delete next[code];
        return next;
      });
      setDistributions((prev) =>
        prev.map((d) =>
          d.budget_code === code
            ? { ...d, timing_pattern_override: undefined, auto_assigned: true }
            : d,
        ),
      );
    } catch {
      // Silently ignore — entry remains until page reload
    }
  };

  const autoCount = distributions.filter((d) => d.auto_assigned).length;
  const manualCount = distributions.length - autoCount;
  const bibleCount = budget.line_items.filter(
    (li) => bibleMap[li.code] && !bibleMap[li.code].is_custom,
  ).length;
  const customCount = budget.line_items.filter(
    (li) => bibleMap[li.code]?.is_custom,
  ).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Toasts */}
      {savedToast && (
        <div className="fixed top-4 right-4 z-50 bg-teal-600 text-white px-4 py-2 rounded-lg shadow-lg text-sm font-medium">
          Code {savedToast} saved to Bible
        </div>
      )}
      {saveError && (
        <div className="fixed top-4 right-4 z-50 bg-red-600 text-white px-4 py-2 rounded-lg shadow-lg text-sm font-medium">
          {saveError}
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            Distribution Configuration
          </h2>
          <p className="text-sm text-gray-500">
            Assign spend phases and curves to each budget line.{' '}
            {bibleCount > 0 && (
              <>
                <span className="text-blue-600 font-medium">
                  {bibleCount} bible-driven
                </span>
                {', '}
              </>
            )}
            {customCount > 0 && (
              <>
                <span className="text-teal-600 font-medium">
                  {customCount} custom
                </span>
                {', '}
              </>
            )}
            <span className="font-medium">{manualCount} manual</span>,{' '}
            <span className="text-amber-600 font-medium">
              {autoCount} auto-assigned
            </span>
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={onBack}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
          >
            Back
          </button>
          <button
            onClick={() => onSubmit(distributions)}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Next: Preview
          </button>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto max-h-[500px]">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="text-left px-3 py-2 font-medium text-gray-600">Code</th>
                <th className="text-left px-3 py-2 font-medium text-gray-600">Description</th>
                <th className="text-right px-3 py-2 font-medium text-gray-600">Total</th>
                <th className="text-left px-3 py-2 font-medium text-gray-600">Timing</th>
                <th className="text-left px-3 py-2 font-medium text-gray-600">Phase / Curve</th>
                <th className="text-center px-3 py-2 font-medium text-gray-600">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {budget.line_items.map((item, idx) => {
                const dist = distributions[idx];
                if (!dist) return null;

                const bible = bibleMap[item.code];
                const isCustomBible = !!bible?.is_custom;
                const isOverridden =
                  !isCustomBible &&
                  !!bible &&
                  !dist.auto_assigned &&
                  !!dist.timing_pattern_override &&
                  dist.timing_pattern_override !== bible.timing_pattern;
                const effectivePattern =
                  dist.timing_pattern_override ?? bible?.timing_pattern;
                const effectiveTitle = effectivePattern
                  ? (patternTitles[effectivePattern] ?? bible?.timing_title)
                  : undefined;
                const isInPatternMode =
                  !bible &&
                  (patternModeRows.has(item.code) || !!dist.timing_pattern_override);
                const isSavingThis = savingCode === item.code;

                return (
                  <tr
                    key={idx}
                    className={
                      isOverridden
                        ? 'bg-purple-50/50'
                        : isCustomBible
                          ? 'bg-teal-50/50'
                          : bible
                            ? 'bg-blue-50/50'
                            : isInPatternMode
                              ? 'bg-orange-50/30'
                              : dist.auto_assigned
                                ? 'bg-amber-50/50'
                                : 'hover:bg-gray-50'
                    }
                  >
                    <td className="px-3 py-1.5 font-mono text-gray-600 text-xs">{item.code}</td>
                    <td className="px-3 py-1.5 text-gray-900 max-w-48 truncate">{item.description}</td>
                    <td className="px-3 py-1.5 text-right font-mono text-xs">{formatCurrency(item.total)}</td>

                    {/* Timing column */}
                    <td className="px-3 py-1.5">
                      {bible ? (
                        <div>
                          <span
                            className={`text-xs font-medium ${
                              isOverridden
                                ? 'text-purple-700'
                                : isCustomBible
                                  ? 'text-teal-700'
                                  : 'text-blue-700'
                            }`}
                          >
                            {effectiveTitle ?? bible.timing_title}
                          </span>
                          {isOverridden &&
                            dist.timing_pattern_override !== bible.timing_pattern && (
                              <p className="text-[10px] text-purple-400 leading-tight mt-0.5">
                                was: {bible.timing_title}
                              </p>
                            )}
                          {isCustomBible && (
                            <button
                              onClick={() => removeFromBible(item.code)}
                              className="block text-[10px] text-teal-500 hover:text-red-500 leading-tight mt-0.5"
                              title="Remove this code from the custom bible"
                            >
                              Remove from Bible
                            </button>
                          )}
                        </div>
                      ) : isInPatternMode ? (
                        <span
                          className={`text-xs font-medium ${
                            effectivePattern ? 'text-orange-700' : 'text-gray-400 italic'
                          }`}
                        >
                          {effectiveTitle ?? 'Select pattern…'}
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400 italic">No bible rule</span>
                      )}
                    </td>

                    {/* Phase / Curve column */}
                    <td className="px-3 py-1.5">
                      {bible ? (
                        <select
                          value={dist.timing_pattern_override ?? bible.timing_pattern}
                          onChange={(e) =>
                            updateDist(idx, 'timing_pattern_override', e.target.value)
                          }
                          className="w-full border border-gray-300 rounded px-2 py-1 text-xs focus:ring-2 focus:ring-blue-500"
                        >
                          {timingOptions.map((opt) => (
                            <option key={opt.pattern} value={opt.pattern}>
                              {opt.title}
                            </option>
                          ))}
                        </select>
                      ) : isInPatternMode ? (
                        <div className="space-y-1">
                          <select
                            value={dist.timing_pattern_override ?? ''}
                            onChange={(e) =>
                              updateDist(idx, 'timing_pattern_override', e.target.value)
                            }
                            className="w-full border border-orange-300 rounded px-2 py-1 text-xs focus:ring-2 focus:ring-orange-400"
                          >
                            <option value="">Select timing pattern…</option>
                            {timingOptions.map((opt) => (
                              <option key={opt.pattern} value={opt.pattern}>
                                {opt.title}
                              </option>
                            ))}
                          </select>
                          <div className="flex gap-1">
                            <button
                              onClick={() => saveToBible(item, dist)}
                              disabled={!dist.timing_pattern_override || isSavingThis}
                              className="flex-1 text-[11px] px-2 py-1 bg-teal-600 text-white rounded hover:bg-teal-700 disabled:opacity-40 disabled:cursor-not-allowed font-medium"
                              title="Save this code → timing pattern to the Bible for all future sessions"
                            >
                              {isSavingThis ? 'Saving…' : 'Save to Bible'}
                            </button>
                            <button
                              onClick={() => exitPatternMode(idx, item.code)}
                              className="text-[11px] px-2 py-1 border border-gray-300 rounded hover:bg-gray-100 text-gray-500"
                              title="Cancel and go back to phase/curve"
                            >
                              ✕
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div>
                          <div className="flex gap-1">
                            <select
                              value={dist.phase}
                              onChange={(e) => updateDist(idx, 'phase', e.target.value)}
                              className="w-full border border-gray-300 rounded px-2 py-1 text-xs focus:ring-2 focus:ring-blue-500"
                            >
                              {PHASES.map((p) => (
                                <option key={p.value} value={p.value}>{p.label}</option>
                              ))}
                            </select>
                            <select
                              value={dist.curve}
                              onChange={(e) => updateDist(idx, 'curve', e.target.value)}
                              className="w-full border border-gray-300 rounded px-2 py-1 text-xs focus:ring-2 focus:ring-blue-500"
                            >
                              {CURVES.map((c) => (
                                <option key={c.value} value={c.value}>{c.label}</option>
                              ))}
                            </select>
                          </div>
                          <button
                            onClick={() => enterPatternMode(item.code)}
                            className="text-[10px] text-teal-600 hover:text-teal-800 mt-0.5 block"
                            title="Assign a bible timing pattern to this code"
                          >
                            → Assign timing pattern
                          </button>
                        </div>
                      )}
                    </td>

                    {/* Status column */}
                    <td className="px-3 py-1.5 text-center">
                      {isOverridden ? (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">Override</span>
                      ) : isCustomBible ? (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-teal-100 text-teal-700">Custom</span>
                      ) : bible ? (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">Bible</span>
                      ) : dist.auto_assigned ? (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">Auto</span>
                      ) : (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">Manual</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
