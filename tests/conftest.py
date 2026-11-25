import dotenv
import pytest

# I test non devono leggere il file .env (con le chiavi vere)
dotenv.load_dotenv = lambda *args, **kwargs: False

from dati_di_prova import dati_pagine, dati_query

VARIABILI = ["LLM_API_KEY", "SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "CLIENT_EMAIL",
             "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]


@pytest.fixture(autouse=True)
def isola_i_test(monkeypatch, tmp_path):
    """Nessuna chiave vera, e i file creati dai test finiscono in una cartella temporanea."""
    for nome in VARIABILI:
        monkeypatch.delenv(nome, raising=False)

    import controllers.api_routes as api
    import controllers.report_controller as controller
    import controllers.scheduler as scheduler

    monkeypatch.setattr(scheduler, "FILE_PROGRAMMA", tmp_path / "programmazione.json")
    monkeypatch.setattr(controller, "CARTELLA_REPORT", tmp_path / "report")
    monkeypatch.setattr(api, "CARTELLA_REPORT", tmp_path / "report")


@pytest.fixture
def pagine():
    return dati_pagine()


@pytest.fixture
def query():
    return dati_query()