from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from databases import Database
from sqlalchemy import MetaData

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("phone_number", String, unique=True, index=True, nullable=False),
    Column("name", String, nullable=False),
    Column("age", Integer, nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

passes = Table(
    "passes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),            # 이용권 이름 (예: 1시간권, 1주일권)
    Column("pass_type", String, nullable=False),       # 'time' 또는 'time_period' 또는 'day_period'
    Column("duration", Integer, nullable=False),       # 시간권은 분 단위, 기간권은 일 단위
    Column("price", Integer, nullable=False),
)

user_passes = Table(
    "user_passes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False), # ForeignKey는 다른 테이블 컬럼에 꼭 존재하는 값이어야 한다는 뜻
    Column("pass_id", Integer, ForeignKey("passes.id"), nullable=False),
    Column("expire_at", DateTime(timezone=True), nullable=True), # 기간권, 일일권용 
    Column("remaining_time", Integer, nullable=True),            
    Column("is_active", Boolean, nullable=False),
    Column("seat_id", Integer, ForeignKey("seats.id"), nullable=True),

)

seats = Table(
    "seats",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, unique=True),  # 예: A1, A2...
    Column("is_occupied", Boolean, default=False),
    Column("user_pass_id", Integer, nullable=True),
    Column("start_at", DateTime(timezone=True), nullable=True)
)


purchase_logs = Table(
    "purchase_logs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("pass_id", Integer, ForeignKey("passes.id"), nullable=False),
    Column("purchased_at", DateTime(timezone=True), server_default=func.now()),
    Column("price", Integer, nullable=False),               # 구매 당시 가격 기록
)
