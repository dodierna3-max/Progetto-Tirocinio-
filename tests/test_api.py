import pytest
from fastapi.testclient import TestClient

import controllers.report_controller as modulo_controller
from controllers.report_controller import ReportController
from dati_di_prova import come_csv
from main import app

client = TestClient(app)  # senza "with": lo scheduler in background non parte


@pytest.fixture
def file_pagine(pagine):
    return ("files", ("pagine.csv", come_csv(pagine), "text/csv"))


@pytest.fixture
def file_query(query):
    return ("files", ("query.csv", come_csv(query), "text/csv"))


def test_un_solo_file_rifiutato(file_pagine):
    r = client.post("/api/upload-report", files=[file_pagine])
    assert r.status_code == 400
    assert "due file" in r.json()["detail"]


def test_senza_llm_il_report_esce_comunque(file_pagine, file_query):
    r = client.post("/api/upload-report", files=[file_pagine, file_query])

    assert r.status_code == 200  # nessuna chiave LLM: testo di riserva, ma indicatori e grafici ci sono
    assert "Il testo di analisi non è al momento disponibile" in r.json()["report_html"]
    assert r.json()["report_html"].count("class='grafico'") == 2
    assert r.json()["email_sent"] is False


def test_report_da_server_salvato_e_elencato(monkeypatch, pagine, query):
    monkeypatch.setattr(modulo_controller, "scarica_csv", lambda nome: pagine if nome == "pagine.csv" else query)

    esito = ReportController().report_da_server()
    elenco = client.get("/api/report-automatici").json()

    assert "19-25_ottobre_2026" in esito["url"]  # il periodo è nel nome del file
    assert [r["periodo"] for r in elenco] == ["19-25 ottobre 2026"]