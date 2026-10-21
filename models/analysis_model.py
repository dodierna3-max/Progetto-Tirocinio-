import pandas as pd
from models.schemas import SEOMetrics, DailyMetrics, ReportData
class SEOAnalyzer:
    """Motore di calcolo vettoriale: converte dati grezzi in ReportData validato."""
    @staticmethod
    def analyze_data(
        current_raw:  list[dict],
        previous_raw: list[dict],
        page_raw:     list[dict],    # ← NUOVO: dati per top landing pages
        daily_raw:    list[dict],    # ← NUOVO: dati per serie storica
        period_label: str
    ) -> ReportData:
        df_curr  = pd.DataFrame(current_raw)  if current_raw  else pd.DataFrame()
        df_prev  = pd.DataFrame(previous_raw) if previous_raw else pd.DataFrame()
        df_pages = pd.DataFrame(page_raw)     if page_raw     else pd.DataFrame()
        df_daily = pd.DataFrame(daily_raw)    if daily_raw    else pd.DataFrame()
        # ── Gestione edge case: nessun traffico nel periodo ──────────────
        if df_curr.empty:
            return ReportData(
                period=period_label,
                total_clicks=0,
                total_impressions=0,
                clicks_delta_pct=0.0,
                avg_ctr=0.0,
                avg_position=1.0,
                top_queries=[],
                top_pages=[],
                daily_trend=[]
            )
        # ── Aggregazione volumi ──────────────────────────────────────────
        curr_clicks      = int(df_curr['clicks'].sum())
        curr_impressions = int(df_curr['impressions'].sum())
        prev_clicks      = int(df_prev['clicks'].sum()) if not df_prev.empty else 0
        # ── Variazione percentuale protetta da ZeroDivisionError ─────────
        if prev_clicks > 0:
            delta_pct = round(((curr_clicks - prev_clicks) / prev_clicks) * 100.0, 2)
        else:
            delta_pct = 100.0 if curr_clicks > 0 else 0.0
        avg_ctr = round(float(df_curr['ctr'].mean()), 4)
        avg_pos = round(float(df_curr['position'].mean()), 2)
        # ── Top 5 query per click ────────────────────────────────────────
        df_top_q = df_curr.sort_values(by='clicks', ascending=False).head(5)
        top_queries = [
            SEOMetrics(**row.to_dict()) for _, row in df_top_q.iterrows()
        ]
        # ── Top 5 pagine di destinazione per click ── NUOVO ─────────────
        top_pages = []
        if not df_pages.empty:
            df_top_p = df_pages.sort_values(by='clicks', ascending=False).head(5)
            top_pages = [
                SEOMetrics(**row.to_dict()) for _, row in df_top_p.iterrows()
            ]
        # ── Serie storica giornaliera ── NUOVO ───────────────────────────
        daily_trend = []
        if not df_daily.empty:
            df_daily_sorted = df_daily.sort_values(by='date', ascending=True)
            daily_trend = [
                DailyMetrics(
                    date=str(row['date']),
                    clicks=int(row['clicks']),
                    impressions=int(row['impressions']),
                    ctr=float(row['ctr']),
                    avg_position=float(row['position'])
                )
                for _, row in df_daily_sorted.iterrows()
            ]
        return ReportData(
            period=period_label,
            total_clicks=curr_clicks,
            total_impressions=curr_impressions,
            clicks_delta_pct=delta_pct,
            avg_ctr=avg_ctr,
            avg_position=avg_pos,
            top_queries=top_queries,
            top_pages=top_pages,        # ← NUOVO
            daily_trend=daily_trend     # ← NUOVO
        )