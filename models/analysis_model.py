from models.schemas import SEOMetrics, DailyMetrics, ReportData


def top_5(rows: list[dict]) -> list[SEOMetrics]:
    """Le 5 righe con più click."""
    best = sorted(rows, key=lambda r: r["clicks"], reverse=True)[:5]
    result = []
    for r in best:
        page = r.get("page")
        result.append(SEOMetrics(
            query=r.get("query") or "",
            page=page if isinstance(page, str) else None,
            clicks=int(r["clicks"]),
            impressions=int(r["impressions"]),
            ctr=float(r["ctr"]),
            position=float(r["position"]),
        ))
    return result


def calculate_delta(current_raw, previous_raw, daily_raw) -> float:
    """Variazione % dei click.

    Con un periodo precedente confronta le query; altrimenti confronta
    la seconda metà dei giorni caricati con la prima metà.
    """
    if previous_raw:
        current = sum(r["clicks"] for r in current_raw)
        previous = sum(r["clicks"] for r in previous_raw)
    else:
        days = sorted(daily_raw, key=lambda r: r["date"])
        if len(days) < 2:
            return 0.0
        half = len(days) // 2
        previous = sum(r["clicks"] for r in days[:half])
        current = sum(r["clicks"] for r in days[half:])

    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round((current - previous) / previous * 100.0, 2)


class SEOAnalyzer:

    @staticmethod
    def analyze_data(
        current_raw: list[dict],
        previous_raw: list[dict],
        page_raw: list[dict],
        daily_raw: list[dict],
        period_label: str
    ) -> ReportData:

        if not current_raw and not daily_raw:
            return ReportData(
                period=period_label, total_clicks=0, total_impressions=0,
                clicks_delta_pct=0.0, avg_ctr=0.0, avg_position=1.0,
                top_queries=[], top_pages=[], daily_trend=[]
            )

        # I totali si calcolano sui giorni: il file delle query contiene solo le prime righe.
        rows = daily_raw or current_raw
        total_clicks = sum(r["clicks"] for r in rows)
        total_impressions = sum(r["impressions"] for r in rows)
        avg_ctr = total_clicks / total_impressions if total_impressions else 0.0
        avg_position = sum(r["position"] for r in rows) / len(rows)

        daily_trend = [
            DailyMetrics(
                date=str(r["date"]),
                clicks=int(r["clicks"]),
                impressions=int(r["impressions"]),
                ctr=float(r["ctr"]),
                avg_position=float(r["position"]),
            )
            for r in sorted(daily_raw, key=lambda r: r["date"])
        ]

        return ReportData(
            period=period_label,
            total_clicks=int(total_clicks),
            total_impressions=int(total_impressions),
            clicks_delta_pct=calculate_delta(current_raw, previous_raw, daily_raw),
            avg_ctr=round(avg_ctr, 4),
            avg_position=round(avg_position, 2),
            top_queries=top_5(current_raw),
            top_pages=top_5(page_raw),
            daily_trend=daily_trend,
        )