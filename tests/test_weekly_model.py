from datetime import date

import pandas as pd
import pytest

from models.weekly_model import analizza_settimana, totali, ultima_settimana, variazione


def a_numero(testo):
    """'17.500' -> 17500.0 e '11,02' -> 11.02 (formato italiano)."""
    return float(testo.replace(".", "").replace(",", "."))


def test_variazione_con_segno_e_base_zero():
    assert variazione(110, 100) == "+10,0%"
    assert variazione(90, 100) == "-10,0%"
    assert variazione(5, 0) == "nuovo (prima 0)"


def test_posizione_media_pesata_sulle_impressioni():
    df = pd.DataFrame({"clicks": [1, 1], "impressions": [900, 100], "position": [2, 20]})
    assert totali(df)[3] == pytest.approx(3.8)  # e non 11, la media semplice


def test_ultima_settimana_completa():
    df = pd.DataFrame({"date": [date(2026, 10, 20), date(2026, 10, 27)]})  # l'ultimo giorno è un martedì
    assert ultima_settimana(df) == (date(2026, 10, 19), date(2026, 10, 25))


def test_analisi_completa(pagine, query):
    r = analizza_settimana(pagine, query)
    canali = r["dati"]["canali"]

    assert r["periodo"] == "19-25 ottobre 2026"
    assert r["periodo_precedente"] == "12-18 ottobre 2026"
    assert [c["canale"] for c in canali] == ["Discover", "Ricerca web", "Immagini", "Google News", "Video"]
    assert "posizione" not in canali[0]  # Discover non ha la posizione
    assert r["grafici"]["giorni_settimana"][0] == "Lun 19"


def test_trend_quattro_settimane(pagine, query):
    trend = analizza_settimana(pagine, query)["dati"]["trend"]
    discover = next(c for c in trend["canali"] if c["canale"] == "Discover")
    clic = [a_numero(c) for c in discover["clic_per_settimana"]]

    assert len(trend["settimane_dalla_piu_vecchia"]) == 4
    assert trend["settimane_dalla_piu_vecchia"][0] == "28 settembre - 4 ottobre 2026"
    assert clic == sorted(clic, reverse=True) and len(set(clic)) == 4  # calo continuo


def test_novita_individuate(pagine, query):
    novita = analizza_settimana(pagine, query)["dati"]["novita"]
    assert [r["pagina"] for r in novita["pagine_discover"]["elenco"]] == ["/news/nuova-pagina.php"]
    assert [r["query"] for r in novita["query"]["elenco"]] == ["query nuova ottobre"]


def test_opportunita_rispettano_il_criterio(pagine, query):
    elenco = analizza_settimana(pagine, query)["dati"]["opportunita"]["query"]
    assert {r["query"] for r in elenco} == {"divano letto ikea", "cucine mondo convenienza"}
    for r in elenco:
        assert a_numero(r["impressioni"]) >= 300
        assert 8 <= a_numero(r["posizione"]) <= 20


def test_settimana_incompleta_solleva_errore(pagine, query):
    pagine = pagine[pagine["date"] <= date(2026, 9, 30)]  # solo tre giorni
    query = query[query["date"] <= date(2026, 9, 30)]
    with pytest.raises(ValueError, match="settimana completa"):
        analizza_settimana(pagine, query)