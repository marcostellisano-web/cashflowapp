from datetime import date

from pydantic import BaseModel


class ShootingBlock(BaseModel):
    """A block of episodes shot together."""

    block_number: int
    block_type: str | None = None  # e.g. "Doc Shoot", "Recre Shoot"
    episode_numbers: list[int]
    shoot_start: date
    shoot_end: date
    location: str | None = None


class EpisodeDelivery(BaseModel):
    """Post-production milestones for a single episode."""

    episode_number: int
    picture_lock_date: date | None = None
    online_date: date | None = None
    mix_date: date | None = None
    delivery_date: date


class ProductionParameters(BaseModel):
    """All production scheduling parameters."""

    title: str
    series_number: int | None = None
    episode_count: int
    prep_start: date
    pp_start: date  # Principal Photography start
    pp_end: date  # Principal Photography end
    edit_start: date  # Edit / post-production start
    shooting_blocks: list[ShootingBlock]
    episode_deliveries: list[EpisodeDelivery]
    final_delivery_date: date
    hiatus_periods: list[tuple[date, date]] = []
