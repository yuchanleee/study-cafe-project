from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from database import database
from models import passes, user_passes, users, purchase_logs, seats
from routes.protected import get_current_user
from typing import List, Optional
router = APIRouter()

# 구매 요청 받을 데이터 형식
class PurchaseRequest(BaseModel):
    pass_id: int

# 로그인 후 사용자별 보유 이용권
class UserPassResponse(BaseModel):
    user_pass_id: int
    pass_id: int
    name: str
    pass_type: str
    remaining_time: Optional[int] = None
    expire_at: Optional[datetime] = None
    is_active: bool

# 착석 처리 데이터 형식
class SeatRequest(BaseModel):
    user_pass_id: int
    seat_id: int

# 이용권 구매
@router.post("/purchase")
async def purchase_pass(request: PurchaseRequest, user_id: int = Depends(get_current_user)):
    # 1. 이용권 존재 확인
    query = passes.select().where(passes.c.id == request.pass_id)
    selected_pass = await database.fetch_one(query)

    if not selected_pass:
        raise HTTPException(status_code=404, detail="해당 이용권이 존재하지 않습니다.")


    # 2. user_passes에 구매 정보 생성
    now = datetime.now(timezone.utc)
    values = {
        "user_id": user_id,
        "pass_id": selected_pass["id"],
    }

    if selected_pass["pass_type"] == "time":
        values["expire_at"] = now + timedelta(minutes=selected_pass["duration"])
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

    # 3. purchase_logs 테이블에 구매 내역 기록
    log_values = {
        "user_id": user_id,
        "pass_id": selected_pass["id"],
        "purchased_at": now,
        "price": selected_pass["price"],
    }
    query = purchase_logs.insert().values(**log_values)
    await database.execute(query)


    return {"message": "이용권이 성공적으로 구매되고 구매 기록이 저장되었습니다."}

# 사용자 이용권 보유 현황
@router.get("/user/passes", response_model=List[UserPassResponse])
async def get_user_passes(user_id: int = Depends(get_current_user)):

    # 1. user_passes + passes 조인해서 사용자 보유 이용권 가져오기
    join_query = (
        user_passes.join(passes, user_passes.c.pass_id == passes.c.id)
        .select()
        .where(user_passes.c.user_id == user_id)
    )

    result = await database.fetch_all(join_query)

    # 2. 포맷팅해서 응답 (Class 인데 클라이언트에게 JSON 배열 형태로 응답 보냄)
    return [
        UserPassResponse(
            user_pass_id=record["id"],
            pass_id=record["pass_id"],
            name=record["name"],
            pass_type=record["pass_type"],
            remaining_time=record["remaining_time"],
            expire_at=record["expire_at"],
            is_active=record["is_active"],
        )
        for record in result
    ]

# 착석처리 
@router.post("/seat")
async def occupy_seat(request: SeatRequest, user_id: int = Depends(get_current_user)):

    now = datetime.now(timezone.utc)

    # user_passes 업데이트: 좌석 지정, 착석 시간 기록, 활성화 처리
    await database.execute(
        user_passes.update()
        .where(user_passes.c.id == request.user_pass_id)
        .values(is_active=True, seat_id=request.seat_id)
    )

    # seats 업데이트: 좌석 점유 상태 변경
    await database.execute(
        seats.update()
        .where(seats.c.id == request.seat_id)
        .values(is_occupied=True, user_pass_id=request.user_pass_id, started_at=now)
    )

    return {"message": "좌석 착석 완료", "seat_id": request.seat_id}