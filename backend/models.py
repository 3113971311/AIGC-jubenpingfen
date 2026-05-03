from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    points = Column(Integer, default=0)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    token_version = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    scripts = relationship("Script", back_populates="user", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="user")


class PointsLog(Base):
    __tablename__ = "points_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # 正=发放, 负=消费
    reason = Column(String(200), nullable=False)
    balance_after = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SystemConfig(Base):
    __tablename__ = "system_configs"

    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=False)


class ModelConfig(Base):
    __tablename__ = "model_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    api_base = Column(String(255), nullable=False)
    api_key = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    scores = relationship("Score", back_populates="model_config")


class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    char_count = Column(Integer, default=0)
    filename = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="scripts")
    scores = relationship("Score", back_populates="script", cascade="all, delete-orphan")


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_config_id = Column(Integer, ForeignKey("model_configs.id"), nullable=False)
    points_cost = Column(Integer, default=0)

    interestingness = Column(Integer, nullable=False)
    popularity = Column(Integer, nullable=False)
    logic = Column(Integer, nullable=False)
    action_smoothness = Column(Integer, nullable=False)
    plot_smoothness = Column(Integer, nullable=False)
    overall = Column(Float, nullable=False)
    analysis = Column(Text)
    suggestions = Column(Text)
    progress = Column(String(500), default="")
    elapsed = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    script = relationship("Script", back_populates="scores")
    user = relationship("User", back_populates="scores")
    model_config = relationship("ModelConfig", back_populates="scores")
