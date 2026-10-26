import os
import requests
from models.schemas import ReportData


class LLMReportView:

    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.api_url = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")

    def generate_narrative(self, data: ReportData) -> str:
        queries_summary = ", ".join(
            f"'{q.query}' ({q.clicks} click, pos. {q.position})" for q in data.top_queries
        ) or "nessuna query disponibile"

        pages_summary = ", ".join(
            f"'{p.page}' ({p.clicks} click)" for p in data.top_pages if p.page
        ) or "nessuna pagina disponibile"

        daily_desc = " | ".join(
            f"{d.date}: {d.clicks} click" for d in data.daily_trend
        ) or "dati giornalieri non disponibili"

        prompt = (
            f"Periodo: {data.period}. "
            f"Click totali: {data.total_clicks} (Variazione: {data.clicks_delta_pct}%). "
            f"Impression: {data.total_impressions}. "
            f"CTR medio: {data.avg_ctr * 100:.2f}%, Posizione media: {data.avg_position}. "
            f"Top query: {queries_summary}. "
            f"Pagine più visitate: {pages_summary}. "
            f"Andamento giornaliero: {daily_desc}. "
            "Scrivi un report discorsivo chiaro in italiano per un cliente non tecnico."
        )

        if not self.api_key or self.api_key.startswith("sk-proj-chiave"):
            trend = "in crescita" if data.clicks_delta_pct >= 0 else "in flessione"
            return (
                f"Nel periodo {data.period}, il sito ha registrato {data.total_clicks} click "
                f"e {data.total_impressions} impressioni, con un trend {trend} ({data.clicks_delta_pct}%). "
                f"Query principali: {queries_summary}. "
                f"Pagine più visitate: {pages_summary}. "
                f"Andamento giornaliero: {daily_desc}."
            )

        response = requests.post(
            self.api_url,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "temperature": 0.2,
                "messages": [
                    {"role": "system", "content": "Sei un consulente SEO senior chiaro e preciso."},
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]