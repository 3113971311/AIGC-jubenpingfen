import asyncio
import time
import traceback
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db, SessionLocal
from models import User, Script, Score, PointsLog
from schemas import ScoreRequest, ScoreResponse, ScoreProgressResponse, ModelOption, PointsLogResponse
from services.ai_scorer import score_script
from services.model_manager import get_active_models, get_model_config
from services.points import consume_or_fail, refund_points
from services.system_config import get_config_int, get_config

router = APIRouter(prefix="/api", tags=["评分"])

_background_tasks: set[asyncio.Task] = set()


async def _run_scoring_background(score_id: int, script_content: str, model_config_id: int, user_id: int):
    """后台执行 AI 评分，使用独立数据库会话"""
    db = SessionLocal()
    try:
        placeholder = db.query(Score).filter(Score.id == score_id).first()
        if not placeholder:
            return

        model_config = get_model_config(db, model_config_id)
        if not model_config:
            placeholder.progress = "错误：模型配置不存在"
            db.commit()
            return

        async def update_progress(msg: str):
            try:
                placeholder.progress = msg
                db.commit()
            except Exception:
                pass

        await update_progress("正在准备评分...")
        timeout = get_config_int(db, "score_timeout", 600) or 0
        t0 = time.time()
        result = await score_script(script_content, model_config, timeout=timeout, progress_callback=update_progress)
        elapsed = round(time.time() - t0, 1)

        placeholder.interestingness = result["interestingness"]
        placeholder.popularity = result["popularity"]
        placeholder.logic = result["logic"]
        placeholder.action_smoothness = result["action_smoothness"]
        placeholder.plot_smoothness = result["plot_smoothness"]
        placeholder.overall = result["overall"]
        placeholder.analysis = result["analysis"]
        placeholder.suggestions = result.get("suggestions", "")
        placeholder.elapsed = elapsed
        placeholder.progress = f"评分完成，耗时 {elapsed} 秒"
        db.commit()

    except Exception as e:
        traceback.print_exc()
        err_msg = str(e)[:200]
        try:
            placeholder = db.query(Score).filter(Score.id == score_id).first()
            if placeholder:
                pts = placeholder.points_cost
                sid = placeholder.script_id
                placeholder.progress = f"评分失败: {err_msg}，积分已退还"
                placeholder.overall = -1
                refund_points(db, user_id, pts, f"评分失败退款: 剧本#{sid}")
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


@router.get("/models/active", response_model=list[ModelOption])
def list_active_models(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    models = get_active_models(db)
    return [ModelOption(id=m.id, provider=m.provider, model_name=m.model_name) for m in models]


@router.post("/scripts/{script_id}/score", response_model=ScoreResponse)
async def do_score(
    script_id: int,
    req: ScoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    if script.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权对该剧本评分")

    existing = db.query(Score).filter(Score.script_id == script_id).first()
    if existing:
        if existing.overall == 0:
            raise HTTPException(status_code=400, detail="该剧本评分进行中，请稍后再试")
        elif existing.overall == -1:
            # 上次评分失败，允许重新评分，删除旧的失败记录
            db.delete(existing)
            db.commit()
        else:
            raise HTTPException(status_code=400, detail="该剧本已评分，不能重复评分")

    model_id = req.model_config_id or int(get_config(db, "active_model_id", "0") or "0")
    if not model_id:
        raise HTTPException(status_code=400, detail="未配置评分模型")

    model_config = get_model_config(db, model_id)
    if not model_config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    if not model_config.is_active:
        raise HTTPException(status_code=400, detail="该模型已禁用")

    max_chars = get_config_int(db, "max_chars", 100000)
    points_per_10000 = get_config_int(db, "points_per_10000_chars", 1)

    if max_chars > 0 and script.char_count > max_chars:
        raise HTTPException(status_code=400, detail=f"剧本字数({script.char_count})超过系统上限({max_chars})")

    import math
    points_cost = max(1, math.ceil(script.char_count / 10000)) * points_per_10000

    try:
        consume_or_fail(db, current_user.id, points_cost,
                        f"评分剧本《{script.title}》(模型: {model_config.provider} {model_config.model_name})")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    placeholder = Score(
        script_id=script_id,
        user_id=current_user.id,
        model_config_id=model_config.id,
        points_cost=points_cost,
        interestingness=0, popularity=0, logic=0,
        action_smoothness=0, plot_smoothness=0,
        overall=0, analysis="", suggestions="",
        progress="正在准备评分...",
    )
    db.add(placeholder)
    db.commit()
    db.refresh(placeholder)

    task = asyncio.create_task(
        _run_scoring_background(placeholder.id, script.content, model_config.id, current_user.id)
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return ScoreResponse(
        id=placeholder.id, script_id=placeholder.script_id, user_id=placeholder.user_id,
        model_config_id=placeholder.model_config_id, points_cost=placeholder.points_cost,
        interestingness=0, popularity=0, logic=0, action_smoothness=0,
        plot_smoothness=0, overall=0, analysis="", suggestions="",
        progress=placeholder.progress, elapsed=None,
        created_at=placeholder.created_at,
        provider=model_config.provider, model_name=model_config.model_name,
    )


@router.get("/scores/{score_id}/progress", response_model=ScoreProgressResponse)
def get_score_progress(
    score_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    score = db.query(Score).filter(Score.id == score_id).first()
    if not score:
        raise HTTPException(status_code=404, detail="评分记录不存在")
    if score.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权查看")
    return ScoreProgressResponse(
        id=score.id,
        script_id=score.script_id,
        progress=score.progress or ("评分完成" if score.overall > 0 else "正在准备..."),
        overall=score.overall,
        elapsed=score.elapsed,
        created_at=score.created_at,
    )


@router.get("/scores/history", response_model=list[ScoreResponse])
def score_history(page: int = 1, page_size: int = 20, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    rows = (
        db.query(Score)
        .filter(Score.user_id == current_user.id)
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
            created_at=s.created_at, elapsed=s.elapsed,
            progress=s.progress,
            provider=s.model_config.provider if s.model_config else None,
            model_name=s.model_config.model_name if s.model_config else None,
        ))
    return result


@router.get("/scores/{score_id}", response_model=ScoreResponse)
def get_score(score_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    score = db.query(Score).filter(Score.id == score_id).first()
    if not score:
        raise HTTPException(status_code=404, detail="评分记录不存在")
    if score.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权查看")
    return ScoreResponse(
        id=score.id, script_id=score.script_id, user_id=score.user_id,
        model_config_id=score.model_config_id, points_cost=score.points_cost,
        interestingness=score.interestingness, popularity=score.popularity,
        logic=score.logic, action_smoothness=score.action_smoothness,
        plot_smoothness=score.plot_smoothness, overall=score.overall,
        analysis=score.analysis, suggestions=score.suggestions,
        created_at=score.created_at, elapsed=score.elapsed,
        progress=score.progress,
        provider=score.model_config.provider if score.model_config else None,
        model_name=score.model_config.model_name if score.model_config else None,
    )


@router.get("/points/log", response_model=list[PointsLogResponse])
def points_log(
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(PointsLog)
        .filter(PointsLog.user_id == current_user.id)
        .order_by(PointsLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return rows
