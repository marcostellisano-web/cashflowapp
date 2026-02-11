export interface ShootingBlock {
  block_number: number;
  episode_numbers: number[];
  shoot_start: string; // ISO date
  shoot_end: string;
  location?: string;
}

export interface EpisodeDelivery {
  episode_number: number;
  rough_cut_date?: string;
  fine_cut_date?: string;
  picture_lock_date?: string;
  online_date?: string;
  delivery_date: string;
}

export interface ProductionParameters {
  title: string;
  series_number?: number;
  episode_count: number;
  prep_start: string;
  prep_end: string;
  wrap_date: string;
  shooting_blocks: ShootingBlock[];
  episode_deliveries: EpisodeDelivery[];
  post_start?: string;
  final_delivery_date: string;
  hiatus_periods: [string, string][];
}
