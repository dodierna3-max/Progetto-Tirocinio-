import io
import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File
from models.analysis_model import SEOAnalyzer
from view.Llm_view import LLMReportView
from view.report_view import ReportFormatter
from utils.notifier import EmailNotifier, TelegramNotifier

router = APIRouter()

# Nomi delle colonne dei CSV di Search Console (italiano e inglese) -> nomi interni
COLUMN_MAP = {
    "query più frequenti": "query", "top queries": "query", "query": "query",
    "pagine principali": "page", "top pages": "page", "page": "page",
    "data": "date", "date": "date",
    "clic": "clicks", "clicks": "clicks",
    "impressioni": "impressions", "impressions": "impressions",
    "ctr": "ctr",
    "posizione": "position", "position": "position",
}


def read_csv(content: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")
    df.columns = [COLUMN_MAP.get(c.strip().lower(), c.strip().lower()) for c in df.columns]
    if "ctr" in df.columns:
        # "8.62%" -> 0.0862
        df["ctr"] = df["ctr"].astype(str).str.rstrip("%").astype(float) / 100
    return df


@router.get("/health")
def health_check():
    return {"status": "online", "service": "SEO Reporting MVC"}


@router.post("/upload-report")
def upload_report(files: list[UploadFile] = File(...)):
    queries, pages, daily = [], [], []

    for file in files:
        try:
            df = read_csv(file.file.read())
        except Exception as e:
            print(f"[CSV ERROR] {file.filename}: {e}")
            raise HTTPException(status_code=400, detail=f"Non riesco a leggere il file \"{file.filename}\".")

        # Il tipo di file si riconosce dalle colonne; gli altri file (dispositivi, paesi...) vengono ignorati
        rows = df.to_dict(orient="records")
        if "query" in df.columns:
            queries = rows
        elif "page" in df.columns:
            pages = rows
        elif "date" in df.columns:
            daily = rows

    if not queries and not daily:
        raise HTTPException(status_code=400, detail="Carica almeno il file delle Query o quello del Grafico.")

    dates = sorted(str(r["date"]) for r in daily)
    period = f"{dates[0]} / {dates[-1]}" if dates else "Dati caricati"

    report_data = SEOAnalyzer.analyze_data(queries, [], pages, daily, period)

    try:
        narrative = LLMReportView().generate_narrative(report_data)
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        narrative = "Il riepilogo automatico non è al momento disponibile."

    html_content = ReportFormatter.format_html(report_data, narrative)
    subject = f"Report SEO ({period})"

    return {
        "report_html": html_content,
        "email_sent": EmailNotifier().send(subject, html_content),
        "telegram_sent": TelegramNotifier().send(subject, narrative),
    }