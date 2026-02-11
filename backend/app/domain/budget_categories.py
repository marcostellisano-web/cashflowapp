"""Default Movie Magic Budgeting code prefix → phase/curve mappings.

Movie Magic uses a standard numbering scheme:
  1000-1999: Above the Line (Producers, Directors, Writers, Cast)
  2000-2999: Below the Line Production (Crew, Equipment, Locations)
  3000-3999: Below the Line Production continued (Art, Construction, Wardrobe)
  4000-4999: Post-Production (Edit, VFX, Sound, Music, Lab)
  5000-5999: Other (Insurance, Legal, Finance, Overheads)
"""

from app.models.distribution import CurveType, PhaseAssignment

# Maps 2-digit code prefix to (phase, curve) defaults.
# Used as fallback when the user has not manually assigned a distribution.
DEFAULT_PHASE_CURVE: dict[str, tuple[PhaseAssignment, CurveType]] = {
    # Above the Line
    "10": (PhaseAssignment.FULL_SPAN, CurveType.FLAT),           # Story & Rights
    "11": (PhaseAssignment.FULL_SPAN, CurveType.FLAT),           # Producer
    "12": (PhaseAssignment.PREP_AND_PRODUCTION, CurveType.FLAT), # Director
    "13": (PhaseAssignment.PRODUCTION, CurveType.SHOOT_PROPORTIONAL),  # Cast
    "14": (PhaseAssignment.FULL_SPAN, CurveType.FLAT),           # ATL Travel/Living

    # Below the Line — Production
    "20": (PhaseAssignment.PREP_AND_PRODUCTION, CurveType.FRONT_LOADED),  # Production Staff
    "21": (PhaseAssignment.PRODUCTION, CurveType.SHOOT_PROPORTIONAL),     # Camera
    "22": (PhaseAssignment.PRODUCTION, CurveType.SHOOT_PROPORTIONAL),     # Electrical / Grip
    "23": (PhaseAssignment.PREP_AND_PRODUCTION, CurveType.BELL),          # Art Department
    "24": (PhaseAssignment.PREP_AND_PRODUCTION, CurveType.FRONT_LOADED),  # Set Construction
    "25": (PhaseAssignment.PREP_AND_PRODUCTION, CurveType.BELL),          # Set Decoration
    "26": (PhaseAssignment.PRODUCTION, CurveType.SHOOT_PROPORTIONAL),     # Props
    "27": (PhaseAssignment.PREP_AND_PRODUCTION, CurveType.BELL),          # Wardrobe
    "28": (PhaseAssignment.PRODUCTION, CurveType.SHOOT_PROPORTIONAL),     # Hair & Makeup
    "29": (PhaseAssignment.PRODUCTION, CurveType.SHOOT_PROPORTIONAL),     # Stunts / SFX

    # Below the Line — Production continued
    "30": (PhaseAssignment.PRODUCTION, CurveType.SHOOT_PROPORTIONAL),     # Locations
    "31": (PhaseAssignment.PRODUCTION, CurveType.SHOOT_PROPORTIONAL),     # Transport
    "32": (PhaseAssignment.PRODUCTION, CurveType.SHOOT_PROPORTIONAL),     # Catering / Craft
    "33": (PhaseAssignment.PRODUCTION, CurveType.SHOOT_PROPORTIONAL),     # Stage / Studio
    "34": (PhaseAssignment.PRODUCTION, CurveType.SHOOT_PROPORTIONAL),     # Second Unit
    "35": (PhaseAssignment.PRODUCTION, CurveType.SHOOT_PROPORTIONAL),     # Production Misc

    # Post-Production
    "40": (PhaseAssignment.POST, CurveType.BELL),               # Editing
    "41": (PhaseAssignment.POST, CurveType.BACK_LOADED),        # VFX
    "42": (PhaseAssignment.POST, CurveType.BACK_LOADED),        # Sound / Post Audio
    "43": (PhaseAssignment.POST, CurveType.BACK_LOADED),        # Music
    "44": (PhaseAssignment.DELIVERY, CurveType.MILESTONE),      # Lab / Deliverables
    "45": (PhaseAssignment.POST, CurveType.BELL),               # Post Supervision

    # Other
    "50": (PhaseAssignment.FULL_SPAN, CurveType.FLAT),          # Insurance
    "51": (PhaseAssignment.FULL_SPAN, CurveType.FLAT),          # Legal
    "52": (PhaseAssignment.FULL_SPAN, CurveType.FLAT),          # Finance / Completion Bond
    "53": (PhaseAssignment.FULL_SPAN, CurveType.FLAT),          # General Expenses
    "54": (PhaseAssignment.FULL_SPAN, CurveType.FLAT),          # Office / Overhead
    "55": (PhaseAssignment.FULL_SPAN, CurveType.FLAT),          # Publicity
}

# Fallback for codes not matching any known prefix
DEFAULT_FALLBACK = (PhaseAssignment.FULL_SPAN, CurveType.FLAT)


def get_default_for_code(code: str) -> tuple[PhaseAssignment, CurveType]:
    """Return the default (phase, curve) for a given budget code."""
    prefix = code[:2] if len(code) >= 2 else code
    return DEFAULT_PHASE_CURVE.get(prefix, DEFAULT_FALLBACK)
