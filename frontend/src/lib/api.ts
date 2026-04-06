import type { TimingBible } from '../types/bible';
import type { ParsedBudget } from '../types/budget';
import type { CashflowOutput, LineItemDistribution } from '../types/cashflow';
import type { ProductionParameters } from '../types/production';
import type { BiblePreset, BreakoutBibleEntry, BreakoutOverride, ProjectOverridesResponse } from '../types/tax_credit';

const BASE = '/api';

export async function uploadBudget(file: File): Promise<ParsedBudget> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/upload`, { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function getDefaultDistributions(
  codes: string[],
): Promise<LineItemDistribution[]> {
  const params = new URLSearchParams();
  codes.forEach((c) => params.append('codes', c));
  const res = await fetch(`${BASE}/defaults/distributions?${params}`);
  if (!res.ok) throw new Error('Failed to get defaults');
  return res.json();
}

export async function previewCashflow(
  budget: ParsedBudget,
  parameters: ProductionParameters,
  distributions: LineItemDistribution[],
): Promise<CashflowOutput> {
  const res = await fetch(`${BASE}/cashflow/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ budget, parameters, distributions }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Preview failed');
  }
  return res.json();
}

export async function generateCashflowExcel(
  budget: ParsedBudget,
  parameters: ProductionParameters,
  distributions: LineItemDistribution[],
): Promise<Blob> {
  const res = await fetch(`${BASE}/cashflow/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ budget, parameters, distributions }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Generation failed');
  }
  return res.blob();
}

export async function listCashflowTemplates(): Promise<string[]> {
  const res = await fetch(`${BASE}/cashflow/templates`);
  if (!res.ok) throw new Error('Failed to list cashflow templates');
  return res.json();
}

export async function getCashflowTemplate(
  templateName: string,
  codes: string[],
): Promise<LineItemDistribution[]> {
  const params = new URLSearchParams();
  codes.forEach((c) => params.append('codes', c));
  const res = await fetch(
    `${BASE}/cashflow/templates/${encodeURIComponent(templateName)}?${params}`,
  );
  if (!res.ok) throw new Error('Failed to load cashflow template');
  return res.json();
}

export async function saveCashflowTemplate(
  templateName: string,
  distributions: LineItemDistribution[],
): Promise<LineItemDistribution[]> {
  const res = await fetch(`${BASE}/cashflow/templates/${encodeURIComponent(templateName)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(distributions),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to save cashflow template');
  }
  return res.json();
}

export function getCashflowTemplateExcelUrl(templateName: string): string {
  return `${BASE}/cashflow/templates/${encodeURIComponent(templateName)}/excel`;
}

export async function uploadCashflowTemplate(
  templateName: string,
  file: File,
): Promise<LineItemDistribution[]> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/cashflow/templates/${encodeURIComponent(templateName)}/upload`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to upload cashflow template');
  }
  return res.json();
}

export async function getTimingBible(): Promise<TimingBible> {
  const res = await fetch(`${BASE}/bible`);
  if (!res.ok) throw new Error('Failed to get timing bible');
  return res.json();
}

export async function uploadParameters(file: File): Promise<ProductionParameters> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/upload/parameters`, { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to parse parameters file');
  }
  return res.json();
}

export function getParametersTemplateUrl(): string {
  return `${BASE}/upload/parameters/template`;
}

export async function getCustomBible(): Promise<import('../types/bible').BibleEntry[]> {
  const res = await fetch(`${BASE}/bible/custom`);
  if (!res.ok) throw new Error('Failed to get custom bible');
  return res.json();
}

export async function upsertCustomBibleEntry(
  entry: import('../types/bible').BibleEntry,
): Promise<import('../types/bible').BibleEntry> {
  const res = await fetch(`${BASE}/bible/custom/${encodeURIComponent(entry.account_code)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to save custom bible entry');
  }
  return res.json();
}

export async function deleteCustomBibleEntry(code: string): Promise<void> {
  const res = await fetch(`${BASE}/bible/custom/${encodeURIComponent(code)}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to delete custom bible entry');
  }
}

export async function generateTaxCreditExcel(
  budget: ParsedBudget,
  title: string,
  overrides?: BreakoutOverride[],
): Promise<Blob> {
  const res = await fetch(`${BASE}/tax-credit/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ budget, title, overrides: overrides ?? null }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Generation failed');
  }
  return res.blob();
}

export function getBreakoutBibleExcelUrl(): string {
  return `${BASE}/tax-credit/bible/excel`;
}

export async function getBreakoutOverrides(
  projectName: string,
  accountCodes: string[],
  descriptions: string[],
): Promise<ProjectOverridesResponse> {
  const params = new URLSearchParams();
  accountCodes.forEach((c) => params.append('account_codes', c));
  descriptions.forEach((d) => params.append('descriptions', d));
  const res = await fetch(
    `${BASE}/tax-credit/overrides/${encodeURIComponent(projectName)}?${params}`,
  );
  if (!res.ok) throw new Error('Failed to load overrides');
  return res.json();
}

export async function getBreakoutBible(): Promise<BreakoutBibleEntry[]> {
  const res = await fetch(`${BASE}/tax-credit/bible`);
  if (!res.ok) throw new Error('Failed to load breakout bible');
  return res.json();
}

export async function upsertBreakoutBibleEntry(
  entry: BreakoutBibleEntry,
): Promise<BreakoutBibleEntry> {
  const res = await fetch(
    `${BASE}/tax-credit/bible/${encodeURIComponent(entry.account_code)}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entry),
    },
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to save bible entry');
  }
  return res.json();
}

export async function deleteBreakoutBibleEntry(accountCode: string): Promise<void> {
  const res = await fetch(
    `${BASE}/tax-credit/bible/${encodeURIComponent(accountCode)}`,
    { method: 'DELETE' },
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to delete bible entry');
  }
}

export async function createPresetFromEntries(
  name: string,
  entries: BreakoutBibleEntry[],
): Promise<{ preset_id: number; name: string; entry_count: number }> {
  const res = await fetch(`${BASE}/tax-credit/bible/presets/from-entries`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, entries }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to save preset');
  }
  return res.json();
}

export async function getBiblePresets(): Promise<BiblePreset[]> {
  const res = await fetch(`${BASE}/tax-credit/bible/presets`);
  if (!res.ok) throw new Error('Failed to load bible presets');
  return res.json();
}

export async function uploadBiblePreset(file: File, name: string): Promise<{ preset_id: number; name: string; entry_count: number }> {
  const form = new FormData();
  form.append('file', file);
  form.append('name', name);
  const res = await fetch(`${BASE}/tax-credit/bible/presets/upload`, { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function activateBiblePreset(id: number): Promise<BiblePreset> {
  const res = await fetch(`${BASE}/tax-credit/bible/presets/${id}/activate`, { method: 'PUT' });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to activate preset');
  }
  return res.json();
}

export async function deactivateBiblePreset(id: number): Promise<BiblePreset> {
  const res = await fetch(`${BASE}/tax-credit/bible/presets/${id}/deactivate`, { method: 'DELETE' });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to deactivate preset');
  }
  return res.json();
}

export async function deleteBiblePreset(id: number): Promise<void> {
  const res = await fetch(`${BASE}/tax-credit/bible/presets/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to delete preset');
  }
}

export async function saveBreakoutOverrides(
  projectName: string,
  overrides: BreakoutOverride[],
): Promise<ProjectOverridesResponse> {
  const res = await fetch(
    `${BASE}/tax-credit/overrides/${encodeURIComponent(projectName)}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ overrides }),
    },
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to save overrides');
  }
  return res.json();
}

export async function listBreakoutTemplates(): Promise<string[]> {
  const res = await fetch(`${BASE}/tax-credit/templates`);
  if (!res.ok) throw new Error('Failed to load templates');
  return res.json();
}

export async function getBreakoutTemplateOverrides(
  templateName: string,
  accountCodes: string[],
  descriptions: string[],
): Promise<ProjectOverridesResponse> {
  const params = new URLSearchParams();
  accountCodes.forEach((c) => params.append('account_codes', c));
  descriptions.forEach((d) => params.append('descriptions', d));
  const res = await fetch(
    `${BASE}/tax-credit/templates/${encodeURIComponent(templateName)}?${params}`,
  );
  if (!res.ok) throw new Error('Failed to load template');
  return res.json();
}

export async function saveBreakoutTemplateOverrides(
  templateName: string,
  overrides: BreakoutOverride[],
): Promise<ProjectOverridesResponse> {
  const res = await fetch(
    `${BASE}/tax-credit/templates/${encodeURIComponent(templateName)}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ overrides }),
    },
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to save template');
  }
  return res.json();
}

export function getBreakoutTemplateExcelUrl(templateName: string): string {
  return `${BASE}/tax-credit/templates/${encodeURIComponent(templateName)}/excel`;
}

export async function deleteBreakoutTemplate(templateName: string): Promise<void> {
  const res = await fetch(
    `${BASE}/tax-credit/templates/${encodeURIComponent(templateName)}`,
    { method: 'DELETE' },
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to delete template');
  }
}

export async function applyTemplateToGlobalBible(templateName: string): Promise<BreakoutBibleEntry[]> {
  const res = await fetch(
    `${BASE}/tax-credit/bible/apply-template/${encodeURIComponent(templateName)}`,
    { method: 'POST' },
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to apply template');
  }
  return res.json();
}

export async function saveBibleAsTemplate(templateName: string): Promise<ProjectOverridesResponse> {
  const res = await fetch(
    `${BASE}/tax-credit/bible/save-as-template/${encodeURIComponent(templateName)}`,
    { method: 'POST' },
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to save as template');
  }
  return res.json();
}

export async function uploadBreakoutTemplate(templateName: string, file: File): Promise<ProjectOverridesResponse> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(
    `${BASE}/tax-credit/templates/${encodeURIComponent(templateName)}/upload`,
    { method: 'POST', body: form },
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to upload template');
  }
  return res.json();
}
