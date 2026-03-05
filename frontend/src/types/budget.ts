export interface BudgetLineItem {
  code: string;
  description: string;
  total: number;
  category: string | null;
  account_group: string | null;
}

export interface ParsedBudget {
  line_items: BudgetLineItem[];
  total_budget: number;
  source_filename: string;
  warnings: string[];
  topsheet_totals: Record<string, number>;
}
