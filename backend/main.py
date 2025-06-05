from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import database
from models import metadata
from sqlalchemy import create_engine
from contextlib import asynccontextmanager
from routes import user, protected, passes, seat
from dotenv import load_dotenv
import os

load_dotenv() #.env 파일 읽기
DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI() # FastAPI 앱 객체 생성

# DB 초기화용 엔진 (테이블 생성에 필요)
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield 
    await database.disconnect()

app=FastAPI(lifespan=lifespan)

# CORS 미들웨어 추가 (React 프론트엔드 기본 주소 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 프론트엔드 주소에 맞게 수정 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(user.router)
app.include_router(protected.router)
app.include_router(passes.router)
app.include_router(seat.router)
@app.get("/")
async def root():
    return {"message": "스터디카페 앱 API 시작!"}
