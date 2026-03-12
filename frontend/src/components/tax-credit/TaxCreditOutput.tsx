import { useState } from 'react';
import { generateTaxCreditExcel } from '../../lib/api';
import type { ParsedBudget } from '../../types/budget';
import type { BreakoutOverride } from '../../types/tax_credit';
import BreakoutOverridesEditor from './BreakoutOverridesEditor';
import OntarioTaxCreditTab from './OntarioTaxCreditTab';

type ActiveTab = 'filing' | 'ofttc';

interface TaxCreditOutputProps {
  budget: ParsedBudget;
  onBack: () => void;
}

export default function TaxCreditOutput({ budget, onBack }: TaxCreditOutputProps) {
  const [activeTab, setActiveTab] = useState<ActiveTab>('filing');
  const [title, setTitle] = useState('');
  const [committedTitle, setCommittedTitle] = useState('');
  const [overrides, setOverrides] = useState<BreakoutOverride[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Commit the title (triggers override load) on blur or Enter
  const handleTitleCommit = () => {
    setCommittedTitle(title.trim());
  };

  const handleDownload = async () => {
    setLoading(true);
    setError(null);
    try {
      const blob = await generateTaxCreditExcel(
        budget,
        title || 'Untitled',
        overrides.length > 0 ? overrides : undefined,
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${(title || 'Untitled').replace(/\s+/g, '_')}_tax_credit_budget.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e.message || 'Failed to generate file');
    } finally {
      setLoading(false);
    }
  };

  const tabs: { id: ActiveTab; label: string }[] = [
    { id: 'filing', label: 'Filing Budget' },
    { id: 'ofttc', label: 'Ontario Tax Credit (OFTTC)' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            Tax Credit Filing Budget
          </h2>
          <p className="text-sm text-gray-500">
            Generate a Telefilm-formatted topsheet from your uploaded budget.
          </p>
        </div>
        <button
          onClick={onBack}
          className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
        >
          Back
        </button>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded-lg transition-colors ${
              activeTab === tab.id
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Budget summary (always visible) */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 flex items-center gap-4">
        <div className="w-10 h-10 bg-green-50 rounded-full flex items-center justify-center flex-shrink-0">
          <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <div>
          <p className="text-xs text-gray-400">{budget.source_filename}</p>
          <p className="text-2xl font-bold text-gray-900">
            ${budget.total_budget.toLocaleString('en-US', { maximumFractionDigits: 0 })}
          </p>
          <p className="text-xs text-gray-400">{budget.line_items.length} line items</p>
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Filing Budget tab */}
      {/* ------------------------------------------------------------------ */}
      {activeTab === 'filing' && (
        <>
          {/* Title input */}
          <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-2">
            <h3 className="text-sm font-semibold text-gray-700">Production Title</h3>
            <p className="text-xs text-gray-400">
              Used as the project key — saved overrides will auto-load when you return to this title.
            </p>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={handleTitleCommit}
              onKeyDown={(e) => e.key === 'Enter' && handleTitleCommit()}
              placeholder="Enter production title…"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Breakout overrides editor */}
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <BreakoutOverridesEditor
              budget={budget}
              projectName={committedTitle}
              onChange={setOverrides}
            />
          </div>

          {/* Output description */}
          <div className="bg-blue-50 border border-blue-100 rounded-xl p-5 space-y-2">
            <h3 className="text-sm font-semibold text-blue-800">What you'll get</h3>
            <ul className="text-sm text-blue-700 space-y-1">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full flex-shrink-0" />
                <span>
                  <strong>Topsheet</strong> — Telefilm-standard accounts 01.00–81.00 with aggregated totals
                </span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full flex-shrink-0" />
                <span>
                  <strong>Budget Lines</strong> — Full line-item detail showing each item mapped to its Telefilm category
                </span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full flex-shrink-0" />
                <span>
                  <strong>Breakout Budget</strong> — Tax credit analysis with your adjusted FOR / OUT / labour % values
                </span>
              </li>
            </ul>
          </div>

          {/* Error */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Download button */}
          <div className="flex justify-center pt-2">
            <button
              onClick={handleDownload}
              disabled={loading}
              className="flex items-center gap-3 px-8 py-3.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-semibold rounded-xl shadow-md transition-colors"
            >
              {loading ? (
                <>
                  <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
                  Generating…
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download Tax Credit Budget
                </>
              )}
            </button>
          </div>
        </>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Ontario Tax Credit (OFTTC) tab */}
      {/* ------------------------------------------------------------------ */}
      {activeTab === 'ofttc' && (
        <OntarioTaxCreditTab budget={budget} overrides={overrides} />
      )}
    </div>
  );
}
