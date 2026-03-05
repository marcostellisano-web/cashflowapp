export interface BibleEntry {
  account_code: string;
  description: string;
  timing_pattern: string;
  timing_details: string;
  timing_title: string;
  is_custom?: boolean;
}

export interface TimingBible {
  entries: BibleEntry[];
}
