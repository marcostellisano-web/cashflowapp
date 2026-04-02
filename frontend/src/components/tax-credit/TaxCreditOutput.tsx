import { useEffect, useState } from 'react';
import {
  generateTaxCreditExcel,
  getBreakoutTemplateExcelUrl,
  listBreakoutTemplates,
  uploadBreakoutTemplate,
} from '../../lib/api';
import type { ParsedBudget } from '../../types/budget';
import type { BreakoutOverride } from '../../types/tax_credit';
import BibleEditor from './BibleEditor';
import BreakoutOverridesEditor from './BreakoutOverridesEditor';

type Tab = 'project' | 'bible';

interface TaxCreditOutputProps {
  budget: ParsedBudget;
  onBack: () => void;
}

export default function TaxCreditOutput({ budget, onBack }: TaxCreditOutputProps) {
  const [tab, setTab] = useState<Tab>('project');
  const [title, setTitle] = useState('');
  const [templates, setTemplates] = useState<string[]>([]);
  const [templateName, setTemplateName] = useState('');
  const [newTemplateName, setNewTemplateName] = useState('');
  const [overrides, setOverrides] = useState<BreakoutOverride[]>([]);
  const [loading, setLoading] = useState(false);
  const [templateBusy, setTemplateBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [templateError, setTemplateError] = useState<string | null>(null);

  useEffect(() => {
    listBreakoutTemplates()
      .then(setTemplates)
      .catch(() => setTemplates([]));
  }, []);

  const handleCreateTemplate = () => {
    const name = newTemplateName.trim();
    if (!name) return;
    if (!templates.includes(name)) setTemplates((prev) => [...prev, name].sort());
    setTemplateName(name);
    setNewTemplateName('');
  };

  const handleUploadTemplate = async (file: File) => {
    const name = templateName.trim();
    if (!name) {
      setTemplateError('Select or create a template first.');
      return;
    }
    setTemplateBusy(true);
    setTemplateError(null);
    try {
      await uploadBreakoutTemplate(name, file);
    } catch (e: any) {
      setTemplateError(e.message || 'Failed to upload template');
    } finally {
      setTemplateBusy(false);
    }
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

      {/* Budget summary */}
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

      {/* Title input */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-2">
        <h3 className="text-sm font-semibold text-gray-700">Production Title</h3>
        <p className="text-xs text-gray-400">
          Used only for the generated file name.
        </p>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Enter production title…"
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-3">
        <h3 className="text-sm font-semibold text-gray-700">Breakout Template</h3>
        <p className="text-xs text-gray-400">
          Choose a reusable template (e.g., Crime, Disaster). Each template can be edited, saved, downloaded, and uploaded.
        </p>
        <div className="flex flex-wrap items-end gap-2">
          <div className="min-w-56">
            <label className="text-xs text-gray-500 font-medium">Existing templates</label>
            <select
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">Select template…</option>
              {templates.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 font-medium">New template</label>
            <input
              value={newTemplateName}
              onChange={(e) => setNewTemplateName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreateTemplate()}
              placeholder="e.g. Crime Shows"
              className="mt-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
          <button
            onClick={handleCreateTemplate}
            className="px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
          >
            Create / Select
          </button>
          <a
            href={templateName ? getBreakoutTemplateExcelUrl(templateName) : undefined}
            className={`px-3 py-2 text-sm rounded-lg border ${templateName ? 'border-gray-300 hover:bg-gray-50 text-gray-700' : 'border-gray-200 text-gray-300 pointer-events-none'}`}
          >
            Download Template
          </a>
          <label className={`px-3 py-2 text-sm rounded-lg border ${templateBusy ? 'border-gray-200 text-gray-300' : 'border-gray-300 hover:bg-gray-50 text-gray-700'} cursor-pointer`}>
            Upload Template
            <input
              type="file"
              accept=".xlsx,.xlsm"
              disabled={templateBusy}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) void handleUploadTemplate(file);
                e.currentTarget.value = '';
              }}
              className="hidden"
            />
          </label>
        </div>
        {templateError && <p className="text-xs text-red-600">{templateError}</p>}
      </div>

      {/* Tabs: Project Overrides | Bible Editor */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setTab('project')}
            className={`px-5 py-3 text-sm font-medium transition-colors ${
              tab === 'project'
                ? 'border-b-2 border-blue-600 text-blue-700 bg-white'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
          >
            Project Overrides
          </button>
          <button
            onClick={() => setTab('bible')}
            className={`px-5 py-3 text-sm font-medium transition-colors ${
              tab === 'bible'
                ? 'border-b-2 border-blue-600 text-blue-700 bg-white'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
          >
            Bible Editor
          </button>
        </div>
        <div className="p-6">
          {tab === 'project' && (
            <BreakoutOverridesEditor
              budget={budget}
              templateName={templateName}
              onChange={setOverrides}
            />
          )}
          {tab === 'bible' && <BibleEditor />}
        </div>
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
          <li className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full flex-shrink-0" />
            <span>
              <strong>Ontario – OFTTC</strong> — Ontario Full Tax Credit calculation sheet
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
    </div>
  );
}
