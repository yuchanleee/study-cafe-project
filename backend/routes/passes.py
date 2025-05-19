from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from database import database
from models import passes, user_passes, users, purchase_logs
from routes.protected import get_current_user

router = APIRouter()

# 구매 요청 받을 데이터 형식
class PurchaseRequest(BaseModel):
    pass_id: int

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
        values["remaining_time"] = selected_pass["duration"]
    elif selected_pass["pass_type"] == "period":
        values["expire_at"] = now + timedelta(days=selected_pass["duration"])
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

