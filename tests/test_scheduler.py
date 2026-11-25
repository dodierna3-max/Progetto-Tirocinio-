from datetime import datetime

import controllers.scheduler as modulo
from controllers.scheduler import ReportScheduler


class OrologioFermo(datetime):
    """Al posto di datetime: now() restituisce sempre mercoledì 21 ottobre 2026, ore 10:00."""
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 10, 21, 10, 0)


def test_settimanale_va_al_lunedi_successivo(monkeypatch):
    monkeypatch.setattr(modulo, "datetime", OrologioFermo)
    scheduler = ReportScheduler()
    scheduler.programma = {"frequenza": "settimana", "giorno": 0, "ora": "08:30", "minuti": 60}

    assert scheduler._calcola_prossimo() == datetime(2026, 10, 26, 8, 30)


def test_programmazione_salvata_e_riletta(monkeypatch):
    monkeypatch.setattr(modulo, "datetime", OrologioFermo)
    nuova = {"frequenza": "settimana", "giorno": 4, "ora": "08:30", "minuti": 60}
    ReportScheduler().cambia_programma(nuova)

    riletto = ReportScheduler()  # un nuovo scheduler legge il file salvato
    assert riletto.programma == nuova
    assert riletto.stato()["prossimo_testo"] == "venerdì 23/10/2026 alle 08:30"