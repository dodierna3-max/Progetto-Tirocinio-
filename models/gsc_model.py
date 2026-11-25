import os
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from googleapiclient.discovery import build
class GSCClient:
    SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
    # Dati mock realistici per sviluppo locale (query)
    _MOCK_QUERY_ROWS = [
        {"query": "consulenza seo", "page": "https://esempio.it/servizi/seo",
         "clicks": 120, "impressions": 1500, "ctr": 0.08, "position": 2.4},
        {"query": "agenzia web",    "page": "https://esempio.it/chi-siamo",
         "clicks": 85,  "impressions": 1100, "ctr": 0.077, "position": 4.1},
        {"query": "posizionamento google", "page": "https://esempio.it/blog/posizionamento",
         "clicks": 60,  "impressions": 900,  "ctr": 0.067, "position": 5.3},
        {"query": "seo locale",     "page": "https://esempio.it/servizi/seo-locale",
         "clicks": 45,  "impressions": 700,  "ctr": 0.064, "position": 6.8},
        {"query": "audit seo",      "page": "https://esempio.it/audit",
         "clicks": 30,  "impressions": 500,  "ctr": 0.060, "position": 8.1},
    ]
    # Dati mock realistici per sviluppo locale (pagine di destinazione)
    _MOCK_PAGE_ROWS = [
        {"query": "", "page": "https://esempio.it/servizi/seo",
         "clicks": 200, "impressions": 2500, "ctr": 0.080, "position": 2.1},
        {"query": "", "page": "https://esempio.it/chi-siamo",
         "clicks": 130, "impressions": 1800, "ctr": 0.072, "position": 3.9},
        {"query": "", "page": "https://esempio.it/blog/posizionamento",
         "clicks": 90,  "impressions": 1200, "ctr": 0.075, "position": 4.5},
    ]
    # Dati mock per serie storica giornaliera (7 giorni)
    _MOCK_DATE_ROWS = [
        {"date": "2026-10-07", "clicks": 95,  "impressions": 1200, "ctr": 0.079, "position": 3.2},
        {"date": "2026-10-08", "clicks": 110, "impressions": 1350, "ctr": 0.081, "position": 3.1},
        {"date": "2026-10-09", "clicks": 88,  "impressions": 1100, "ctr": 0.080, "position": 3.3},
        {"date": "2026-10-10", "clicks": 102, "impressions": 1280, "ctr": 0.080, "position": 3.0},
        {"date": "2026-10-11", "clicks": 75,  "impressions": 980,  "ctr": 0.077, "position": 3.5},
        {"date": "2026-10-12", "clicks": 60,  "impressions": 820,  "ctr": 0.073, "position": 3.7},
        {"date": "2026-10-13", "clicks": 130, "impressions": 1600, "ctr": 0.081, "position": 2.9},
    ]
    def __init__(self):
        self.site_url  = os.getenv("GSC_SITE_URL", "https://www.esempio.it/")
        self.creds_path = os.getenv("GSC_CREDENTIALS_PATH", "")
    # ------------------------------------------------------------------ #
    #  Metodo privato: costruisce il client autenticato Google            #
    # ------------------------------------------------------------------ #
    def _build_service(self):
        creds = service_account.Credentials.from_service_account_file(
            self.creds_path, scopes=self.SCOPES
        )
        return build('searchconsole', 'v1', credentials=creds)
    # ------------------------------------------------------------------ #
    #  Metodo privato: esegue una singola query sull'API GSC              #
    # ------------------------------------------------------------------ #
    def _execute_query(self, service, payload: dict) -> list:
        try:
            response = (
                service.searchanalytics()
                       .query(siteUrl=self.site_url, body=payload)
                       .execute()
            )
            return response.get('rows', [])
        except HttpError as e:
            # Gestione errori HTTP Google (401, 403, 429, 500…)
            print(f"[GSCClient] HttpError {e.resp.status}: {e.error_details}")
            return []
        except Exception as e:
            print(f"[GSCClient] Errore imprevisto: {e}")
            return []
    # ------------------------------------------------------------------ #
    #  Recupero top query con pagina di destinazione associata           #
    # ------------------------------------------------------------------ #
    def fetch_query_metrics(
        self,
        start_date: str,
        end_date: str,
        row_limit: int = 10
    ) -> list[dict]:
        """Restituisce le top query con la relativa pagina di destinazione."""
        if not os.path.exists(self.creds_path):
            return self._MOCK_QUERY_ROWS[:row_limit]
        service = self._build_service()
        payload = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': ['query', 'page'],     # ← NUOVO: dimensione 'page'
            'rowLimit': row_limit
        }
        rows = self._execute_query(service, payload)
        return [
            {
                "query": r['keys'][0],
                "page":  r['keys'][1],           # ← NUOVO: landing page
                "clicks":      int(r['clicks']),
                "impressions": int(r['impressions']),
                "ctr":         float(r['ctr']),
                "position":    float(r['position'])
            }
            for r in rows
        ]
    # ------------------------------------------------------------------ #
    #  Recupero top pagine di destinazione (dimensione: page)            #
    # ------------------------------------------------------------------ #
    def fetch_page_metrics(
        self,
        start_date: str,
        end_date: str,
        row_limit: int = 10
    ) -> list[dict]:
        """Restituisce le pagine di destinazione con metriche aggregate."""
        if not os.path.exists(self.creds_path):
            return self._MOCK_PAGE_ROWS[:row_limit]
        service = self._build_service()
        payload = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': ['page'],              # ← solo dimensione pagina
            'rowLimit': row_limit
        }
        rows = self._execute_query(service, payload)
        return [
            {
                "query": "",
                "page":  r['keys'][0],
                "clicks":      int(r['clicks']),
                "impressions": int(r['impressions']),
                "ctr":         float(r['ctr']),
                "position":    float(r['position'])
            }
            for r in rows
        ]
    # ------------------------------------------------------------------ #
    #  Recupero serie storica giornaliera                                 #
    # ------------------------------------------------------------------ #
    def fetch_daily_metrics(
        self,
        start_date: str,
        end_date: str
    ) -> list[dict]:
        """Restituisce le metriche aggregate per singolo giorno (serie storica)."""
        if not os.path.exists(self.creds_path):
            return self._MOCK_DATE_ROWS
        service = self._build_service()
        payload = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': ['date'],              # ← NUOVO: dimensione 'date'
        }
        rows = self._execute_query(service, payload)
        return [
            {
                "date":        r['keys'][0],
                "clicks":      int(r['clicks']),
                "impressions": int(r['impressions']),
                "ctr":         float(r['ctr']),
                "position":    float(r['position'])
            }
            for r in rows
        ]
