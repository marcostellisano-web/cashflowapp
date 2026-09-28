from app import database


def test_vercel_default_database_uses_writable_tmp(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    assert database._default_database_url() == "sqlite:////tmp/cashflowapp-bible.db"


def test_local_default_database_remains_project_relative(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)

    assert database._default_database_url() == "sqlite:///./bible.db"
