import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

from controllers.report_controller import ReportController

FILE_PROGRAMMA = Path("programmazione.json")
PROGRAMMA_INIZIALE = {"frequenza": "settimana", "giorno": 0, "ora": "08:30", "minuti": 60}
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]


class ReportScheduler:

    def __init__(self):
        self.controller = ReportController()
        self.programma = PROGRAMMA_INIZIALE
        if FILE_PROGRAMMA.exists():
            self.programma = json.loads(FILE_PROGRAMMA.read_text(encoding="utf-8"))
        self.in_corso = False
        self.ultimo_esito = None  # ultimo report creato da quando il server è acceso
        self.prossimo = self._calcola_prossimo()

    def _calcola_prossimo(self) -> datetime:
        """Data e ora del prossimo report in base alla programmazione."""
        p = self.programma
        adesso = datetime.now()
        if p["frequenza"] == "minuti":
            return adesso + timedelta(minutes=p["minuti"])

        ore, minuti = map(int, p["ora"].split(":"))
        prossimo = adesso.replace(hour=ore, minute=minuti, second=0, microsecond=0)
        if p["frequenza"] == "settimana":
            prossimo += timedelta(days=(p["giorno"] - prossimo.weekday()) % 7)
        if prossimo <= adesso:
            prossimo += timedelta(days=7 if p["frequenza"] == "settimana" else 1)
        return prossimo

    def cambia_programma(self, nuovo: dict):
        """Salva la nuova programmazione e ricalcola il prossimo report."""
        self.programma = nuovo
        FILE_PROGRAMMA.write_text(json.dumps(nuovo), encoding="utf-8")
        self.prossimo = self._calcola_prossimo()
        print(f"[SCHEDULER] Programmazione cambiata. Prossimo report: {self.prossimo:%d/%m/%Y alle %H:%M}")

    def stato(self) -> dict:
        """Quello che mostra la pagina: programmazione, tempo che manca, ultimo report."""
        return {
            "programma": self.programma,
            "in_corso": self.in_corso,
            "ultimo_esito": self.ultimo_esito,
            "secondi_mancanti": max(0, int((self.prossimo - datetime.now()).total_seconds())),
            "prossimo_testo": f"{GIORNI[self.prossimo.weekday()]} {self.prossimo:%d/%m/%Y alle %H:%M}",
        }

    def _run_loop(self):
        print(f"[SCHEDULER] Attivo. Prossimo report: {self.prossimo:%d/%m/%Y alle %H:%M}")
        while True:
            if datetime.now() >= self.prossimo:
                self.in_corso = True
                self.ultimo_esito = self.controller.report_da_server() or self.ultimo_esito
                self.in_corso = False
                self.prossimo = self._calcola_prossimo()
                print(f"[SCHEDULER] Prossimo report: {self.prossimo:%d/%m/%Y alle %H:%M}")
            time.sleep(1)

    def start(self):
        threading.Thread(target=self._run_loop, daemon=True).start()


# Un solo scheduler, condiviso da main.py e dalle route
scheduler = ReportScheduler()