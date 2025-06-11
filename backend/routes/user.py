from fastapi import APIRouter, HTTPException
# 사용자의 입력값을 검증하고 구조화할 수 있는 도구 (Pydantic의 BaseModel)
from pydantic import BaseModel
# 우리가 만든 비동기 DB 연결 객체
from database import database
# users 테이블 정의가 담긴 models.py에서 users 불러옴
from models import users
# 가입일 저장을 위한 현재 시간 모듈
from datetime import datetime, timezone, timedelta, tzinfo
# JWT 생성을 위한 라이브러리 
from jose import jwt
# FastAPI 라우터 객체 생성 (user 관련 경로 전용)
router = APIRouter()

import pytz
KST = pytz.timezone("Asia/Seoul")
from dotenv import load_dotenv
import os

load_dotenv()  # .env 파일 읽기


# JWT 관련 설정값 
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# 사용자가 회원가입 시 보내는 데이터 형식 정의
class UserCreate(BaseModel):
    name: str          # 이름 (문자열)
    age: int           # 나이 (정수)
    phone_number: str  # 핸드폰 번호 (문자열)

# 로그인 요청 시 받을 데이터 형식 
class UserLogin(BaseModel):
    phone_number: str

# JWT 액세스 토큰 생성 함수 
def create_access_token(data: dict, expires_delta: timedelta):
    """
    주어진 사용자 정보(data)와 만료시간을 바탕으로 JWT 액세스 토큰을 생성합니다.
    """
    to_encode = data.copy()  # 원본을 복사해서 수정
    expire = datetime.now(KST) + expires_delta  # 현재 시간 + 만료 시간 설정
    to_encode.update({"exp": expire})  # JWT에는 만료 시간(exp) 필드가 필요함
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # JWT 토큰 생성
    return encoded_jwt


# 회원가입 API 엔드포인트 정의
@router.post("/signup")
async def signup(user: UserCreate):
    """
    사용자 회원가입 처리 함수
    :param user: 요청 바디로 전달된 회원 정보 (name, age, phone_number)
    """

    # 1. 핸드폰 번호로 이미 등록된 사용자인지 DB 조회
    query = users.select().where(users.c.phone_number == user.phone_number)
    existing_user = await database.fetch_one(query)

    # 2. 이미 있으면 예외 발생 (HTTP 400)
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 등록된 번호입니다.")

    # 3. 등록된 적 없다면, DB에 사용자 정보 저장
    query = users.insert().values(
        name=user.name,
        age=user.age,
        phone_number=user.phone_number,
        created_at=datetime.now(KST)  # 가입 시간은 서버에서 자동 설정
    )
    await database.execute(query)

    # 4. 성공 메시지 반환
    return {"message": "회원가입 성공"}

# 로그인 API 라우터
@router.post("/login")
async def login(user: UserLogin):
    """
    핸드폰 번호로 로그인 요청을 처리합니다.
    성공 시 JWT 토큰을 반환하고,
    등록되지 않은 번호일 경우 에러를 반환합니다.
    """

    # 1. 해당 번호로 등록된 사용자가 있는지 데이터베이스에서 조회
    query = users.select().where(users.c.phone_number == user.phone_number)
    existing_user = await database.fetch_one(query)

    # 2. 없다면 로그인 실패 (401 Unauthorized)
    if not existing_user:
        raise HTTPException(status_code=401, detail="등록되지 않은 번호입니다.")

    # 3. 있다면 JWT 토큰 생성
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": str(existing_user["id"])},  # sub(subject)는 토큰 주체
        expires_delta=access_token_expires
    )

    # 4. 발급한 토큰을 JSON 형태로 반환
    return {
        "access_token": token,
        "token_type": "bearer"
    }