"""Default Cashflow Timing Bible data.

This is the standard timing bible for TV productions. It maps each budget
account code to a specific cashflow timing pattern based on how that cost
is typically paid (payroll cycle, AP cycle, milestone-triggered, etc.).

Update this file when timing rules change.
"""

from app.models.timing_bible import BibleEntry, TimingBible, TimingPattern

_ENTRIES = [
    # --- Above the Line ---
    BibleEntry(
        account_code="0220",
        description="SCRIPT EDITOR(S)",
        timing_pattern=TimingPattern.EDIT_MINUS_2_TO_PIC_LOCK,
        timing_details="Evenly over the course of production on payroll weeks - starting two weeks before the edit starts until the end of picture lock of all eps",
        timing_title="Edit -2 to Picture Lock",
    ),
    BibleEntry(
        account_code="0225",
        description="RESEARCH",
        timing_pattern=TimingPattern.PREP_TO_LAST_SHOOT_PAYROLL,
        timing_details="Evenly over the course of production on payroll weeks - from the start until the end of last shoot block",
        timing_title="Prep to Last Shoot",
    ),
    BibleEntry(
        account_code="0401",
        description="EXECUTIVE PRODUCER",
        timing_pattern=TimingPattern.INTERNALS,
        timing_details="Monthly - mid month from prep to delivery, on AP weeks",
        timing_title="Internals",
    ),
    BibleEntry(
        account_code="0405",
        description="PRODUCER",
        timing_pattern=TimingPattern.INTERNALS,
        timing_details="Monthly - mid month from prep to delivery, on AP weeks",
        timing_title="Internals",
    ),
    BibleEntry(
        account_code="0410",
        description="SERIES PRODUCER",
        timing_pattern=TimingPattern.PREP_TO_DELIVERY_PAYROLL,
        timing_details="Evenly over the course of production on payroll weeks - from the start until final delivery",
        timing_title="Prep to Delivery Payroll",
    ),
    BibleEntry(
        account_code="0460",
        description="TRAVEL EXPENSES EXECUTIVE PRODUCER",
        timing_pattern=TimingPattern.TRAVEL,
        timing_details="Split by number of blocks - paid 2-3 weeks before each block on AP weeks",
        timing_title="Travel",
    ),
    BibleEntry(
        account_code="0461",
        description="TRAVEL EXPENSES SERIES PRODUCER(S)",
        timing_pattern=TimingPattern.TRAVEL,
        timing_details="Split by number of blocks - paid 2-3 weeks before each block on AP weeks",
        timing_title="Travel",
    ),
    BibleEntry(
        account_code="0465",
        description="LIVING EXPENSES EXECUTIVE PRODUCER",
        timing_pattern=TimingPattern.TRAVEL,
        timing_details="Split by number of blocks - paid 2-3 weeks before each block on AP weeks",
        timing_title="Travel",
    ),
    BibleEntry(
        account_code="0466",
        description="LIVING EXPENSES SERIES PRODUCER(S)",
        timing_pattern=TimingPattern.TRAVEL,
        timing_details="Split by number of blocks - paid 2-3 weeks before each block on AP weeks",
        timing_title="Travel",
    ),
    BibleEntry(
        account_code="0470",
        description="TRAVEL EXPENSES CORUS EXECUTIVE PRODUCER",
        timing_pattern=TimingPattern.TRAVEL,
        timing_details="Split by number of blocks - paid 2-3 weeks before each block on AP weeks",
        timing_title="Travel",
    ),
    BibleEntry(
        account_code="0490",
        description="LIVING EXPENSES CORUS EXECUTIVE PRODUCER",
        timing_pattern=TimingPattern.TRAVEL,
        timing_details="Split by number of blocks - paid 2-3 weeks before each block on AP weeks",
        timing_title="Travel",
    ),

    # --- Cast / Performers ---
    BibleEntry(
        account_code="0601",
        description="STARS",
        timing_pattern=TimingPattern.SHOOT_PAYROLL,
        timing_details="Split by number of weeks during shooting, paid on payroll weeks (starts 1-2 weeks after start of shoot)",
        timing_title="Shoot Payroll",
    ),
    BibleEntry(
        account_code="0640",
        description="OTHER PERFORMER'S",
        timing_pattern=TimingPattern.SHOOT_PAYROLL,
        timing_details="Split by number of weeks during shooting, paid on payroll weeks (starts 1-2 weeks after start of shoot)",
        timing_title="Shoot Payroll",
    ),

    # --- Production Staff ---
    BibleEntry(
        account_code="1201",
        description="PRODUCTION SUPERVISOR",
        timing_pattern=TimingPattern.INTERNALS,
        timing_details="Monthly - mid month from prep to delivery, on AP weeks",
        timing_title="Internals",
    ),
    BibleEntry(
        account_code="1205",
        description="PRODUCTION MANAGER",
        timing_pattern=TimingPattern.PREP_TO_DELIVERY_PAYROLL,
        timing_details="Evenly over the course of production on payroll weeks - from the start until final delivery",
        timing_title="Prep to Delivery Payroll",
    ),
    BibleEntry(
        account_code="1235",
        description="PRODUCTION ASSISTANT(S)/TRAINEE(S)",
        timing_pattern=TimingPattern.SHOOT_PAYROLL,
        timing_details="Split by number of weeks during shooting, paid on payroll weeks (starts 1-2 weeks after start of shoot)",
        timing_title="Shoot Payroll",
    ),
    BibleEntry(
        account_code="1243",
        description="PRODUCTION CO-ORDINATOR",
        timing_pattern=TimingPattern.PREP_TO_ROUGH_CUT_PAYROLL,
        timing_details="Evenly over the course of production on payroll weeks - from the start until the end of rough cut for all eps",
        timing_title="Prep to Rough Cut",
    ),
    BibleEntry(
        account_code="1248",
        description="OFFICE PRODUCTION ASSISTANT",
        timing_pattern=TimingPattern.INTERNALS,
        timing_details="Monthly - mid month from prep to delivery, on AP weeks",
        timing_title="Internals",
    ),
    BibleEntry(
        account_code="1250",
        description="PRODUCTION ACCOUNTANT",
        timing_pattern=TimingPattern.INTERNALS,
        timing_details="Monthly - mid month from prep to delivery, on AP weeks",
        timing_title="Internals",
    ),
    BibleEntry(
        account_code="1254",
        description="BOOKKEEPERS",
        timing_pattern=TimingPattern.INTERNALS,
        timing_details="Monthly - mid month from prep to delivery, on AP weeks",
        timing_title="Internals",
    ),

    # --- Art / Design ---
    BibleEntry(
        account_code="1301",
        description="PRODUCTION DESIGNER",
        timing_pattern=TimingPattern.SHOOT_PAYROLL,
        timing_details="Split by number of weeks during shooting, paid on payroll weeks (starts 1-2 weeks after start of shoot)",
        timing_title="Shoot Payroll",
    ),
    BibleEntry(
        account_code="1320",
        description="PRODUCTION ASSISTANT/TRAINEE(S)",
        timing_pattern=TimingPattern.SHOOT_PAYROLL,
        timing_details="Split by number of weeks during shooting, paid on payroll weeks (starts 1-2 weeks after start of shoot)",
        timing_title="Shoot Payroll",
    ),

    # --- Construction ---
    BibleEntry(
        account_code="1401",
        description="CONSTRUCTION CO-ORDINATOR",
        timing_pattern=TimingPattern.SHOOT_PAYROLL,
        timing_details="Split by number of weeks during shooting, paid on payroll weeks (starts 1-2 weeks after start of shoot)",
        timing_title="Shoot Payroll",
    ),
    BibleEntry(
        account_code="1495",
        description="OTHER",
        timing_pattern=TimingPattern.SHOOT_PAYROLL,
        timing_details="Split by number of weeks during shooting, paid on payroll weeks (starts 1-2 weeks after start of shoot)",
        timing_title="Shoot Payroll",
    ),

    # --- Camera ---
    BibleEntry(
        account_code="2201",
        description="DIRECTOR OF PHOTOGRAPHY",
        timing_pattern=TimingPattern.SHOOT_PAYROLL,
        timing_details="Split by number of weeks during shooting, paid on payroll weeks (starts 1-2 weeks after start of shoot)",
        timing_title="Shoot Payroll",
    ),
    BibleEntry(
        account_code="2205",
        description="CAMERA OPERATOR",
        timing_pattern=TimingPattern.SHOOT_PAYROLL,
        timing_details="Split by number of weeks during shooting, paid on payroll weeks (starts 1-2 weeks after start of shoot)",
        timing_title="Shoot Payroll",
    ),
    BibleEntry(
        account_code="2210",
        description="1ST ASSISTANT CAMERAPERSON / DMT",
        timing_pattern=TimingPattern.SHOOT_PAYROLL,
        timing_details="Split by number of weeks during shooting, paid on payroll weeks (starts 1-2 weeks after start of shoot)",
        timing_title="Shoot Payroll",
    ),
    BibleEntry(
        account_code="2260",
        description="DOP TRAVEL",
        timing_pattern=TimingPattern.TRAVEL,
        timing_details="Split by number of blocks - paid 2-3 weeks before each block on AP weeks",
        timing_title="Travel",
    ),
    BibleEntry(
        account_code="2263",
        description="DOP LIVING",
        timing_pattern=TimingPattern.TRAVEL,
        timing_details="Split by number of blocks - paid 2-3 weeks before each block on AP weeks",
        timing_title="Travel",
    ),
    BibleEntry(
        account_code="2270",
        description="STILL PHOTOGRAPHER",
        timing_pattern=TimingPattern.STILL_PHOTO,
        timing_details="2-3 weeks after each block on payroll weeks",
        timing_title="Still Photo",
    ),

    # --- Sound ---
    BibleEntry(
        account_code="2501",
        description="MIXER/SOUND RECORDIST",
        timing_pattern=TimingPattern.SHOOT_PAYROLL,
        timing_details="Split by number of weeks during shooting, paid on payroll weeks (starts 1-2 weeks after start of shoot)",
        timing_title="Shoot Payroll",
    ),

    # --- Office / Production Office ---
    BibleEntry(
        account_code="2801",
        description="OFFICE RENTALS",
        timing_pattern=TimingPattern.INTERNALS,
        timing_details="Monthly - mid month from prep to delivery, on AP weeks",
        timing_title="Internals",
    ),
    BibleEntry(
        account_code="2805",
        description="OFFICE FURNITURE",
        timing_pattern=TimingPattern.INTERNALS,
        timing_details="Monthly - mid month from prep to delivery, on AP weeks",
        timing_title="Internals",
    ),
    BibleEntry(
        account_code="2807",
        description="OFFICE EQUIPMENT",
        timing_pattern=TimingPattern.INTERNALS,
        timing_details="Monthly - mid month from prep to delivery, on AP weeks",
        timing_title="Internals",
    ),
    BibleEntry(
        account_code="2810",
        description="PHOTOCOPY",
        timing_pattern=TimingPattern.INTERNALS,
        timing_details="Monthly - mid month from prep to delivery, on AP weeks",
        timing_title="Internals",
    ),
    BibleEntry(
        account_code="2815",
        description="STATIONERY/SUPPLIES",
        timing_pattern=TimingPattern.INTERNALS,
        timing_details="Monthly - mid month from prep to delivery, on AP weeks",
        timing_title="Internals",
    ),
    BibleEntry(
        account_code="2820",
        description="TELEPHONE/TELEX/POSTAGE",
        timing_pattern=TimingPattern.INTERNALS,
        timing_details="Monthly - mid month from prep to delivery, on AP weeks",
        timing_title="Internals",
    ),
    BibleEntry(
        account_code="2830",
        description="COURIER",
        timing_pattern=TimingPattern.INTERNALS,
        timing_details="Monthly - mid month from prep to delivery, on AP weeks",
        timing_title="Internals",
    ),
    BibleEntry(
        account_code="2835",
        description="COMPUTER SERVICES",
        timing_pattern=TimingPattern.INTERNALS,
        timing_details="Monthly - mid month from prep to delivery, on AP weeks",
        timing_title="Internals",
    ),
    BibleEntry(
        account_code="2840",
        description="OFFICE CRAFT SERVICE",
        timing_pattern=TimingPattern.INTERNALS,
        timing_details="Monthly - mid month from prep to delivery, on AP weeks",
        timing_title="Internals",
    ),
    BibleEntry(
        account_code="2845",
        description="CLEANING",
        timing_pattern=TimingPattern.INTERNALS,
        timing_details="Monthly - mid month from prep to delivery, on AP weeks",
        timing_title="Internals",
    ),

    # --- Location / Shoot Operations ---
    BibleEntry(
        account_code="3020",
        description="TELEPHONE/TELEX/POSTAGE",
        timing_pattern=TimingPattern.MONTHLY_SHOOT,
        timing_details="Monthly over the course of the shoot (end of month), on AP weeks",
        timing_title="Monthly (shoot months)",
    ),
    BibleEntry(
        account_code="3095",
        description="OTHER",
        timing_pattern=TimingPattern.MONTHLY_SHOOT,
        timing_details="Monthly over the course of the shoot (end of month), on AP weeks",
        timing_title="Monthly (shoot months)",
    ),
    BibleEntry(
        account_code="3105",
        description="SITE RENTALS",
        timing_pattern=TimingPattern.MONTHLY_SHOOT,
        timing_details="Monthly over the course of the shoot (end of month), on AP weeks",
        timing_title="Monthly (shoot months)",
    ),
    BibleEntry(
        account_code="3142",
        description="CLEANING",
        timing_pattern=TimingPattern.MONTHLY_SHOOT,
        timing_details="Monthly over the course of the shoot (end of month), on AP weeks",
        timing_title="Monthly (shoot months)",
    ),
    BibleEntry(
        account_code="3195",
        description="OTHER",
        timing_pattern=TimingPattern.MONTHLY_SHOOT,
        timing_details="Monthly over the course of the shoot (end of month), on AP weeks",
        timing_title="Monthly (shoot months)",
    ),

    # --- Catering / Craft ---
    BibleEntry(
        account_code="3210",
        description="CATERING",
        timing_pattern=TimingPattern.PER_DIEM,
        timing_details="Split by number of blocks - during shoot blocks on AP weeks",
        timing_title="Per Diem",
    ),
    BibleEntry(
        account_code="3215",
        description="CRAFT SERVICE",
        timing_pattern=TimingPattern.PER_DIEM,
        timing_details="Split by number of blocks - during shoot blocks on AP weeks",
        timing_title="Per Diem",
    ),

    # --- Pre-Shoot Lump Sums ---
    BibleEntry(
        account_code="3225",
        description="FIRST AID",
        timing_pattern=TimingPattern.PRE_SHOOT,
        timing_details="Lump sum 2-3 weeks before. Start of PP - AP week",
        timing_title="Pre-Shoot",
    ),
    BibleEntry(
        account_code="3260",
        description="PUBLIC RELATIONS",
        timing_pattern=TimingPattern.PRE_SHOOT,
        timing_details="Lump sum 2-3 weeks before. Start of PP - AP week",
        timing_title="Pre-Shoot",
    ),

    # --- Travel & Transport ---
    BibleEntry(
        account_code="3301",
        description="FARES",
        timing_pattern=TimingPattern.TRAVEL,
        timing_details="Split by number of blocks - paid 2-3 weeks before each block on AP weeks",
        timing_title="Travel",
    ),
    BibleEntry(
        account_code="3310",
        description="HOTELS",
        timing_pattern=TimingPattern.TRAVEL,
        timing_details="Split by number of blocks - paid 2-3 weeks before each block on AP weeks",
        timing_title="Travel",
    ),
    BibleEntry(
        account_code="3320",
        description="PER DIEMS",
        timing_pattern=TimingPattern.PER_DIEM,
        timing_details="Split by number of blocks - during shoot blocks on AP weeks",
        timing_title="Per Diem",
    ),
    BibleEntry(
        account_code="3330",
        description="TAXIS/LIMOUSINES",
        timing_pattern=TimingPattern.PER_DIEM,
        timing_details="Split by number of blocks - during shoot blocks on AP weeks",
        timing_title="Per Diem",
    ),
    BibleEntry(
        account_code="3335",
        description="EXCESS BAGGAGE",
        timing_pattern=TimingPattern.PER_DIEM,
        timing_details="Split by number of blocks - during shoot blocks on AP weeks",
        timing_title="Per Diem",
    ),
    BibleEntry(
        account_code="3340",
        description="SHIPPING",
        timing_pattern=TimingPattern.MONTHLY_SHOOT,
        timing_details="Monthly over the course of the shoot (end of month), on AP weeks",
        timing_title="Monthly (shoot months)",
    ),
    BibleEntry(
        account_code="3395",
        description="OTHER",
        timing_pattern=TimingPattern.LEGAL,
        timing_details="Paid in 4 even chunks - starting a few weeks after prep ending a few weeks after delivery - AP weeks",
        timing_title="Legal",
    ),

    # --- Vehicles ---
    BibleEntry(
        account_code="3401",
        description="PRODUCTION CARS",
        timing_pattern=TimingPattern.MONTHLY_SHOOT,
        timing_details="Monthly over the course of the shoot (end of month), on AP weeks",
        timing_title="Monthly (shoot months)",
    ),
    BibleEntry(
        account_code="3430",
        description="GAS",
        timing_pattern=TimingPattern.PER_DIEM,
        timing_details="Split by number of blocks - during shoot blocks on AP weeks",
        timing_title="Per Diem",
    ),
    BibleEntry(
        account_code="3440",
        description="TAXIS",
        timing_pattern=TimingPattern.PER_DIEM,
        timing_details="Split by number of blocks - during shoot blocks on AP weeks",
        timing_title="Per Diem",
    ),
    BibleEntry(
        account_code="3445",
        description="PARKING",
        timing_pattern=TimingPattern.PER_DIEM,
        timing_details="Split by number of blocks - during shoot blocks on AP weeks",
        timing_title="Per Diem",
    ),
    BibleEntry(
        account_code="3447",
        description="MILEAGE",
        timing_pattern=TimingPattern.PER_DIEM,
        timing_details="Split by number of blocks - during shoot blocks on AP weeks",
        timing_title="Per Diem",
    ),

    # --- Rentals (Shoot) ---
    BibleEntry(
        account_code="3510",
        description="CARPENTRY RENTALS",
        timing_pattern=TimingPattern.SHOOT_RENTALS,
        timing_details="Split by number of weeks during shooting, paid on AP weeks (starts 1-2 weeks after start of shoot)",
        timing_title="Shoot Rentals",
    ),
    BibleEntry(
        account_code="3830",
        description="PURCHASES",
        timing_pattern=TimingPattern.SHOOT_PURCHASES,
        timing_details="Split by number of blocks - during shoot blocks on AP weeks",
        timing_title="Shoot Purchases",
    ),
    BibleEntry(
        account_code="4512",
        description="DAILY RENTALS",
        timing_pattern=TimingPattern.SHOOT_RENTALS,
        timing_details="Split by number of weeks during shooting, paid on AP weeks (starts 1-2 weeks after start of shoot)",
        timing_title="Shoot Rentals",
    ),
    BibleEntry(
        account_code="4530",
        description="PURCHASES",
        timing_pattern=TimingPattern.SHOOT_PURCHASES,
        timing_details="Split by number of blocks - during shoot blocks on AP weeks",
        timing_title="Shoot Purchases",
    ),
    BibleEntry(
        account_code="4812",
        description="DAILY RENTALS",
        timing_pattern=TimingPattern.SHOOT_RENTALS,
        timing_details="Split by number of weeks during shooting, paid on AP weeks (starts 1-2 weeks after start of shoot)",
        timing_title="Shoot Rentals",
    ),
    BibleEntry(
        account_code="4830",
        description="PURCHASES",
        timing_pattern=TimingPattern.SHOOT_PURCHASES,
        timing_details="Split by number of blocks - during shoot blocks on AP weeks",
        timing_title="Shoot Purchases",
    ),

    # --- Music / Stock ---
    BibleEntry(
        account_code="5001",
        description="ORIGINAL SCENES",
        timing_pattern=TimingPattern.PRE_SHOOT,
        timing_details="Lump sum 2-3 weeks before. Start of PP - AP week",
        timing_title="Pre-Shoot",
    ),

    # --- Post-Production ---
    BibleEntry(
        account_code="6001",
        description="SUPERVISOR",
        timing_pattern=TimingPattern.EDIT_INTERNALS,
        timing_details="Monthly - mid month over the course of the edit",
        timing_title="Edit Internals",
    ),
    BibleEntry(
        account_code="6002",
        description="POST COORDINATOR",
        timing_pattern=TimingPattern.PP_MINUS_2_TO_DELIVERY_PAYROLL,
        timing_details="Evenly over the course of production on payroll weeks - starting two weeks before PP until final delivery",
        timing_title="PP -2 to Delivery",
    ),
    BibleEntry(
        account_code="6010",
        description="EDITOR",
        timing_pattern=TimingPattern.EDIT_PAYROLL,
        timing_details="Evenly over the edit from edit start to picture lock - payroll weeks",
        timing_title="Edit",
    ),
    BibleEntry(
        account_code="6012",
        description="ASSISTANT EDITOR(S)",
        timing_pattern=TimingPattern.PP_MINUS_1_TO_DELIVERY_PAYROLL,
        timing_details="Evenly over the course of production on payroll weeks - starting one weeks before PP until final delivery",
        timing_title="PP -1 to Delivery",
    ),
    BibleEntry(
        account_code="6042",
        description="OTHER LABOUR",
        timing_pattern=TimingPattern.PP_MINUS_2_TO_DELIVERY_PAYROLL,
        timing_details="Evenly over the course of production on payroll weeks - starting two weeks before PP until final delivery",
        timing_title="PP -2 to Delivery",
    ),
    BibleEntry(
        account_code="6070",
        description="DIALOGUE / TRANSCRIPTION",
        timing_pattern=TimingPattern.PICK_LOCK,
        timing_details="Split by picture locks, paid 2-3 weeks after each picture lock - AP weeks",
        timing_title="Pick Lock",
    ),
    BibleEntry(
        account_code="6101",
        description="EDITING ROOMS",
        timing_pattern=TimingPattern.EDIT_INTERNALS,
        timing_details="Monthly - mid month over the course of the edit",
        timing_title="Edit Internals",
    ),
    BibleEntry(
        account_code="6110",
        description="EDITING EQUIPMENT",
        timing_pattern=TimingPattern.EDIT_INTERNALS,
        timing_details="Monthly - mid month over the course of the edit",
        timing_title="Edit Internals",
    ),
    BibleEntry(
        account_code="6130",
        description="PICTURE EDITING PURCHASES",
        timing_pattern=TimingPattern.EDIT_INTERNALS,
        timing_details="Monthly - mid month over the course of the edit",
        timing_title="Edit Internals",
    ),
    BibleEntry(
        account_code="6215",
        description="ON LINE",
        timing_pattern=TimingPattern.EDIT_INTERNALS,
        timing_details="Monthly - mid month over the course of the edit",
        timing_title="Edit Internals",
    ),
    BibleEntry(
        account_code="6221",
        description="COLOUR CORRECTION",
        timing_pattern=TimingPattern.ONLINE_EDITOR,
        timing_details="Split by each online, paid 2-3 weeks after each online - payroll weeks",
        timing_title="Online Editor",
    ),
    BibleEntry(
        account_code="6264",
        description="DISTRIBUTION COPIES",
        timing_pattern=TimingPattern.DELIVERY_COPIES,
        timing_details="Split by each delivery, paid 2-3 before each delivery - AP weeks",
        timing_title="Delivery copies",
    ),
    BibleEntry(
        account_code="6325",
        description="MIX-STUDIO & STOCK",
        timing_pattern=TimingPattern.MIX,
        timing_details="Paid 2-3 weeks after each mix, AP weeks",
        timing_title="Mix",
    ),
    BibleEntry(
        account_code="6610",
        description="COMPOSER",
        timing_pattern=TimingPattern.COMPOSER,
        timing_details="Paid in 2 pieces - one during midpoint of the edit, another at final picture lock - payroll weeks",
        timing_title="Composer",
    ),
    BibleEntry(
        account_code="6670",
        description="MUSIC RIGHTS",
        timing_pattern=TimingPattern.AFTER_DELIVERY,
        timing_details="Paid one month after delivery - AP week",
        timing_title="After Delivery",
    ),
    BibleEntry(
        account_code="6695",
        description="OTHER",
        timing_pattern=TimingPattern.AFTER_DELIVERY,
        timing_details="Paid one month after delivery - AP week",
        timing_title="After Delivery",
    ),
    BibleEntry(
        account_code="6701",
        description="TITLES-OPENING, CLOSING/GRAPHICS/SHOOT",
        timing_pattern=TimingPattern.GRAPHICS,
        timing_details="Starts 3-4 weeks after edit start, until final online - paid bi-weekly - AP weeks",
        timing_title="Graphics",
    ),
    BibleEntry(
        account_code="6710",
        description="GRAPHICS",
        timing_pattern=TimingPattern.GRAPHICS,
        timing_details="Starts 3-4 weeks after edit start, until final online - paid bi-weekly - AP weeks",
        timing_title="Graphics",
    ),
    BibleEntry(
        account_code="6890",
        description="CLOSED CAPTIONING",
        timing_pattern=TimingPattern.PICK_LOCK,
        timing_details="Split by picture locks, paid 2-3 weeks after each picture lock - AP weeks",
        timing_title="Pick Lock",
    ),
    BibleEntry(
        account_code="6892",
        description="DESCRIBED VIDEO",
        timing_pattern=TimingPattern.PICK_LOCK,
        timing_details="Split by picture locks, paid 2-3 weeks after each picture lock - AP weeks",
        timing_title="Pick Lock",
    ),

    # --- Publicity ---
    BibleEntry(
        account_code="7001",
        description="UNIT PUBLICIST",
        timing_pattern=TimingPattern.EDIT_INTERNALS,
        timing_details="Monthly - mid month over the course of the edit",
        timing_title="Edit Internals",
    ),
    BibleEntry(
        account_code="7025",
        description="STILLS/PRINTING/PROCESSING",
        timing_pattern=TimingPattern.STILL_PHOTO,
        timing_details="2-3 weeks after each block on payroll weeks",
        timing_title="Still Photo",
    ),
    BibleEntry(
        account_code="7050",
        description="PUBLIC RELATIONS",
        timing_pattern=TimingPattern.EDIT_INTERNALS,
        timing_details="Monthly - mid month over the course of the edit",
        timing_title="Edit Internals",
    ),

    # --- Insurance / Legal / Finance ---
    BibleEntry(
        account_code="7101",
        description="INSURANCE - PACKAGE, ADDITIONAL COVERAGE",
        timing_pattern=TimingPattern.INSURANCE,
        timing_details="Lump sum 2-3 weeks after prep start, AP week",
        timing_title="Insurance",
    ),
    BibleEntry(
        account_code="7110",
        description="LEGAL FEES",
        timing_pattern=TimingPattern.LEGAL,
        timing_details="Paid in 4 even chunks - starting a few weeks after prep ending a few weeks after delivery - AP weeks",
        timing_title="Legal",
    ),
    BibleEntry(
        account_code="7120",
        description="POST PRODUCTION ACCOUNTING",
        timing_pattern=TimingPattern.AFTER_DELIVERY,
        timing_details="Paid one month after delivery - AP week",
        timing_title="After Delivery",
    ),
    BibleEntry(
        account_code="7125",
        description="AUDIT FEE",
        timing_pattern=TimingPattern.AFTER_DELIVERY,
        timing_details="Paid one month after delivery - AP week",
        timing_title="After Delivery",
    ),
    BibleEntry(
        account_code="7130",
        description="BANK CHARGES",
        timing_pattern=TimingPattern.PREP_TO_DELIVERY_AP,
        timing_details="Evenly over the course of production on AP weeks - from start until final delivery",
        timing_title="Prep to Delivery AP",
    ),
    BibleEntry(
        account_code="7201",
        description="CORPORATE OVERHEAD",
        timing_pattern=TimingPattern.INTERNALS,
        timing_details="Monthly - mid month from prep to delivery, on AP weeks",
        timing_title="Internals",
    ),
    BibleEntry(
        account_code="7210",
        description="TAX CREDIT ADMINISTRATION FEE",
        timing_pattern=TimingPattern.AFTER_DELIVERY,
        timing_details="Paid one month after delivery - AP week",
        timing_title="After Delivery",
    ),
    BibleEntry(
        account_code="7220",
        description="INTERIM FINANCING",
        timing_pattern=TimingPattern.FINANCING,
        timing_details="Paid at the end of fiscal year ends. October (pro-rated by the amount of spend in each fiscal year) - some projects span 2 fiscal years",
        timing_title="Financing",
    ),
    BibleEntry(
        account_code="7295",
        description="OTHER",
        timing_pattern=TimingPattern.AFTER_DELIVERY,
        timing_details="Paid one month after delivery - AP week",
        timing_title="After Delivery",
    ),
]

DEFAULT_BIBLE = TimingBible(entries=_ENTRIES)
