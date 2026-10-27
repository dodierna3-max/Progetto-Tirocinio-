from datetime import date, timedelta
from models.gsc_model import GSCClient
from models.analysis_model import SEOAnalyzer
from view.Llm_view import LLMReportView
from view.report_view import ReportFormatter
from utils.notifier import EmailNotifier, TelegramNotifier


class ReportController:

    def __init__(self):
        self.gsc_client = GSCClient()
        self.llm_view   = LLMReportView()
        self.email      = EmailNotifier()
        self.telegram   = TelegramNotifier()

    def execute_pipeline(self, days: int = 7) -> dict:
        today      = date.today() - timedelta(days=3)
        curr_start = today - timedelta(days=days)
        prev_end   = curr_start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days)
        period_label = f"{curr_start} / {today}"

        curr_raw  = self.gsc_client.fetch_query_metrics(str(curr_start), str(today))
        prev_raw  = self.gsc_client.fetch_query_metrics(str(prev_start), str(prev_end))
        page_raw  = self.gsc_client.fetch_page_metrics(str(curr_start), str(today))
        daily_raw = self.gsc_client.fetch_daily_metrics(str(curr_start), str(today))

        report_data = SEOAnalyzer.analyze_data(curr_raw, prev_raw, page_raw, daily_raw, period_label)

        try:
            narrative = self.llm_view.generate_narrative(report_data)
        except Exception as e:
            narrative = f"Riepilogo AI non disponibile ({e}). Consultare la tabella dati."

        subject      = f"Report SEO ({period_label})"
        html_content = ReportFormatter.format_html(report_data, narrative)
        email_sent    = self.email.send(subject, html_content)
        telegram_sent = self.telegram.send(subject, narrative)

        result = ReportFormatter.format_json(report_data, narrative)
        result["email_sent"]    = email_sent
        result["telegram_sent"] = telegram_sent
        return result