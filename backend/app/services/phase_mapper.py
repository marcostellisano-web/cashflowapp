"""Map budget codes to default phase/curve assignments."""

from app.domain.budget_categories import get_default_for_code
from app.models.distribution import CurveType, LineItemDistribution, PhaseAssignment


def get_default_distributions(codes: list[str]) -> list[LineItemDistribution]:
    """Return default LineItemDistribution for a list of budget codes.

    All returned distributions are marked as auto_assigned=True.
    """
    results = []
    for code in codes:
        phase, curve = get_default_for_code(code)
        results.append(
            LineItemDistribution(
                budget_code=code,
                phase=phase,
                curve=curve,
                auto_assigned=True,
            )
        )
    return results


def merge_distributions(
    budget_codes: list[str],
    user_distributions: list[LineItemDistribution],
) -> list[LineItemDistribution]:
    """Merge user-provided distributions with auto-assigned defaults.

    User distributions take precedence. Any budget codes not covered by the user
    get auto-assigned defaults.

    Returns the complete list of distributions (one per budget code).
    """
    user_map = {d.budget_code: d for d in user_distributions}
    merged = []

    for code in budget_codes:
        if code in user_map:
            dist = user_map[code]
            # Ensure user-provided ones are not marked auto
            dist.auto_assigned = False
            merged.append(dist)
        else:
            phase, curve = get_default_for_code(code)
            merged.append(
                LineItemDistribution(
                    budget_code=code,
                    phase=phase,
                    curve=curve,
                    auto_assigned=True,
                )
            )

    return merged
