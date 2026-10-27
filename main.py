import os
from models.gsc_model import GSCClient
from models.analysis_model import SEOAnalyzer
from view.Llm_view import LLMReportView
from view.report_view import ReportFormatter
from utils.notifier import EmailNotifier, TelegramNotifier

if __name__ == "__main__":
    print("--- INIZIO TEST STADIO 1 + STADIO 2 ---\n")

    # 1. STADIO 1: Dati grezzi e calcolo metriche (Mock)
    print("[1/4] Estrazione dati e calcolo metriche (Pandas)...")
    gsc = GSCClient()
    report_data = SEOAnalyzer.analyze_data(
        current_raw=gsc.fetch_query_metrics("2026-10-07", "2026-10-13"),
        previous_raw=[],
        page_raw=gsc.fetch_page_metrics("2026-10-07", "2026-10-13"),
        daily_raw=gsc.fetch_daily_metrics("2026-10-07", "2026-10-13"),
        period_label="Test Stadio 1+2 (Ottobre 2026)"
    )

    # 2. STADIO 2 (LLM): Generazione del testo AI (o Fallback)
    print("[2/4] Generazione commento strategico (LLM_View)...")
    llm = LLMReportView()
    narrative = llm.generate_narrative(report_data)
    print(f"      -> Commento generato: '{narrative[:60]}...'")

    # 3. STADIO 2 (View): Creazione grafica HTML
    print("[3/4] Impaginazione grafica (ReportFormatter)...")
    html_output = ReportFormatter.format_html(report_data, narrative)

    # ---> SALVATAGGIO LOCALE DEL FILE HTML (Per il test visivo)
    file_html = "test_report.html"
    with open(file_html, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"      -> FILE SALVATO: Apri '{file_html}' per vedere la grafica!")

    # 4. STADIO 2 (Utils): Test Invio Email e Telegram
    print("\n[4/4] Test Moduli di Spedizione (Notifiers)...")
    
    email_bot = EmailNotifier()
    email_success = email_bot.send(subject="📊 Report SEO Test", html_body=html_output)
    
    telegram_bot = TelegramNotifier()
    telegram_success = telegram_bot.send(subject="Report SEO Test", body=narrative)

    print("\n--- TEST COMPLETATO CON SUCCESSO! ---")