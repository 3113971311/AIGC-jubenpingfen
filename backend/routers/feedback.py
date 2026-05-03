import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth import get_current_user
from config import SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_USE_TLS, FEEDBACK_RECIPIENT
from database import get_db
from models import User
from schemas import FeedbackRequest
from services.system_config import get_config

router = APIRouter(prefix="/api", tags=["feedback"])


def _get_smtp_config(db: Session):
    """Read SMTP settings from system_config, falling back to env/config defaults."""
    return {
        "host": get_config(db, "smtp_host", SMTP_HOST),
        "port": int(get_config(db, "smtp_port", str(SMTP_PORT))),
        "username": get_config(db, "smtp_username", SMTP_USERNAME),
        "password": get_config(db, "smtp_password", SMTP_PASSWORD),
        "use_tls": get_config(db, "smtp_use_tls", "true" if SMTP_USE_TLS else "false").lower() == "true",
        "recipient": get_config(db, "feedback_recipient", FEEDBACK_RECIPIENT),
    }


@router.post("/feedback")
def submit_feedback(
    req: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit user feedback via email"""
    cfg = _get_smtp_config(db)
    if not cfg["username"] or not cfg["password"]:
        return {
            "ok": False,
            "message": "SMTP 未配置，请前往系统设置中配置邮箱",
        }

    subject = f"[剧本评分系统] 用户反馈 - {current_user.username}"
    body = f"""收到一条新的用户反馈：

用户名：{current_user.username}
联系方式：{req.contact or '未填写'}
时间：{_now_str()}

反馈内容：
{req.content}
"""

    try:
        msg = MIMEMultipart()
        msg["From"] = cfg["username"]
        msg["To"] = cfg["recipient"]
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        if cfg["use_tls"]:
            server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=15)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=15)

        server.login(cfg["username"], cfg["password"])
        server.sendmail(cfg["username"], cfg["recipient"], msg.as_string())
        server.quit()

        return {"ok": True, "message": "反馈已发送，感谢您的意见！"}
    except smtplib.SMTPAuthenticationError:
        return {"ok": False, "message": "邮件发送失败：SMTP 认证失败，请检查邮箱账号和授权码"}
    except Exception as e:
        return {"ok": False, "message": f"邮件发送失败：{e}"}


def _now_str():
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
