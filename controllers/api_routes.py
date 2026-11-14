from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File
from controllers.report_controller import ReportController, CARTELLA_REPORT
from controllers.scheduler import scheduler
from models.schemas import ConfigScheduler
from models.weekly_model import leggi_csv

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "online", "service": "SEO Reporting MVC"}


@router.get("/report-automatici")
def report_automatici():
    """Elenco dei report creati dallo scheduler, dal più recente."""
    file_report = sorted(CARTELLA_REPORT.glob("report_*.html"), reverse=True)[:10]
    return [
        {
            "periodo": f.stem.split("__")[1].replace("_", " ") if "__" in f.stem else "Report",  # nome: report_<data>__<periodo>
            "creato": datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m/%Y alle %H:%M"),
            "nome": f.name,
            "url": f"/static/report/{f.name}",
        }
        for f in file_report
    ]


@router.get("/scheduler")
def stato_scheduler():
    return scheduler.stato()


@router.post("/scheduler")
def cambia_scheduler(config: ConfigScheduler):
    scheduler.cambia_programma(config.model_dump())
    return scheduler.stato()


@router.post("/upload-report")
def upload_report(files: list[UploadFile] = File(...)):
    pagine = query = None

    for file in files:
        try:
            df = leggi_csv(file.file)
        except Exception as e:
            print(f"[CSV ERROR] {file.filename}: {type(e).__name__}: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Il file \"{file.filename}\" non ha il formato atteso "
                       "(export giornaliero di Search Console per pagina o per query)."
            )
        # Il tipo di file si riconosce dalle colonne
        if "page" in df.columns:
            pagine = df
        elif "query" in df.columns:
            query = df

    if pagine is None or query is None:
        raise HTTPException(status_code=400, detail="Carica due file: l'export giornaliero per pagina e quello per query.")

    try:
        return ReportController().report_settimanale(pagine, query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))