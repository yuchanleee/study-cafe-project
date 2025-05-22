from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from dotenv import load_dotenv
import os

load_dotenv()

# JWT 관련 설정
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# FastAPI용 OAuth2 비밀번호 인증 스킴 (토큰 가져올 위치 명시)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# 라우터 생성
router = APIRouter()

# JWT 토큰 검증 함수
async def get_current_user(token: str = Depends(oauth2_scheme)) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="유효하지 않은 인증입니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 토큰 디코드해서 payload 추출
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")

        if user_id_str is None:
            raise credentials_exception

        return int(user_id_str)

    except JWTError:
        raise credentials_exception

# 보호된 API 예시 (/me)
@router.get("/me")
async def read_users_me(user_id: int = Depends(get_current_user)):
    return {
        "message": "로그인한 사용자만 볼 수 있는 정보입니다.",
        "user_id": user_id
    }