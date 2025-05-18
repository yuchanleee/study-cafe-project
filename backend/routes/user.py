# FastAPI에서 라우터(경로 관리)를 위한 모듈
from fastapi import APIRouter, HTTPException

# 사용자의 입력값을 검증하고 구조화할 수 있는 도구 (Pydantic의 BaseModel)
from pydantic import BaseModel

# 우리가 만든 비동기 DB 연결 객체
from backend.database import database

# users 테이블 정의가 담긴 models.py에서 users 불러옴
from backend.models import users

# 가입일 저장을 위한 현재 시간 모듈
from datetime import datetime

# FastAPI 라우터 객체 생성 (user 관련 경로 전용)
router = APIRouter()

# 사용자가 회원가입 시 보내는 데이터 형식 정의
class UserCreate(BaseModel):
    name: str          # 이름 (문자열)
    age: int           # 나이 (정수)
    phone_number: str  # 핸드폰 번호 (문자열)

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
        joined_at=datetime.utcnow()  # 가입 시간은 서버에서 자동 설정
    )
    await database.execute(query)

    # 4. 성공 메시지 반환
    return {"message": "회원가입 성공"}
