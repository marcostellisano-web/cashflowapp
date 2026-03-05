import type { BibleEntry } from '../types/bible';

const STORAGE_KEY = 'cashflow_custom_bible';

export type CustomBibleEntry = BibleEntry & { is_custom: true };

export function getCustomBibleEntries(): CustomBibleEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as BibleEntry[];
    return parsed.map((e) => ({ ...e, is_custom: true as const }));
  } catch {
    return [];
  }
}

export function saveCustomBibleEntry(entry: BibleEntry): void {
  const entries = getCustomBibleEntries();
  const idx = entries.findIndex((e) => e.account_code === entry.account_code);
  const newEntry: CustomBibleEntry = { ...entry, is_custom: true };
  if (idx >= 0) {
    entries[idx] = newEntry;
  } else {
    entries.push(newEntry);
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
}

export function removeCustomBibleEntry(code: string): void {
  const entries = getCustomBibleEntries().filter((e) => e.account_code !== code);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
}
