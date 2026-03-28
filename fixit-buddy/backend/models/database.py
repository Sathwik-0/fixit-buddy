from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid, os
from dotenv import load_dotenv

load_dotenv()
Base = declarative_base()

# Use /tmp for the SQLite file so Railway doesn't block the write permission
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/fixit.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Device(Base):
    __tablename__ = "devices"
    id            = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    brand         = Column(String)
    model         = Column(String)
    category      = Column(String)
    score         = Column(Float)
    grade         = Column(String)
    msrp_eur      = Column(Float)
    dpp_id        = Column(String)
    parts         = relationship("SparePart", back_populates="device")

class SparePart(Base):
    __tablename__ = "spare_parts"
    id            = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id     = Column(String, ForeignKey("devices.id"))
    part_name     = Column(String)
    part_number   = Column(String)
    oem_price_eur = Column(Float)
    eu_compliant  = Column(Boolean)
    device        = relationship("Device", back_populates="parts")

class RepairSession(Base):
    __tablename__ = "repair_sessions"
    id            = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id     = Column(String, ForeignKey("devices.id"))
    status        = Column(String, default="active")
    chunks        = relationship("RagChunk", back_populates="session")

class RagChunk(Base):
    __tablename__ = "rag_chunks"
    id            = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id    = Column(String, ForeignKey("repair_sessions.id"))
    chunk_index   = Column(Integer)
    content       = Column(Text)
    session       = relationship("RepairSession", back_populates="chunks")
