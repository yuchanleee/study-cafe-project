from databases import Database
from dotenv import load_dotenv
import os

load_dotenv() #.env 파일 읽기
DATABASE_URL = os.getenv("DATABASE_URL")  # 개발용 SQLite DB 파일 경로, 나중에 PostgreSQL 등으로 바꿀 수 있음

# 데이터베이스 객체 생성 (비동기 방식)
database = Database(DATABASE_URL)
