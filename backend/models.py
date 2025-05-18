from sqlalchemy import Table, Column, Integer, String, DateTime
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