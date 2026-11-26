# Report SEO settimanale

Crea un report settimanale dagli export giornalieri di Google Search Console (per pagina e per query).
I numeri sono calcolati dal codice; il testo di analisi è scritto da un modello di linguaggio.

## Installazione (Windows, PowerShell)

    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt

## Configurazione

1. Crea una chiave API gratuita su https://aistudio.google.com ("Get API key").
2. Copia il file `.env.example`, rinominalo `.env` e incolla la chiave dopo `LLM_API_KEY=`.

Email è facoltativ: senza, il report viene creato ma non inviato.

## Avvio

    uvicorn main:app --reload

Poi apri http://127.0.0.1:8000

## Uso

- Report manuale: scegli i due CSV di Search Console e premi "Crea il report".
- Report automatico: usa i file di esempio in `static/gsc/` all'orario impostato nel timer
  (per provarlo subito scegli "Ogni tot minuti").

## Test

    python -m pytest -v