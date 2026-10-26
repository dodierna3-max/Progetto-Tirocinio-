from models.gsc_model import GSCClient
from models.analysis_model import SEOAnalyzer

if __name__ == "__main__":
    # 1. Istanzia il client (senza file .env userà automaticamente i dati Mock)
    gsc = GSCClient()

    # 2. Estrae i 4 blocchi di dati grezzi (list[dict])
    curr_raw  = gsc.fetch_query_metrics("2026-10-07", "2026-10-13")
    prev_raw  = []  # Simuliamo settimana precedente a zero (oppure passa curr_raw)
    page_raw  = gsc.fetch_page_metrics("2026-10-07", "2026-10-13")
    daily_raw = gsc.fetch_daily_metrics("2026-10-07", "2026-10-13")

    # 3. Esegue il calcolo vettoriale Pandas e valida con Pydantic
    report = SEOAnalyzer.analyze_data(
        current_raw=curr_raw,
        previous_raw=prev_raw,
        page_raw=page_raw,
        daily_raw=daily_raw,
        period_label="Test Stadio 1 (2026-10-07 / 2026-10-13)"
    )

    # 4. Stampa a schermo l'oggetto ReportData convertito in JSON formattato
    print(report.model_dump_json(indent=2))