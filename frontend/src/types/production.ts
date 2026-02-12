export interface ShootingBlock {
  block_number: number;
  block_type?: string; // e.g. "Doc Shoot", "Recre Shoot"
  episode_numbers: number[];
  shoot_start: string; // ISO date
  shoot_end: string;
  location?: string;
}

export interface EpisodeDelivery {
  episode_number: number;
  picture_lock_date?: string;
  online_date?: string;
  mix_date?: string;
  delivery_date: string;
}

export interface ProductionParameters {
  title: string;
  series_number?: number;
  episode_count: number;
  prep_start: string;
  pp_start: string; // Principal Photography start
  pp_end: string; // Principal Photography end
  edit_start: string; // Edit / post-production start
  shooting_blocks: ShootingBlock[];
  episode_deliveries: EpisodeDelivery[];
  final_delivery_date: string;
  hiatus_periods: [string, string][];
}
