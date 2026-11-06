from dotenv import load_dotenv
load_dotenv(override=True)
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from controllers.api_routes import router as api_router
from controllers.scheduler import ReportScheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    ReportScheduler().start()
    yield


app = FastAPI(title="SEO Reporting MVC", version="1.0.0", lifespan=lifespan)
app.include_router(api_router, prefix="/api")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_home():
    return FileResponse("static/index.html")