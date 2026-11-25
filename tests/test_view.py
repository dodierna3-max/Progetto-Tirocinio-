import view.Llm_view as modulo
from models.weekly_model import analizza_settimana
from view.Llm_view import LLMReportView
from view.report_view import crea_report


def test_report_completo(pagine, query):
    risultato = analizza_settimana(pagine, query)
    testo_llm = "```html\n<h1>Titolo</h1><p>Sintesi</p><h2>Canali</h2>[[GRAFICO_DISCOVER]][[GRAFICO_WEB]]\n```"
    html = crea_report(testo_llm, risultato)

    assert "```" not in html                      # delimitatori rimossi
    assert html.count("class='grafico'") == 2     # due grafici
    assert html.count("vs settimana prec.") == 5  # cinque indicatori
    assert html.index("Sintesi") < html.index("class='kpi'") < html.index("<h2")  # indicatori dopo la sintesi


class RispostaFinta:
    def __init__(self, codice, testo=""):
        self.status_code, self.ok, self.text = codice, codice < 400, testo

    def json(self):
        return {"choices": [{"message": {"content": self.text}}]}

    def raise_for_status(self):
        pass  # le risposte finte usate qui non sono errori


def test_riprova_su_errori_temporanei(monkeypatch):
    risposte = [RispostaFinta(503), RispostaFinta(429), RispostaFinta(200, "<h1>Ok</h1>")]
    chiamate = []

    def post_finto(*args, **kwargs):
        chiamate.append(1)
        return risposte[len(chiamate) - 1]

    monkeypatch.setattr(modulo.requests, "post", post_finto)
    monkeypatch.setattr(modulo.time, "sleep", lambda secondi: None)  # niente attese vere

    assert LLMReportView()._ask_llm("prompt") == "<h1>Ok</h1>"
    assert len(chiamate) == 3  # la terza richiesta va a buon fine