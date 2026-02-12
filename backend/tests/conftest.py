import pytest
from datetime import date

from app.models.budget import BudgetCategory, BudgetLineItem, ParsedBudget
from app.models.production import (
    EpisodeDelivery,
    ProductionParameters,
    ShootingBlock,
)


@pytest.fixture
def sample_budget() -> ParsedBudget:
    return ParsedBudget(
        line_items=[
            BudgetLineItem(code="1100", description="Executive Producer", total=200000, category=BudgetCategory.ABOVE_THE_LINE),
            BudgetLineItem(code="1200", description="Director", total=150000, category=BudgetCategory.ABOVE_THE_LINE),
            BudgetLineItem(code="1300", description="Cast", total=500000, category=BudgetCategory.ABOVE_THE_LINE),
            BudgetLineItem(code="2100", description="Camera Department", total=120000, category=BudgetCategory.BELOW_THE_LINE_PRODUCTION),
            BudgetLineItem(code="2200", description="Electrical / Grip", total=80000, category=BudgetCategory.BELOW_THE_LINE_PRODUCTION),
            BudgetLineItem(code="2300", description="Art Department", total=200000, category=BudgetCategory.BELOW_THE_LINE_PRODUCTION),
            BudgetLineItem(code="3000", description="Locations", total=100000, category=BudgetCategory.BELOW_THE_LINE_PRODUCTION),
            BudgetLineItem(code="4000", description="Editing", total=90000, category=BudgetCategory.BELOW_THE_LINE_POST),
            BudgetLineItem(code="4100", description="VFX", total=150000, category=BudgetCategory.BELOW_THE_LINE_POST),
            BudgetLineItem(code="5000", description="Insurance", total=60000, category=BudgetCategory.OTHER),
        ],
        total_budget=1650000,
        source_filename="test_budget.xlsx",
        warnings=[],
    )


@pytest.fixture
def sample_params() -> ProductionParameters:
    return ProductionParameters(
        title="Test Show",
        series_number=1,
        episode_count=4,
        prep_start=date(2025, 1, 6),
        pp_start=date(2025, 2, 17),
        pp_end=date(2025, 4, 25),
        edit_start=date(2025, 4, 28),
        shooting_blocks=[
            ShootingBlock(
                block_number=1,
                block_type="Shoot",
                episode_numbers=[1, 2],
                shoot_start=date(2025, 2, 17),
                shoot_end=date(2025, 3, 21),
            ),
            ShootingBlock(
                block_number=2,
                block_type="Shoot",
                episode_numbers=[3, 4],
                shoot_start=date(2025, 3, 24),
                shoot_end=date(2025, 4, 25),
            ),
        ],
        episode_deliveries=[
            EpisodeDelivery(episode_number=1, picture_lock_date=date(2025, 5, 5), delivery_date=date(2025, 6, 6)),
            EpisodeDelivery(episode_number=2, picture_lock_date=date(2025, 5, 12), delivery_date=date(2025, 6, 13)),
            EpisodeDelivery(episode_number=3, picture_lock_date=date(2025, 5, 19), delivery_date=date(2025, 6, 20)),
            EpisodeDelivery(episode_number=4, picture_lock_date=date(2025, 5, 26), delivery_date=date(2025, 6, 27)),
        ],
        final_delivery_date=date(2025, 6, 27),
        hiatus_periods=[],
    )
