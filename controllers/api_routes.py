from fastapi import APIRouter, HTTPException, Query
from controllers.report_controller import ReportController

router     = APIRouter()
controller = ReportController()


@router.get("/health")
def health_check():
    return {"status": "online", "service": "SEO Reporting MVC"}


@router.post("/generate-report")
def trigger_report(days: int = Query(default=7, ge=1, le=90)):
    try:
        return controller.execute_pipeline(days=days)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))