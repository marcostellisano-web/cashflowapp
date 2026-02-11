from datetime import date

from pydantic import BaseModel


class ShootingBlock(BaseModel):
    """A block of episodes shot together."""

    block_number: int
    episode_numbers: list[int]
    shoot_start: date
    shoot_end: date
    location: str | None = None


class EpisodeDelivery(BaseModel):
    """Post-production milestones for a single episode."""

    episode_number: int
    rough_cut_date: date | None = None
    fine_cut_date: date | None = None
    picture_lock_date: date | None = None
    online_date: date | None = None
    delivery_date: date


class ProductionParameters(BaseModel):
    """All production scheduling parameters."""

    title: str
    series_number: int | None = None
    episode_count: int
    prep_start: date
    prep_end: date
    wrap_date: date
    shooting_blocks: list[ShootingBlock]
    episode_deliveries: list[EpisodeDelivery]
    post_start: date | None = None
    final_delivery_date: date
    hiatus_periods: list[tuple[date, date]] = []
