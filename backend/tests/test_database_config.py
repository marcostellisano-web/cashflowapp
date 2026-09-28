from app import database


def test_vercel_default_database_uses_writable_tmp(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    assert database._default_database_url() == "sqlite:////tmp/cashflowapp-bible.db"


def test_local_default_database_remains_project_relative(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)

    assert database._default_database_url() == "sqlite:///./bible.db"


def test_provider_postgres_urls_use_installed_psycopg2_driver():
    assert database._normalize_database_url("postgres://host/db") == (
        "postgresql+psycopg2://host/db"
    )
    assert database._normalize_database_url("postgresql://host/db") == (
        "postgresql+psycopg2://host/db"
    )


def test_database_initialization_is_lazy_and_runs_once(monkeypatch):
    calls = []
    monkeypatch.setattr(database, "_initialized", False)
    monkeypatch.setattr(database, "init_db", lambda: calls.append("initialized"))

    database.ensure_db_initialized()
    database.ensure_db_initialized()

    assert calls == ["initialized"]
