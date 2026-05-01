import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import User, Script
from schemas import ScriptResponse, ScriptDetailResponse, TextScriptCreate
from services.file_parser import parse_file
from config import UPLOAD_DIR

router = APIRouter(prefix="/api/scripts", tags=["剧本"])

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/text", response_model=ScriptResponse)
def create_text_script(
    req: TextScriptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = req.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="剧本内容不能为空")
    script = Script(
        user_id=current_user.id,
        title=req.title.strip() or "未命名剧本",
        content=content,
        char_count=len(content),
    )
    db.add(script)
    db.commit()
    db.refresh(script)
    return script


@router.post("/upload", response_model=ScriptResponse)
async def upload_script(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 校验文件类型
    ext = os.path.splitext(file.filename or "untitled.txt")[1].lower()
    if ext not in (".txt", ".docx", ".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 txt / docx / pdf 格式")

    # 保存文件
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    content_bytes = await file.read()
    with open(filepath, "wb") as f:
        f.write(content_bytes)

    # 解析文件
    try:
        title, content = parse_file(filepath, file.filename or "untitled")
    except Exception as e:
        os.remove(filepath)
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")

    char_count = len(content)

    script = Script(
        user_id=current_user.id,
        title=title,
        content=content,
        char_count=char_count,
        filename=file.filename,
    )
    db.add(script)
    db.commit()
    db.refresh(script)
    return script


@router.get("", response_model=list[ScriptResponse])
def list_scripts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scripts = (
        db.query(Script)
        .filter(Script.user_id == current_user.id)
        .order_by(Script.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return scripts


@router.get("/{script_id}", response_model=ScriptDetailResponse)
def get_script(
    script_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    if script.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权查看")
    return script


@router.delete("/{script_id}")
def delete_script(
    script_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    if script.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权删除")
    db.delete(script)
    db.commit()
    return {"ok": True}
