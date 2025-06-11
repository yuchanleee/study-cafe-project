from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta, tzinfo
from database import database
from models import seats, user_passes, passes
from routes.protected import get_current_user
import pytz
KST = pytz.timezone("Asia/Seoul")
router=APIRouter()

class SeatStatusResponse(BaseModel):
    seat_name: str
    is_occupied: bool
    occupant_user_pass_id: Optional[int] = None
    occupant_remaining_time: Optional[int] = None  # 분 단위로 예시


@router.get("/status", response_model=List[SeatStatusResponse])
async def get_seat_status(user_id: int = Depends(get_current_user)):
    """
    모든 좌석 상태 조회 API.
    착석 중인 좌석은 occupant 정보와 남은 시간(분)을 포함해 반환.
    """

    # 1. 모든 좌석 조회
    query = seats.select()
    seat_records = await database.fetch_all(query)

    seat_status_list = []

    # 2. 착석중인 좌석에 대한 user_pass, pass 정보 조회 및 남은 시간 계산
    for seat in seat_records:
        if seat["is_occupied"] is not None:
            user_pass_query = user_passes.select().where(user_passes.c.id == seat["user_pass_id"])
            user_pass = await database.fetch_one(user_pass_query)

            if not user_pass:
                # 데이터 이상한 경우 대비: 착석 좌석에 user_pass_id가 없으면 비우기
                occupant_user_pass_id = None
                occupant_remaining_time = None
            else:

                occupant_user_pass_id = seat["user_pass_id"]

                # 남은 시간 계산 (분 단위)
                remaining_time = None
                now = datetime.now(KST)

                if user_pass["expire_at"]:
                    expire_at = user_pass["expire_at"].replace(tzinfo=timezone.utc) # sqlite에서는 timezone을 지원 안해서 저장은 utc로, 사용할때는 수동 보정 
                    remaining_delta = expire_at - now
                    remaining_time = max(int(remaining_delta.total_seconds() // 60), 0)

                elif user_pass["remaining_time"]:
                    # 예: 남은 시간이 직접 저장된 경우
                    start_at = seat["start_at"].replace(tzinfo=KST)
                    usetime_delta = now - start_at
                    remaining_time = max(int(user_pass["remaining_time"] - int(usetime_delta.total_seconds() // 60)),0)
                

                # 남은 시간이 0 이하라면 만료 처리
                if remaining_time is not None and remaining_time <= 0:
                    # 1. 좌석 비우기
                    seat_update = (
                        seats.update()
                        .where(seats.c.id == seat["id"])
                        .values(is_occupied=False, user_pass_id=None, start_at=None)
                    )
                    await database.execute(seat_update)

                    # 2. user_pass 만료처리: 삭제
                    delete_pass = user_passes.delete().where(user_passes.c.id == user_pass["id"])
                    await database.execute(delete_pass)

                    # 3. 반환용 데이터
                    occupant_user_pass_id = None
                    remaining_time = None


                occupant_remaining_time = remaining_time

        else:
            occupant_user_pass_id = None
            occupant_remaining_time = None

        seat_status_list.append(
            SeatStatusResponse(
                seat_name=seat["id"],
                is_occupied=seat["is_occupied"],
                occupant_user_pass_id=occupant_user_pass_id,
                occupant_remaining_time=occupant_remaining_time,
            )
        )

    return seat_status_list

