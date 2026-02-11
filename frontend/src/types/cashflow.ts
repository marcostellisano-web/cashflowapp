export type CurveType =
  | 'flat'
  | 'bell'
  | 'front_loaded'
  | 'back_loaded'
  | 's_curve'
  | 'shoot_proportional'
  | 'milestone';

export type PhaseAssignment =
  | 'prep'
  | 'production'
  | 'post'
  | 'delivery'
  | 'full_span'
  | 'prep_and_production'
  | 'production_and_post';

export interface LineItemDistribution {
  budget_code: string;
  phase: PhaseAssignment;
  curve: CurveType;
  curve_params?: Record<string, number>;
  milestone_dates?: string[];
  milestone_amounts?: number[];
  auto_assigned: boolean;
}

export interface WeekColumn {
  week_number: number;
  week_commencing: string;
  phase_label: string;
  is_hiatus: boolean;
  shoot_days: number;
}

export interface CashflowRow {
  code: string;
  description: string;
  total: number;
  weekly_amounts: number[];
}

export interface CashflowOutput {
  title: string;
  weeks: WeekColumn[];
  rows: CashflowRow[];
  weekly_totals: number[];
  cumulative_totals: number[];
  grand_total: number;
}
