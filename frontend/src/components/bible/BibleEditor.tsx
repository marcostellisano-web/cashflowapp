import { useEffect, useRef, useState } from 'react';
import {
  applyTemplateToGlobalBible,
  deleteBreakoutBibleEntry,
  deleteBreakoutTemplate,
  getBreakoutBible,
  getBreakoutBibleExcelUrl,
  getBreakoutTemplateExcelUrl,
  listBreakoutTemplates,
  saveBibleAsTemplate,
  uploadBreakoutTemplate,
  upsertBreakoutBibleEntry,
} from '../../lib/api';
import type { BreakoutBibleEntry } from '../../types/tax_credit';

const BUILTIN_TEMPLATE = 'Nat Geo - 4 Episode';

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

  // Add account form
  const [newCode, setNewCode] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [addError, setAddError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  // Templates state
  const [templates, setTemplates] = useState<string[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(true);
  const [applyingTemplate, setApplyingTemplate] = useState<string | null>(null);
  const [deletingTemplate, setDeletingTemplate] = useState<string | null>(null);
  const [templateError, setTemplateError] = useState<string | null>(null);
  const [saveAsName, setSaveAsName] = useState('');
  const [savingAsTemplate, setSavingAsTemplate] = useState(false);
  const [saveAsError, setSaveAsError] = useState<string | null>(null);
  const [saveAsMessage, setSaveAsMessage] = useState<string | null>(null);
  const [uploadName, setUploadName] = useState('');
  const [templateUploading, setTemplateUploading] = useState(false);
  const [templateUploadError, setTemplateUploadError] = useState<string | null>(null);
  const [templateUploadMessage, setTemplateUploadMessage] = useState<string | null>(null);
  const [showUploadForm, setShowUploadForm] = useState(false);

  useEffect(() => {
    getBreakoutBible()
      .then((data: BreakoutBibleEntry[]) => setEntries(data))
      .catch((e: any) => setSaveError(e.message))
      .finally(() => setLoading(false));

    listBreakoutTemplates()
      .then(setTemplates)
      .catch(() => {})
      .finally(() => setTemplatesLoading(false));
  }, []);

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

  const handleSaveAll = async () => {
    const toSave = Object.values(dirty);
    if (toSave.length === 0) return;
    setSaving(true);
    setSaveError(null);
    const id = ++saveCountRef.current;
    try {
      await Promise.all(toSave.map((e) => upsertBreakoutBibleEntry(e)));
      if (id !== saveCountRef.current) return;
      setEntries((prev) =>
        prev.map((e) =>
          dirty[e.account_code]
            ? { ...dirty[e.account_code], is_customized: true }
            : e,
        ),
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
    } catch (e: any) {
      setAddError(e.message || 'Failed to add account');
    } finally {
      setAdding(false);
    }
  };

  const handleApplyTemplate = async (name: string) => {
    const isBuiltin = name === BUILTIN_TEMPLATE;
    const msg = isBuiltin
      ? `Apply the "${name}" template? This will reset all bible customisations to the default values.`
      : `Apply the "${name}" template? This will overwrite the current global bible with this template's values.`;
    if (!window.confirm(msg)) return;
    setTemplateError(null);
    setApplyingTemplate(name);
    try {
      const fresh = await applyTemplateToGlobalBible(name);
      setEntries(fresh);
      setDirty({});
    } catch (e: any) {
      setTemplateError(e.message || 'Failed to apply template');
    } finally {
      setApplyingTemplate(null);
    }
  };

  const handleDeleteTemplate = async (name: string) => {
    if (!window.confirm(`Delete template "${name}"? This cannot be undone.`)) return;
    setTemplateError(null);
    setDeletingTemplate(name);
    try {
      await deleteBreakoutTemplate(name);
      setTemplates((prev) => prev.filter((t) => t !== name));
    } catch (e: any) {
      setTemplateError(e.message || 'Failed to delete template');
    } finally {
      setDeletingTemplate(null);
    }
  };

  const handleSaveAsTemplate = async () => {
    const name = saveAsName.trim();
    if (!name) { setSaveAsError('Template name is required'); return; }
    if (name === BUILTIN_TEMPLATE) { setSaveAsError(`"${BUILTIN_TEMPLATE}" is a built-in template and cannot be overwritten.`); return; }
    setSaveAsError(null);
    setSaveAsMessage(null);
    setSavingAsTemplate(true);
    try {
      await saveBibleAsTemplate(name);
      setSaveAsMessage(`Saved as "${name}".`);
      setSaveAsName('');
      if (!templates.includes(name)) setTemplates((prev) => [...prev, name].sort());
    } catch (e: any) {
      setSaveAsError(e.message || 'Failed to save template');
    } finally {
      setSavingAsTemplate(false);
    }
  };

  const handleTemplateUpload = async (file: File) => {
    const name = uploadName.trim();
    if (!name) { setTemplateUploadError('Template name is required before upload.'); return; }
    if (name === BUILTIN_TEMPLATE) { setTemplateUploadError(`"${BUILTIN_TEMPLATE}" is a built-in template and cannot be overwritten.`); return; }
    setTemplateUploading(true);
    setTemplateUploadError(null);
    setTemplateUploadMessage(null);
    try {
      const resp = await uploadBreakoutTemplate(name, file);
      setTemplateUploadMessage(`Template "${name}" uploaded (${resp.overrides.length} rows).`);
      if (!templates.includes(name)) setTemplates((prev) => [...prev, name].sort());
    } catch (e: any) {
      setTemplateUploadError(e.message || 'Template upload failed');
    } finally {
      setTemplateUploading(false);
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

      {/* ── Bible Templates ─────────────────────────────────────────────── */}
      <div className="border border-gray-200 rounded-xl overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-gray-800">Bible Templates</h3>
            <p className="text-xs text-gray-500 mt-0.5">
              Apply a template to load a complete set of bible values into the global bible.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowUploadForm((v) => !v)}
              className="text-xs px-2.5 py-1.5 border border-gray-300 rounded hover:bg-gray-100 text-gray-600"
            >
              {showUploadForm ? 'Hide Upload' : 'Upload Template Excel'}
            </button>
          </div>
        </div>

        {templateError && (
          <div className="px-4 py-2 bg-red-50 border-b border-red-200 text-xs text-red-700">
            {templateError}
          </div>
        )}

        {/* Template list */}
        <div className="divide-y divide-gray-100">
          {/* Built-in template */}
          <div className="flex items-center gap-3 px-4 py-3 bg-white">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-800">{BUILTIN_TEMPLATE}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-indigo-100 text-indigo-700 font-medium">
                  built-in
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">Default BREAKOUT_BIBLE values — applies when no customisations are saved.</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <a
                href={getBreakoutBibleExcelUrl()}
                download="breakout_bible.xlsx"
                className="text-xs px-2.5 py-1.5 border border-gray-200 rounded hover:bg-gray-50 text-gray-600 inline-flex items-center gap-1"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Excel
              </a>
              <button
                onClick={() => void handleApplyTemplate(BUILTIN_TEMPLATE)}
                disabled={applyingTemplate === BUILTIN_TEMPLATE}
                className="text-xs px-2.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white rounded font-medium"
              >
                {applyingTemplate === BUILTIN_TEMPLATE ? 'Applying…' : 'Apply'}
              </button>
            </div>
          </div>

          {/* User-created templates */}
          {templatesLoading ? (
            <div className="px-4 py-3 text-xs text-gray-400">Loading templates…</div>
          ) : templates.length === 0 ? (
            <div className="px-4 py-3 text-xs text-gray-400">No saved templates yet.</div>
          ) : (
            templates.map((name) => (
              <div key={name} className="flex items-center gap-3 px-4 py-3 bg-white">
                <div className="flex-1 min-w-0">
                  <span className="text-sm font-medium text-gray-800">{name}</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <a
                    href={getBreakoutTemplateExcelUrl(name)}
                    download={`template_${name}.xlsx`}
                    className="text-xs px-2.5 py-1.5 border border-gray-200 rounded hover:bg-gray-50 text-gray-600 inline-flex items-center gap-1"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Excel
                  </a>
                  <button
                    onClick={() => void handleApplyTemplate(name)}
                    disabled={applyingTemplate === name}
                    className="text-xs px-2.5 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded font-medium"
                  >
                    {applyingTemplate === name ? 'Applying…' : 'Apply'}
                  </button>
                  <button
                    onClick={() => void handleDeleteTemplate(name)}
                    disabled={deletingTemplate === name}
                    className="text-xs px-2.5 py-1.5 border border-red-200 text-red-600 hover:bg-red-50 rounded"
                  >
                    {deletingTemplate === name ? '…' : 'Delete'}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Save current bible as template */}
        <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
          <p className="text-xs text-gray-500 mb-2 font-medium">Save current global bible as a new template</p>
          <div className="flex items-center gap-2 flex-wrap">
            <input
              value={saveAsName}
              onChange={(e) => setSaveAsName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && void handleSaveAsTemplate()}
              placeholder="Template name…"
              className="flex-1 min-w-40 px-2.5 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={() => void handleSaveAsTemplate()}
              disabled={savingAsTemplate}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm font-medium rounded"
            >
              {savingAsTemplate ? 'Saving…' : 'Save as Template'}
            </button>
          </div>
          {saveAsError && <p className="text-xs text-red-600 mt-1">{saveAsError}</p>}
          {saveAsMessage && <p className="text-xs text-green-700 mt-1">{saveAsMessage}</p>}
        </div>

        {/* Upload template form (collapsible) */}
        {showUploadForm && (
          <div className="px-4 py-3 bg-blue-50 border-t border-blue-200">
            <p className="text-xs text-blue-700 mb-2">
              Upload an Excel file to create/update a template. Required columns:
              <strong> Account, Description, OUT, Prov Labour %, Fed Labour %, Prov Svc %, Svc Prop %, Fed Svc %</strong>
            </p>
            <div className="flex items-end gap-2 flex-wrap">
              <div className="flex flex-col gap-1">
                <label className="text-xs text-blue-700 font-medium">Template Name</label>
                <input
                  value={uploadName}
                  onChange={(e) => setUploadName(e.target.value)}
                  placeholder="e.g. Crime Shows"
                  className="w-56 px-2 py-1.5 border border-blue-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <label className={`px-3 py-1.5 rounded text-sm font-medium border ${templateUploading ? 'border-gray-300 text-gray-400 bg-gray-100' : 'border-blue-300 text-blue-700 hover:bg-blue-100'} cursor-pointer`}>
                {templateUploading ? 'Uploading…' : 'Choose Excel File'}
                <input
                  type="file"
                  accept=".xlsx,.xlsm"
                  disabled={templateUploading}
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) void handleTemplateUpload(file);
                    e.currentTarget.value = '';
                  }}
                />
              </label>
            </div>
            {templateUploadMessage && <p className="text-xs text-green-700 mt-1">{templateUploadMessage}</p>}
            {templateUploadError && <p className="text-xs text-red-700 mt-1">{templateUploadError}</p>}
          </div>
        )}
      </div>

      {/* ── Add account ─────────────────────────────────────────────────── */}
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

      {/* ── Toolbar ─────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 flex-wrap">
        <input
          type="text"
          placeholder="Filter by code or description…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 w-64"
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
          onClick={() => void handleSaveAll()}
          disabled={dirtyCount === 0 || saving}
          className="px-5 py-2 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium rounded-lg transition-colors"
        >
          {saving
            ? 'Saving…'
            : dirtyCount > 0
            ? `Save ${dirtyCount} change${dirtyCount !== 1 ? 's' : ''}`
            : 'No changes'}
        </button>
      </div>

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
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
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
              <span className="w-3 h-3 bg-blue-100 rounded-sm inline-block border border-blue-200" /> Customized
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
