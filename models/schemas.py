from pydantic import BaseModel, Field
from typing import List, Optional
class SEOMetrics(BaseModel):
    """Rappresenta e valida una singola riga di metriche estratta da GSC (query + pagina)."""
    query: str
    page: Optional[str] = None          # ← NUOVO: pagina di destinazione
    clicks: int = Field(ge=0)
    impressions: int = Field(ge=0)
    ctr: float = Field(ge=0.0, le=1.0)
    position: float = Field(ge=1.0)
class DailyMetrics(BaseModel):
    """Rappresenta le metriche aggregate per un singolo giorno (serie storica)."""
    date: str                            # ← NUOVO: formato YYYY-MM-DD
    clicks: int = Field(ge=0)
    impressions: int = Field(ge=0)
    ctr: float = Field(ge=0.0, le=1.0)
    avg_position: float = Field(ge=1.0)
class ReportData(BaseModel):
    """Contenitore aggregato certificato per la generazione del report."""
    period: str
    total_clicks: int
    total_impressions: int
    clicks_delta_pct: float
    avg_ctr: float
    avg_position: float
    top_queries: List[SEOMetrics]
    top_pages: List[SEOMetrics]          # ← NUOVO: top landing pages
    daily_trend: List[DailyMetrics]      # ← NUOVO: serie storica giornaliera
