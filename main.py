from fastapi import FastAPI, HTTPException, status, Depends, APIRouter
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import models
from database import get_db, engine
from contextlib import asynccontextmanager
from fastapi.exception_handlers import (http_exception_handler, request_validation_exception_handler)
from fastapi.requests import Request
from routers import users, posts

@asynccontextmanager
async def lifespan(_app:FastAPI):
    yield
    await engine.dispose()
app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(posts.router, prefix="/posts", tags=["posts"])

@app.get("/")
def root():
    return "this is root "




@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exception: StarletteHTTPException):
    return await http_exception_handler(request, exception)
    

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request:Request, exception:RequestValidationError):
    return await request_validation_exception_handler(request, exception)
