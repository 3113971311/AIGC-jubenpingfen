from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ===== Auth =====

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserInfo"


class UserInfo(BaseModel):
    id: int
    username: str
    points: int
    is_admin: bool
    is_active: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=8, max_length=100)
    points: int = Field(default=0, ge=0)
    is_admin: bool = False


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=2, max_length=50)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    points: Optional[int] = Field(None, ge=0)
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None


class UserListResponse(BaseModel):
    id: int
    username: str
    points: int
    is_admin: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ===== Model Config =====

class ModelConfigCreate(BaseModel):
    provider: str = Field(min_length=1, max_length=50)
    model_name: str = Field(min_length=1, max_length=100)
    api_base: str = Field(min_length=1, max_length=255)
    api_key: str = Field(min_length=1)


class ModelConfigUpdate(BaseModel):
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None


class ModelConfigResponse(BaseModel):
    id: int
    provider: str
    model_name: str
    api_base: str
    api_key_masked: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ModelOption(BaseModel):
    """用户端模型选择列表"""
    id: int
    provider: str
    model_name: str

    model_config = {"from_attributes": True}


class SystemConfigItem(BaseModel):
    key: str
    value: str


# ===== Script =====

class TextScriptCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


class ScriptResponse(BaseModel):
    id: int
    user_id: int
    title: str
    char_count: int
    filename: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ScriptDetailResponse(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    char_count: int
    filename: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ===== Score =====

class ScoreRequest(BaseModel):
    model_config_id: int = 0


class ScoreResponse(BaseModel):
    id: int
    script_id: int
    user_id: int
    model_config_id: int
    points_cost: int
    interestingness: int
    popularity: int
    logic: int
    action_smoothness: int
    plot_smoothness: int
    overall: float
    analysis: Optional[str]
    suggestions: Optional[str] = None
    progress: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScoreProgressResponse(BaseModel):
    """评分进度查询响应"""
    id: int
    script_id: int
    progress: str
    overall: float  # 0=进行中, >0=已完成
    created_at: datetime


# ===== Points Log =====

class PointsLogResponse(BaseModel):
    id: int
    amount: int
    reason: str
    balance_after: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ===== Feedback =====

class FeedbackRequest(BaseModel):
    contact: str = Field(default="", max_length=200)
    content: str = Field(min_length=1, max_length=5000)


# ===== Admin Stats =====

class AdminStats(BaseModel):
    total_users: int
    total_scores: int
    total_points_consumed: int
