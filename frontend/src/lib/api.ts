import type { TimingBible } from '../types/bible';
import type { ParsedBudget } from '../types/budget';
import type { CashflowOutput, LineItemDistribution } from '../types/cashflow';
import type { ProductionParameters } from '../types/production';

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

export async function getTimingBible(): Promise<TimingBible> {
  const res = await fetch(`${BASE}/bible`);
  if (!res.ok) throw new Error('Failed to get timing bible');
  return res.json();
}
