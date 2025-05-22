from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from database import database
from models import seats, user_passes, passes
from routes.protected import get_current_user

router=APIRouter()

class SeatStatusResponse(BaseModel):
    seat_id: int
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
                now = datetime.now(timezone.utc)

                if user_pass["expire_at"]:
                    remaining_delta = user_pass["expire_at"] - now
                    remaining_time = max(int(remaining_delta.total_seconds() // 60), 0)

                elif user_pass["remaining_time"] is not None:
                    # 예: 남은 시간이 직접 저장된 경우
                    usetime_delta = now - seat["start_at"]
                    remaining_time = max(int(user_pass["remaining_time"] - int(usetime_delta.total_seconds() // 60)),0)

                occupant_remaining_time = remaining_time

        else:
            occupant_user_pass_id = None
            occupant_remaining_time = None

        seat_status_list.append(
            SeatStatusResponse(
                seat_id=seat["id"],
                is_occupied=seat["is_occupied"],
                occupant_user_pass_id=occupant_user_pass_id,
                occupant_remaining_time=occupant_remaining_time,
            )
        )

    return seat_status_list

