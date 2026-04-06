from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.main import app


def _sample_template_rows():
    return [
        {
            "budget_code": "1100",
            "phase": "prep",
            "curve": "front_loaded",
            "curve_params": None,
            "milestone_dates": None,
            "milestone_amounts": None,
            "auto_assigned": False,
            "timing_pattern_override": "PROD->POST",
        },
        {
            "budget_code": "1200",
            "phase": "production",
            "curve": "bell",
            "curve_params": None,
            "milestone_dates": None,
            "milestone_amounts": None,
            "auto_assigned": False,
            "timing_pattern_override": None,
        },
    ]


def test_cashflow_template_round_trip():
    with TestClient(app) as client:
        save_res = client.put("/api/cashflow/templates/TestSeries", json=_sample_template_rows())
        assert save_res.status_code == 200

        list_res = client.get("/api/cashflow/templates")
        assert list_res.status_code == 200
        assert "TestSeries" in list_res.json()

        load_res = client.get(
            "/api/cashflow/templates/TestSeries",
            params=[("codes", "1100"), ("codes", "1200")],
        )
        assert load_res.status_code == 200
        body = load_res.json()
        assert len(body) == 2
        assert body[0]["budget_code"] == "1100"


def test_cashflow_template_upload_and_download():
    wb = Workbook()
    ws = wb.active
    ws.append(["Account", "Phase", "Curve", "Timing Pattern Override"])
    ws.append(["1100", "prep", "front_loaded", "PROD->POST"])
    ws.append(["1200", "production", "bell", ""])

    import io
    data = io.BytesIO()
    wb.save(data)
    data.seek(0)

    with TestClient(app) as client:
        up = client.post(
            "/api/cashflow/templates/UploadedCF/upload",
            files={
                "file": (
                    "cashflow_template.xlsx",
                    data.getvalue(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
        assert up.status_code == 200
        assert len(up.json()) == 2

        down = client.get("/api/cashflow/templates/UploadedCF/excel")
        assert down.status_code == 200
        assert (
            down.headers["content-type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert down.content.startswith(b"PK")
