from sqlalchemy.orm import Session

from models import User, PointsLog


def consume_or_fail(db: Session, user_id: int, amount: int, reason: str) -> int:
    """原子扣减积分。成功返回扣减后余额，积分不足或用户不存在时抛出 ValueError。"""
    user = db.query(User).with_for_update().filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户不存在")
    if user.points < amount:
        raise ValueError(f"积分不足，需要 {amount} 积分，当前剩余 {user.points} 积分")
    user.points -= amount
    balance_after = user.points
    log = PointsLog(user_id=user_id, amount=-amount, reason=reason, balance_after=balance_after)
    db.add(log)
    db.commit()
    return balance_after


def grant_points(db: Session, user_id: int, amount: int, reason: str) -> int:
    """发放积分，返回发放后余额。仅用于管理员操作，不用于退款。"""
    if amount <= 0:
        raise ValueError("发放金额必须大于0")
    user = db.query(User).with_for_update().filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户不存在")
    user.points += amount
    balance_after = user.points
    log = PointsLog(user_id=user_id, amount=amount, reason=reason, balance_after=balance_after)
    db.add(log)
    db.commit()
    return balance_after


def refund_points(db: Session, user_id: int, amount: int, reason: str):
    """内部退款（不做业务校验），直接加回积分"""
    user = db.query(User).with_for_update().filter(User.id == user_id).first()
    if not user:
        return
    user.points += amount
    log = PointsLog(user_id=user_id, amount=amount, reason=reason, balance_after=user.points)
    db.add(log)
    db.commit()
