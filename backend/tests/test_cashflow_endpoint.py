from fastapi.testclient import TestClient

from app.main import app
from app.models.cashflow import GenerateRequest


def test_generate_cashflow_returns_excel_file(sample_budget, sample_params):
    client = TestClient(app)
    payload = GenerateRequest(
        budget=sample_budget,
        parameters=sample_params,
        distributions=[],
    ).model_dump(mode="json")

    response = client.post("/api/cashflow/generate", json=payload)

    assert response.status_code == 200
    assert (
        response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="Test_Show_cashflow.xlsx"'
    )
    assert response.content.startswith(b"PK")
