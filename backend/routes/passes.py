from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from database import database
from models import passes, user_passes, users, purchase_logs
from routes.protected import get_current_user
from typing import List, Optional
router = APIRouter()

# 구매 요청 받을 데이터 형식
class PurchaseRequest(BaseModel):
    pass_id: int

# 로그인 후 사용자별 보유 이용권
class UserPassResponse(BaseModel):
    pass_id: int
    name: str
    pass_type: str
    remaining_time: Optional[int] = None
    expire_at: Optional[datetime] = None
    is_active: bool

# 이용권 구매
@router.post("/purchase")
async def purchase_pass(request: PurchaseRequest, current_user: str = Depends(get_current_user)):
    # 1. 이용권 존재 확인
    query = passes.select().where(passes.c.id == request.pass_id)
    selected_pass = await database.fetch_one(query)

    if not selected_pass:
        raise HTTPException(status_code=404, detail="해당 이용권이 존재하지 않습니다.")

    # 2. 사용자 정보 조회
    query = users.select().where(users.c.phone_number == current_user) 
    user = await database.fetch_one(query)

    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 3. user_passes에 구매 정보 생성
    now = datetime.now(timezone.utc)
    values = {
        "user_id": user["id"],
        "pass_id": selected_pass["id"],
        "purchase_at": now,
    }

    if selected_pass["pass_type"] == "time":
        values["expire_at"] = now + timedelta(hours=selected_pass["duration"])
        values["is_active"] = True
    elif selected_pass["pass_type"] == "time_period":
        values["remaining_time"] = selected_pass["duration"]
        values["is_active"] = False
    elif selected_pass["pass_type"] == "day":
        values["expire_at"] = now + timedelta(days=selected_pass["duration"])
        values["is_active"] = True
    else:
        raise HTTPException(status_code=400, detail="알 수 없는 이용권 유형입니다.")

    query = user_passes.insert().values(**values)
    await database.execute(query)

    # 4. purchase_logs 테이블에 구매 내역 기록
    log_values = {
        "user_id": user["id"],
        "pass_id": selected_pass["id"],
        "purchased_at": now,
        "price": selected_pass["price"],
    }
    query = purchase_logs.insert().values(**log_values)
    await database.execute(query)


    return {"message": "이용권이 성공적으로 구매되고 구매 기록이 저장되었습니다."}

# 사용자 이용권 보유 현황
@router.get("/user/passes", response_model=List[UserPassResponse])
async def get_user_passes(current_user: str = Depends(get_current_user)):
    # 1. 사용자 정보 조회
    query = users.select().where(users.c.phone_number == current_user)
    user = await database.fetch_one(query)

    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 2. user_passes + passes 조인해서 사용자 보유 이용권 가져오기
    join_query = (
        user_passes.join(passes, user_passes.c.pass_id == passes.c.id)
        .select()
        .where(user_passes.c.user_id == user["id"])
    )

    result = await database.fetch_all(join_query)

    # 3. 포맷팅해서 응답 (Class 인데 클라이언트에게 JSON 배열 형태로 응답 보냄)
    return [
        UserPassResponse(
            pass_id=record["pass_id"],
            name=record["name"],
            pass_type=record["pass_type"],
            remaining_time=record["remaining_time"],
            expire_at=record["expire_at"],
            is_active=record["is_active"],
        )
        for record in result
    ]