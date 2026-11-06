import os
import requests
from dotenv import load_dotenv
from models.schemas import ReportData


class LLMReportView:

    def __init__(self):
        load_dotenv(override=True)
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.api_url = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions").strip()
        self.model   = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite").strip()

    def generate_narrative(self, data: ReportData) -> str:
        queries_list = "\n".join(
            f"  - \"{q.query}\": {q.clicks} click, {q.impressions} visualizzazioni, posizione media {q.position}"
            for q in data.top_queries
        ) or "  Nessun dato disponibile."

        pages_list = "\n".join(
            f"  - {p.page}: {p.clicks} click, {p.impressions} visualizzazioni"
            for p in data.top_pages if p.page
        ) or "  Nessun dato disponibile."

        trend = "in crescita" if data.clicks_delta_pct >= 0 else "in calo"
        sign  = "+" if data.clicks_delta_pct >= 0 else ""

        prompt = f"""Dati del sito web nel periodo "{data.period}":

- Visitatori totali da Google: {data.total_clicks}
- Volte che il sito è comparso nei risultati: {data.total_impressions}
- Andamento delle visite nel periodo: {sign}{data.clicks_delta_pct}% ({trend})
- Percentuale di chi ha cliccato dopo aver visto il sito: {data.avg_ctr * 100:.2f}%
- Posizione media nei risultati di Google: {data.avg_position}

Parole cercate dagli utenti per trovare il sito:
{queries_list}

Pagine più visitate:
{pages_list}

Scrivi un report formale in italiano per il titolare dell'azienda, che NON ha competenze tecniche.
Rispondi a queste domande in modo chiaro e diretto:
1. Il sito sta andando bene o male rispetto a prima?
2. Le persone trovano il sito su Google? Come?
3. Quali sono i punti di forza e le criticità?
4. Cosa suggerirebbe un consulente per migliorare la situazione?

Regole:
- Usa un tono professionale ma comprensibile, come una lettera di un consulente di fiducia.
- NON usare mai termini tecnici senza spiegarli (es. non dire "CTR" ma "percentuale di click").
- Scrivi paragrafi discorsivi, NON elenchi puntati.
- Massimo 250 parole."""

        if not self.api_key:
            return (
                f"Gentile Cliente,\n\n"
                f"nel periodo analizzato ({data.period}), il Suo sito ha ricevuto "
                f"{data.total_clicks} visite da Google su {data.total_impressions} "
                f"visualizzazioni nei risultati di ricerca, con un andamento {trend} "
                f"({sign}{data.clicks_delta_pct}% nel corso del periodo).\n\n"
                f"Le parole più cercate dagli utenti per raggiungere il Suo sito sono state: "
                + ", ".join(f'"{q.query}"' for q in data.top_queries[:3])
                + "."
            )

        response = requests.post(
            self.api_url,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": self.model,
                "temperature": 0.3,
                "messages": [
                    {"role": "system", "content": (
                        "Sei un consulente di comunicazione digitale esperto. "
                        "Scrivi report chiari e professionali per clienti non tecnici. "
                        "Il tuo tono è quello di un professionista di fiducia che spiega "
                        "con semplicità l'andamento online dell'azienda del cliente."
                    )},
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=60
        )

        print(f"[DEBUG LLM] Status={response.status_code}")
        if not response.ok:
            print(f"[DEBUG LLM] Errore: {response.text}")

        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]