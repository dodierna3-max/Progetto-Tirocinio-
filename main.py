from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from controllers.api_routes import router as api_router
from controllers.scheduler import ReportScheduler




@asynccontextmanager
async def lifespan(app: FastAPI):
    ReportScheduler().start()
    yield


app = FastAPI(title="SEO Reporting MVC", version="1.0.0", lifespan=lifespan)
app.include_router(api_router, prefix="/api")