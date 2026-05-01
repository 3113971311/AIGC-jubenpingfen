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

router = APIRouter(prefix="/api", tags=["feedback"])


@router.post("/feedback")
def submit_feedback(
    req: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit user feedback via email"""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        return {
            "ok": False,
            "message": "SMTP 未配置，请联系管理员设置 SMTP_USERNAME 和 SMTP_PASSWORD 环境变量",
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
        msg["From"] = SMTP_USERNAME
        msg["To"] = FEEDBACK_RECIPIENT
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        if SMTP_USE_TLS:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15)

        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_USERNAME, FEEDBACK_RECIPIENT, msg.as_string())
        server.quit()

        return {"ok": True, "message": "反馈已发送，感谢您的意见！"}
    except smtplib.SMTPAuthenticationError:
        return {"ok": False, "message": "邮件发送失败：SMTP 认证失败，请检查邮箱账号和授权码"}
    except Exception as e:
        return {"ok": False, "message": f"邮件发送失败：{e}"}


def _now_str():
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
