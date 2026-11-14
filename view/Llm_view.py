import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

PROMPT_TEMPLATE = Path(__file__).parent / "prompt_template.txt"


class LLMReportView:

    def __init__(self):
        load_dotenv(override=True)
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.api_url = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions").strip()
        self.model   = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite").strip()

    def _ask_llm(self, prompt: str) -> str:
        """Invia il prompt al modello e restituisce il testo della risposta."""
        for _ in range(3):  # con troppe richieste il servizio risponde 503: si riprova
            response = requests.post(
                self.api_url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "temperature": 0.3, "messages": [{"role": "user", "content": prompt}]},
                timeout=120
            )
            if response.status_code not in (429, 500, 503):
                break
            time.sleep(5)

        if not response.ok:
            print(f"[LLM] Errore {response.status_code}: {response.text}")
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def generate_weekly_html(self, risultato: dict) -> str:
        """Compila il prompt con i dati calcolati e restituisce l'HTML scritto dall'LLM."""
        if not self.api_key:
            raise ValueError("LLM_API_KEY non configurata")

        prompt = PROMPT_TEMPLATE.read_text(encoding="utf-8")
        prompt = prompt.replace("{periodo}", risultato["periodo"])
        prompt = prompt.replace("{periodo_precedente}", risultato["periodo_precedente"])
        prompt = prompt.replace("{dati}", json.dumps(risultato["dati"], ensure_ascii=False, indent=1))
        return self._ask_llm(prompt)