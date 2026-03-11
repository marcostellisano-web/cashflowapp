export interface BreakoutOverride {
  account_code: string;
  description: string;
  /** null = use currency-based formula; true = always FOR; false = never FOR */
  is_foreign: boolean | null;
  /** null = use bible default; true = force OUT; false = force not-OUT */
  is_non_prov: boolean | null;
  fed_labour_pct: number | null;
  fed_svc_labour_pct: number | null;
  prov_labour_pct: number | null;
  prov_svc_labour_pct: number | null;
  svc_property_pct: number | null;
}

export interface ProjectOverridesResponse {
  project_name: string;
  overrides: BreakoutOverride[];
}
