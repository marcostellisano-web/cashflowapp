export interface BibleEntry {
  account_code: string;
  description: string;
  timing_pattern: string;
  timing_details: string;
  timing_title: string;
}

export interface TimingBible {
  entries: BibleEntry[];
}
