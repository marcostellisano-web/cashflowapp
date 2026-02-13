import { useState, useEffect } from 'react';
import type { BibleEntry } from '../../types/bible';
import type { ParsedBudget } from '../../types/budget';
import type {
  LineItemDistribution,
  PhaseAssignment,
  CurveType,
} from '../../types/cashflow';
import { getDefaultDistributions, getTimingBible } from '../../lib/api';
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

  // Load bible + defaults on mount
  useEffect(() => {
    // Always load bible for display purposes
    getTimingBible()
      .then((bible) => {
        const map: Record<string, BibleEntry> = {};
        bible.entries.forEach((e) => { map[e.account_code] = e; });
        setBibleMap(map);
      })
      .catch(() => {}); // Bible is optional for display

    if (savedDistributions && savedDistributions.length > 0) return;

    const codes = budget.line_items.map((li) => li.code);
    getDefaultDistributions(codes)
      .then((defaults) => {
        setDistributions(defaults);
      })
      .catch(() => {
        // Fallback: all flat/full_span
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
  }, [budget, savedDistributions]);

  const updateDist = (
    idx: number,
    field: 'phase' | 'curve',
    value: string,
  ) => {
    const updated = [...distributions];
    updated[idx] = {
      ...updated[idx],
      [field]: value,
      auto_assigned: false,
    };
    setDistributions(updated);
  };

  const autoCount = distributions.filter((d) => d.auto_assigned).length;
  const manualCount = distributions.length - autoCount;
  const bibleCount = budget.line_items.filter((li) => bibleMap[li.code]).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
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
                <th className="text-left px-3 py-2 font-medium text-gray-600">
                  Code
                </th>
                <th className="text-left px-3 py-2 font-medium text-gray-600">
                  Description
                </th>
                <th className="text-right px-3 py-2 font-medium text-gray-600">
                  Total
                </th>
                <th className="text-left px-3 py-2 font-medium text-gray-600">
                  Timing
                </th>
                <th className="text-left px-3 py-2 font-medium text-gray-600">
                  Phase / Curve
                </th>
                <th className="text-center px-3 py-2 font-medium text-gray-600">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {budget.line_items.map((item, idx) => {
                const dist = distributions[idx];
                if (!dist) return null;
                const bible = bibleMap[item.code];
                return (
                  <tr
                    key={idx}
                    className={
                      bible
                        ? 'bg-blue-50/50'
                        : dist.auto_assigned
                          ? 'bg-amber-50/50'
                          : 'hover:bg-gray-50'
                    }
                  >
                    <td className="px-3 py-1.5 font-mono text-gray-600 text-xs">
                      {item.code}
                    </td>
                    <td className="px-3 py-1.5 text-gray-900 max-w-48 truncate">
                      {item.description}
                    </td>
                    <td className="px-3 py-1.5 text-right font-mono text-xs">
                      {formatCurrency(item.total)}
                    </td>
                    <td className="px-3 py-1.5">
                      {bible ? (
                        <div>
                          <span className="text-xs font-medium text-blue-700">
                            {bible.timing_title}
                          </span>
                          <p className="text-[10px] text-gray-400 leading-tight mt-0.5 max-w-56 truncate" title={bible.timing_details}>
                            {bible.timing_details}
                          </p>
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400 italic">
                          No bible rule
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-1.5">
                      {bible ? (
                        <span className="text-[10px] text-gray-400 italic">
                          Bible-driven
                        </span>
                      ) : (
                        <div className="flex gap-1">
                          <select
                            value={dist.phase}
                            onChange={(e) =>
                              updateDist(idx, 'phase', e.target.value)
                            }
                            className="w-full border border-gray-300 rounded px-2 py-1 text-xs focus:ring-2 focus:ring-blue-500"
                          >
                            {PHASES.map((p) => (
                              <option key={p.value} value={p.value}>
                                {p.label}
                              </option>
                            ))}
                          </select>
                          <select
                            value={dist.curve}
                            onChange={(e) =>
                              updateDist(idx, 'curve', e.target.value)
                            }
                            className="w-full border border-gray-300 rounded px-2 py-1 text-xs focus:ring-2 focus:ring-blue-500"
                          >
                            {CURVES.map((c) => (
                              <option key={c.value} value={c.value}>
                                {c.label}
                              </option>
                            ))}
                          </select>
                        </div>
                      )}
                    </td>
                    <td className="px-3 py-1.5 text-center">
                      {bible ? (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                          Bible
                        </span>
                      ) : dist.auto_assigned ? (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
                          Auto
                        </span>
                      ) : (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">
                          Manual
                        </span>
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
