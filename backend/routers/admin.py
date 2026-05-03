from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from auth import get_admin_user, hash_password, revoke_user_tokens
from database import get_db
from models import User, Score, ModelConfig
from schemas import (
    UserCreate, UserUpdate, UserListResponse, AdminStats,
    ModelConfigCreate, ModelConfigUpdate, ModelConfigResponse, ScoreResponse,
    SystemConfigItem,
)
from services.model_manager import (
    create_model_config, update_model_config,
    delete_model_config, toggle_model_config, mask_api_key,
    decrypt_api_key,
)
from services.points import grant_points
from services.system_config import get_all_configs, set_config

router = APIRouter(prefix="/api/admin", tags=["后台管理"])


# ==================== 用户管理 ====================

@router.get("/users", response_model=list[UserListResponse])
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    q = db.query(User)
    if search:
        q = q.filter(User.username.contains(search))
    total = q.count()
    users = q.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return users


@router.post("/users", response_model=UserListResponse)
def create_user(req: UserCreate, db: Session = Depends(get_db), _admin: User = Depends(get_admin_user)):
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        points=req.points,
        is_admin=req.is_admin,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserListResponse)
def update_user(
    user_id: int,
    req: UserUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if req.username is not None and req.username != user.username:
        if db.query(User).filter(User.username == req.username).first():
            raise HTTPException(status_code=400, detail="用户名已存在")
        user.username = req.username
    if req.password is not None:
        user.password_hash = hash_password(req.password)
        revoke_user_tokens(user, db)
    if req.points is not None and req.points != user.points:
        diff = req.points - user.points
        if diff != 0:
            grant_points(db, user_id, diff, "管理员调整积分")
    if req.is_admin is not None:
        user.is_admin = req.is_admin
    if req.is_active is not None and req.is_active != user.is_active:
        user.is_active = req.is_active
        revoke_user_tokens(user, db)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="不能删除管理员账号")
    db.delete(user)
    db.commit()
    return {"ok": True}


@router.put("/users/{user_id}/toggle")
def toggle_user(user_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = not user.is_active
    db.commit()
    return {"ok": True, "is_active": user.is_active}


@router.post("/users/{user_id}/recharge")
def recharge_user(
    user_id: int,
    amount: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="充值金额必须大于0")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    balance = grant_points(db, user_id, amount, "管理员后台充值")
    return {"ok": True, "balance_after": balance}


# ==================== 模型配置 ====================

def _model_to_response(m: ModelConfig) -> ModelConfigResponse:
    return ModelConfigResponse(
        id=m.id, provider=m.provider, model_name=m.model_name,
        api_base=m.api_base, api_key_masked=mask_api_key(m.api_key),
        is_active=m.is_active, created_at=m.created_at,
    )


@router.get("/models", response_model=list[ModelConfigResponse])
def list_models(db: Session = Depends(get_db), _admin: User = Depends(get_admin_user)):
    models = db.query(ModelConfig).order_by(ModelConfig.created_at.desc()).all()
    return [_model_to_response(m) for m in models]


@router.post("/models", response_model=ModelConfigResponse)
def add_model(req: ModelConfigCreate, db: Session = Depends(get_db), _admin: User = Depends(get_admin_user)):
    m = create_model_config(db, provider=req.provider, model_name=req.model_name,
                            api_base=req.api_base, api_key=req.api_key)
    return _model_to_response(m)


@router.put("/models/{model_id}", response_model=ModelConfigResponse)
def update_model(model_id: int, req: ModelConfigUpdate,
                 db: Session = Depends(get_db), _admin: User = Depends(get_admin_user)):
    kwargs = req.model_dump(exclude_none=True)
    m = update_model_config(db, model_id, **kwargs)
    if not m:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return _model_to_response(m)


@router.delete("/models/{model_id}")
def delete_model(model_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_admin_user)):
    if not delete_model_config(db, model_id):
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return {"ok": True}


@router.put("/models/{model_id}/toggle", response_model=ModelConfigResponse)
def toggle_model(model_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_admin_user)):
    m = toggle_model_config(db, model_id)
    if not m:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return _model_to_response(m)


@router.post("/models/{model_id}/test")
async def test_model(model_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_admin_user)):
    m = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="模型配置不存在")

    import httpx
    api_key = decrypt_api_key(m.api_key)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{m.api_base}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": m.model_name,
                    "messages": [{"role": "user", "content": "回复OK"}],
                    "max_tokens": 10,
                },
            )
        if resp.status_code == 200:
            data = resp.json()
            reply = data["choices"][0]["message"]["content"][:100]
            return {"ok": True, "message": f"连接成功！模型回复: {reply}"}
        elif resp.status_code in (401, 403):
            return {"ok": False, "message": "认证失败，请检查 API Key 是否正确"}
        elif resp.status_code == 404:
            return {"ok": False, "message": "API 地址或模型名不正确（404）"}
        else:
            return {"ok": False, "message": f"模型API返回 HTTP {resp.status_code}"}
    except Exception:
        return {"ok": False, "message": "连接模型服务失败，请检查 API 地址是否正确"}


# ==================== 系统设置 ====================

@router.get("/settings", response_model=list[SystemConfigItem])
def get_settings(db: Session = Depends(get_db), _admin: User = Depends(get_admin_user)):
    configs = get_all_configs(db)
    return [SystemConfigItem(key=k, value=v) for k, v in configs.items()]


@router.put("/settings")
def update_settings(
    data: list[SystemConfigItem],
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    for item in data:
        set_config(db, item.key, item.value)
    return {"ok": True}


# ==================== 评分记录 & 统计 ====================

@router.get("/scores", response_model=list[ScoreResponse])
def list_all_scores(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    rows = (
        db.query(Score)
        .order_by(Score.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    result = []
    for s in rows:
        result.append(ScoreResponse(
            id=s.id, script_id=s.script_id, user_id=s.user_id,
            model_config_id=s.model_config_id, points_cost=s.points_cost,
            interestingness=s.interestingness, popularity=s.popularity,
            logic=s.logic, action_smoothness=s.action_smoothness,
            plot_smoothness=s.plot_smoothness, overall=s.overall,
            analysis=s.analysis, suggestions=s.suggestions,
            progress=s.progress, elapsed=s.elapsed,
            created_at=s.created_at,
            provider=s.model_config.provider if s.model_config else None,
            model_name=s.model_config.model_name if s.model_config else None,
        ))
    return result


@router.get("/stats", response_model=AdminStats)
def get_stats(db: Session = Depends(get_db), _admin: User = Depends(get_admin_user)):
    total_users = db.query(User).count()
    total_scores = db.query(Score).count()
    total_consumed = db.query(func.coalesce(func.sum(Score.points_cost), 0)).scalar()
    return AdminStats(
        total_users=total_users,
        total_scores=total_scores,
        total_points_consumed=total_consumed,
    )


@router.get("/models/stats")
def get_model_stats(db: Session = Depends(get_db), _admin: User = Depends(get_admin_user)):
    """每个模型的评分耗时统计"""
    models = db.query(ModelConfig).order_by(ModelConfig.created_at.desc()).all()
    result = []
    for m in models:
        stats = db.query(
            func.count(Score.id),
            func.avg(Score.elapsed),
            func.min(Score.elapsed),
            func.max(Score.elapsed),
        ).filter(
            Score.model_config_id == m.id,
            Score.elapsed > 0,
            Score.overall > 0,
        ).first()
        count, avg_elapsed, min_elapsed, max_elapsed = stats
        result.append({
            "id": m.id,
            "provider": m.provider,
            "model_name": m.model_name,
            "is_active": m.is_active,
            "score_count": count or 0,
            "avg_elapsed": round(avg_elapsed, 1) if avg_elapsed else None,
            "min_elapsed": round(min_elapsed, 1) if min_elapsed else None,
            "max_elapsed": round(max_elapsed, 1) if max_elapsed else None,
        })
    return result
