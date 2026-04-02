from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.main import app


def _sample_overrides():
    return {
        "overrides": [
            {
                "account_code": "1201",
                "description": "Director",
                "is_foreign": None,
                "is_non_prov": False,
                "fed_labour_pct": 0.85,
                "fed_svc_labour_pct": 0.85,
                "prov_labour_pct": 0.8,
                "prov_svc_labour_pct": 0.8,
                "svc_property_pct": 0.0,
            }
        ]
    }


def test_template_round_trip():
    with TestClient(app) as client:
        save_res = client.put("/api/tax-credit/templates/Crime", json=_sample_overrides())
        assert save_res.status_code == 200

        list_res = client.get("/api/tax-credit/templates")
        assert list_res.status_code == 200
        assert "Crime" in list_res.json()

        load_res = client.get(
            "/api/tax-credit/templates/Crime",
            params=[("account_codes", "1201"), ("descriptions", "Director")],
        )
        assert load_res.status_code == 200
        payload = load_res.json()
        assert payload["project_name"] == "template::Crime"
        assert payload["overrides"][0]["account_code"] == "1201"


def test_template_excel_download():
    with TestClient(app) as client:
        client.put("/api/tax-credit/templates/Disaster", json=_sample_overrides())

        response = client.get("/api/tax-credit/templates/Disaster/excel")
        assert response.status_code == 200
        assert (
            response.headers["content-type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert response.content.startswith(b"PK")


def test_template_upload_with_account_and_svc_prop_headers():
    wb = Workbook()
    ws = wb.active
    ws.append([
        "Account",
        "Description",
        "OUT",
        "Prov Labour %",
        "Fed Labour %",
        "Prov Svc %",
        "Svc Prop %",
        "Fed Svc %",
    ])
    ws.append(["1201", "Director", "FALSE", "80%", "85%", "80%", "0%", "85%"])

    import io
    payload = io.BytesIO()
    wb.save(payload)
    payload.seek(0)

    with TestClient(app) as client:
        response = client.post(
            "/api/tax-credit/templates/Uploaded/upload",
            files={
                "file": (
                    "template.xlsx",
                    payload.getvalue(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["project_name"] == "template::Uploaded"
        assert body["overrides"][0]["account_code"] == "1201"
