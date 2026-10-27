from models.schemas import ReportData


class ReportFormatter:

    @staticmethod
    def format_html(data: ReportData, narrative: str) -> str:
        query_rows = "".join(
            f"<tr><td>{q.query}</td><td>{q.clicks}</td><td>{q.impressions}</td><td>{q.position}</td></tr>"
            for q in data.top_queries
        ) or "<tr><td colspan='4'>Nessuna query disponibile</td></tr>"

        page_rows = "".join(
            f"<tr><td>{p.page}</td><td>{p.clicks}</td><td>{p.impressions}</td><td>{p.position}</td></tr>"
            for p in data.top_pages
        ) or "<tr><td colspan='4'>Nessuna pagina disponibile</td></tr>"

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <h2>Report SEO — Periodo: {data.period}</h2>
            <p>
                <strong>Click Totali:</strong> {data.total_clicks} ({data.clicks_delta_pct}%) |
                <strong>Impressioni:</strong> {data.total_impressions} |
                <strong>CTR Medio:</strong> {data.avg_ctr * 100:.2f}% |
                <strong>Posizione Media:</strong> {data.avg_position}
            </p>

            <h3>Analisi Strategica</h3>
            <p style="background: #f4f6f8; padding: 12px; border-left: 4px solid #2563eb;">
                {narrative}
            </p>

            <h3>Top 5 Query</h3>
            <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%;">
                <tr style="background: #e2e8f0;">
                    <th>Query</th><th>Click</th><th>Impressioni</th><th>Posizione</th>
                </tr>
                {query_rows}
            </table>

            <h3>Top 5 Pagine</h3>
            <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%;">
                <tr style="background: #e2e8f0;">
                    <th>Pagina</th><th>Click</th><th>Impressioni</th><th>Posizione</th>
                </tr>
                {page_rows}
            </table>
        </body>
        </html>
        """

    @staticmethod
    def format_json(data: ReportData, narrative: str) -> dict:
        return {
            "metrics": data.model_dump(),
            "narrative": narrative
        }