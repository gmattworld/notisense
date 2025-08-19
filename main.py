import asyncio
import sys

from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from mangum import Mangum
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from notisense_api.application.v1 import notifications
from notisense_api.domain.exceptions.base_exception import AppBaseException

from notisense_api.domain.schemas.common_schema import BaseResponseSchema
from notisense_api.domain.utilities.config import settings
from notisense_api.infrastructure.persistence.database import get_db

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

IS_PROD = settings.IS_PROD
app = FastAPI(
    title="Notisense API",
    docs_url=None if IS_PROD else "/docs",
    redoc_url=None if IS_PROD else "/redoc",
    openapi_url=None if IS_PROD else "/openapi.json",
    dependencies=[Depends(get_db)]
)


@app.exception_handler(AppBaseException)
async def base_exception_handler(request: Request, exc: AppBaseException):
    return JSONResponse(
        status_code=exc.status_code,
        content=BaseResponseSchema(
            success=False,
            data=None,
            message=exc.detail,
            status_code=exc.status_code
        ).model_dump()
    )


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    # allow_origins=["*"],
    # allow_methods=["*"],
    # allow_headers=["*"],
)


app.include_router(notifications.controller.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Notisense API"}

handler = Mangum(app = app)
