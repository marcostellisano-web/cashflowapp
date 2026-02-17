"""Parse production parameters from an uploaded Excel file.

Expected format — a workbook with 3 sheets:

Sheet: "Info"
  Row 1: headers    Row 2: values
  Columns: Title | Episode Count | Prep Start | PP Start | PP End | Edit Start | Final Delivery | First Payroll Week

Sheet: "Shooting Blocks"
  Row 1: headers    Row 2+: one row per block
  Columns: Block | Type | Episodes | Shoot Start | Shoot End

Sheet: "Episode Deliveries"
  Row 1: headers    Row 2+: one row per episode
  Columns: Episode | Picture Lock | Online | Mix | Delivery
"""

from datetime import date, datetime
from io import BytesIO
from typing import BinaryIO

import openpyxl

from app.models.production import EpisodeDelivery, ProductionParameters, ShootingBlock


def _parse_date(val: object) -> date | None:
    """Coerce a cell value to a date, or None."""
    if val is None or val == "":
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%d-%b-%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Cannot parse date: {val}")
    raise ValueError(f"Unexpected date value type: {type(val)}")


def _require_date(val: object, field_name: str) -> date:
    result = _parse_date(val)
    if result is None:
        raise ValueError(f"Missing required date: {field_name}")
    return result


def _parse_episodes(val: object) -> list[int]:
    """Parse episode numbers from a cell — supports '1, 2, 3' or '1-3' or single int."""
    if val is None:
        return []
    if isinstance(val, (int, float)):
        return [int(val)]
    text = str(val).strip()
    if not text:
        return []
    # Handle ranges like '1-3'
    if "-" in text and "," not in text:
        parts = text.split("-")
        if len(parts) == 2:
            try:
                return list(range(int(parts[0].strip()), int(parts[1].strip()) + 1))
            except ValueError:
                pass
    # Handle comma-separated
    nums = []
    for part in text.split(","):
        part = part.strip()
        if part:
            try:
                nums.append(int(part))
            except ValueError:
                pass
    return nums


def parse_parameters_excel(file: BinaryIO) -> ProductionParameters:
    """Parse an Excel workbook into ProductionParameters."""
    wb = openpyxl.load_workbook(file, data_only=True)

    # --- Sheet: Info ---
    info_sheet = None
    for name in ("Info", "info", "INFO", "Production Info"):
        if name in wb.sheetnames:
            info_sheet = wb[name]
            break
    if info_sheet is None:
        # Fall back to first sheet
        info_sheet = wb.worksheets[0]

    # Read header row → value row
    headers = [str(c.value or "").strip().lower() for c in info_sheet[1]]
    values = [c.value for c in info_sheet[2]]

    def _col(name: str) -> object:
        """Find a column by fuzzy header match."""
        name_lower = name.lower()
        for i, h in enumerate(headers):
            if name_lower in h:
                return values[i] if i < len(values) else None
        return None

    title = str(_col("title") or "Untitled")
    episode_count = int(_col("episode") or _col("count") or 6)
    prep_start = _require_date(_col("prep"), "Prep Start")
    pp_start = _require_date(_col("pp start") or _col("pp_start"), "PP Start")
    pp_end = _require_date(_col("pp end") or _col("pp_end"), "PP End")
    edit_start = _require_date(_col("edit"), "Edit Start")
    final_delivery = _require_date(_col("final") or _col("delivery"), "Final Delivery")
    first_payroll = _parse_date(_col("payroll"))

    # --- Sheet: Shooting Blocks ---
    blocks_sheet = None
    for name in ("Shooting Blocks", "Blocks", "blocks", "shooting blocks", "SHOOTING BLOCKS"):
        if name in wb.sheetnames:
            blocks_sheet = wb[name]
            break

    blocks: list[ShootingBlock] = []
    if blocks_sheet is not None:
        b_headers = [str(c.value or "").strip().lower() for c in blocks_sheet[1]]

        def _bcol(row_vals: list, name: str) -> object:
            for i, h in enumerate(b_headers):
                if name in h:
                    return row_vals[i] if i < len(row_vals) else None
            return None

        for row in blocks_sheet.iter_rows(min_row=2, values_only=True):
            row_vals = list(row)
            if not any(row_vals):
                continue
            block_num = _bcol(row_vals, "block")
            if block_num is None:
                block_num = len(blocks) + 1
            blocks.append(
                ShootingBlock(
                    block_number=int(block_num),
                    block_type=str(_bcol(row_vals, "type") or "Shoot"),
                    shoot_start=_require_date(_bcol(row_vals, "start"), f"Block {block_num} Shoot Start"),
                    shoot_end=_require_date(_bcol(row_vals, "end"), f"Block {block_num} Shoot End"),
                )
            )

    # --- Sheet: Episode Deliveries ---
    del_sheet = None
    for name in ("Episode Deliveries", "Deliveries", "deliveries", "episode deliveries", "EPISODE DELIVERIES"):
        if name in wb.sheetnames:
            del_sheet = wb[name]
            break

    deliveries: list[EpisodeDelivery] = []
    if del_sheet is not None:
        d_headers = [str(c.value or "").strip().lower() for c in del_sheet[1]]

        def _dcol(row_vals: list, name: str) -> object:
            for i, h in enumerate(d_headers):
                if name in h:
                    return row_vals[i] if i < len(row_vals) else None
            return None

        for row in del_sheet.iter_rows(min_row=2, values_only=True):
            row_vals = list(row)
            if not any(row_vals):
                continue
            ep_num = _dcol(row_vals, "episode")
            if ep_num is None:
                ep_num = len(deliveries) + 1
            deliveries.append(
                EpisodeDelivery(
                    episode_number=int(ep_num),
                    picture_lock_date=_parse_date(_dcol(row_vals, "picture") or _dcol(row_vals, "lock")),
                    online_date=_parse_date(_dcol(row_vals, "online")),
                    mix_date=_parse_date(_dcol(row_vals, "mix")),
                    delivery_date=_require_date(_dcol(row_vals, "delivery"), f"Ep {ep_num} Delivery"),
                )
            )

    wb.close()

    return ProductionParameters(
        title=title,
        episode_count=episode_count,
        prep_start=prep_start,
        pp_start=pp_start,
        pp_end=pp_end,
        edit_start=edit_start,
        shooting_blocks=blocks,
        episode_deliveries=deliveries,
        final_delivery_date=final_delivery,
        first_payroll_week=first_payroll,
        hiatus_periods=[],
    )


def generate_parameters_template() -> BytesIO:
    """Generate a blank Excel template for production parameters."""
    wb = openpyxl.Workbook()

    # Sheet 1: Info
    ws_info = wb.active
    ws_info.title = "Info"
    ws_info.append(["Title", "Episode Count", "Prep Start", "PP Start", "PP End", "Edit Start", "Final Delivery", "First Payroll Week"])
    ws_info.append(["My Production", 6, "", "", "", "", "", ""])
    for col in range(1, 9):
        ws_info.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 18

    # Sheet 2: Shooting Blocks
    ws_blocks = wb.create_sheet("Shooting Blocks")
    ws_blocks.append(["Block", "Type", "Shoot Start", "Shoot End"])
    ws_blocks.append([1, "Shoot", "", ""])
    for col in range(1, 5):
        ws_blocks.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 18

    # Sheet 3: Episode Deliveries
    ws_del = wb.create_sheet("Episode Deliveries")
    ws_del.append(["Episode", "Picture Lock", "Online", "Mix", "Delivery"])
    ws_del.append([1, "", "", "", ""])
    for col in range(1, 6):
        ws_del.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 18

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    wb.close()
    return buf
