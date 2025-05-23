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
        .values(is_occupied=True, user_pass_id=request.user_pass_id, start_at=now)
    )

    return {"message": "좌석 착석 완료", "seat_id": request.seat_id}

# 퇴실처리
@router.post("/leave")
async def leave_seat(user_id: int = Depends(get_current_user)):
    """
    좌석 퇴실 처리 API. 사용자가 착석 중인 좌석이 있으면 퇴실 처리하고,
    남은 시간을 user_passes에 저장함.
    """
    # 1. 사용자가 착석 중인 좌석 찾기 
    query = seats.select().where(seats.c.is_occupied == True)
    seat_records = await database.fetch_all(query)

    user_seat = None
    for seat in seat_records:
        # 해당 좌석의 user_pass_id로 user_passes 확인
        user_pass_query = user_passes.select().where(user_passes.c.id == seat["user_pass_id"])
        user_pass = await database.fetch_one(user_pass_query)

        if user_pass and user_pass["user_id"] == user_id:
            user_seat = seat
            break
    
    if not user_seat:
        raise HTTPException(status_code=404, detail="퇴실 처리할 좌석이 없습니다.")
    
    # 2. user_pass의 남은 시간 계산

    user_pass_query = user_passes.select().where(user_passes.c.id == user_seat["user_pass_id"])
    user_pass = await database.fetch_one(user_pass_query)
    now = datetime.now(timezone.utc)
    
    if user_pass["remaining_time"] is not None:
        elapsed_minutes = int((now - user_pass["started_at"]).total_seconds() // 60)
        update_remaining_time = user_pass["remaining_time"] - elapsed_minutes

        # user_pass 만료처리: 삭제
        if update_remaining_time <=0:
                delete_pass = user_passes.delete().where(user_passes.c.id == user_seat["user_pass_id"])
                await database.execute(delete_pass)

        # 시간이 남았다면 이용권 남은시간 갱신 
        else:
            await database.execute(
                user_passes.update()
                .where(user_passes.c.id == user_pass["id"])
                .values(
                    remaining_time=update_remaining_time,
                    is_active=False,
                    seat_id=None
                )
            )
    
    else:
        # user_pass 만료처리: 삭제
        expire_at = user_pass["expire_at"].replace(tzinfo=timezone.utc) # sqlite에서는 timezone을 지원 안해서 저장은 utc로, 사용할때는 수동 보정 
        elapsed_minutes = expire_at - now
        update_remaining_time = int(elapsed_minutes.total_seconds() // 60)

        if update_remaining_time <=0:
                delete_pass = user_passes.delete().where(user_passes.c.id == user_seat["user_pass_id"])
                await database.execute(delete_pass)

        else:
            # 기간 남았다면 그대로 저장
            await database.execute(
                user_passes.update()
                .where(user_passes.c.id == user_pass["id"])
                .values(
                    is_active=False,
                    seat_id=None
                )
            )
    
    # 3. 좌석 비우기
    await database.execute(
        seats.update()
        .where(seats.c.id == user_seat["id"])
        .values(
            is_occupied=False,
            user_pass_id=None,
            start_at=None
        )
    )

    return {"message": "퇴실 처리가 완료되었습니다."}
