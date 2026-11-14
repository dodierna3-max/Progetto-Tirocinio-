from datetime import datetime
from pathlib import Path

from models.weekly_model import analizza_settimana, scarica_csv
from view.Llm_view import LLMReportView
from view.report_view import crea_report
from utils.notifier import EmailNotifier, TelegramNotifier

CARTELLA_REPORT = Path("static/report")

# Se l'LLM non risponde il report esce comunque, con indicatori e grafici
TESTO_NON_DISPONIBILE = (
    "<h1>Report settimanale</h1>"
    "<p>Il testo di analisi non è al momento disponibile: trovi qui sotto i dati principali.</p>"
    "<h2>Andamento giornaliero</h2>[[GRAFICO_DISCOVER]][[GRAFICO_WEB]]"
)


class ReportController:

    def __init__(self):
        self.llm_view = LLMReportView()
        self.email    = EmailNotifier()
        self.telegram = TelegramNotifier()

    def report_settimanale(self, pagine, query) -> dict:
        """Dai due export giornalieri al report finito, con invio di email e Telegram."""
        risultato = analizza_settimana(pagine, query)  # ValueError se manca una settimana completa

        try:
            llm_html = self.llm_view.generate_weekly_html(risultato)
        except Exception as e:
            print(f"[LLM ERROR] {e}")
            llm_html = TESTO_NON_DISPONIBILE

        html = crea_report(llm_html, risultato)
        oggetto = f"Report settimanale SEO ({risultato['periodo']})"

        dati = risultato["dati"]
        riassunto = (f"{risultato['periodo']}: {dati['clic_totali']} clic "
                     f"({dati['clic_totali_variazione']} rispetto a {risultato['periodo_precedente']}).")

        return {
            "periodo": risultato["periodo"],
            "report_html": html,
            "email_sent": self.email.send(oggetto, html),
            "telegram_sent": self.telegram.send(oggetto, riassunto),
        }

    def report_da_server(self) -> dict | None:
        """Lavoro dello scheduler: scarica i CSV dal server dei dati, invia il report e lo salva in static/report."""
        print("[SCHEDULER] Generazione del report automatico in corso...")
        try:
            risultato = self.report_settimanale(scarica_csv("pagine.csv"), scarica_csv("query.csv"))
        except Exception as e:
            print(f"[SCHEDULER] Report non generato: {e}")
            return None

        CARTELLA_REPORT.mkdir(parents=True, exist_ok=True)
        periodo = risultato["periodo"].replace(" ", "_")  # il periodo resta leggibile nel nome del file
        nome = f"report_{datetime.now():%Y-%m-%d_%H-%M}__{periodo}.html"
        (CARTELLA_REPORT / nome).write_text(risultato["report_html"], encoding="utf-8")
        print(f"[SCHEDULER] Report salvato: http://127.0.0.1:8000/static/report/{nome}")
        print(f"[SCHEDULER] Email inviata: {'sì' if risultato['email_sent'] else 'no'}")
        return {
            "periodo": risultato["periodo"],
            "url": f"/static/report/{nome}",
            "email_sent": risultato["email_sent"],
        }