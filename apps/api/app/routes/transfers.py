from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field
from decimal import Decimal
from typing_extensions import Annotated
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case
from ..db import get_db
from ..models import Account, LedgerEntry, Transfer
from ..security.deps import require_user
from ..security.rate_limit import ratelimit_or_429

router = APIRouter(prefix="/transfers", tags=["transfers"])

Amount = Annotated[
    Decimal,
    Field(gt=0, max_digits=18, decimal_places=2)
]

class TransferIn(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Amount

def compute_balance(db: Session, account_id: int):
    q = select(
        func.coalesce(func.sum(
            case(
                (LedgerEntry.entry_type == "credit", LedgerEntry.amount),
                (LedgerEntry.entry_type == "debit", -LedgerEntry.amount),
                else_=0
            )
        ), 0)
    ).where(LedgerEntry.account_id == account_id)
    return db.execute(q).scalar_one()

@router.post("")
def create_transfer(
    body: TransferIn,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    user=Depends(require_user(["transfers:write"])),
):
    if not ratelimit_or_429(f"user:{user.id}:transfers"):
        raise HTTPException(429, "Rate limit exceeded")

    # Idempotency: if already exists, return previous
    existing = db.query(Transfer).filter(
        Transfer.user_id == user.id,
        Transfer.idempotency_key == idempotency_key
    ).first()
    if existing:
        return {
            "id": existing.id,
            "status": existing.status,
            "amount": str(existing.amount),
            "from_account_id": existing.from_account_id,
            "to_account_id": existing.to_account_id,
            "idempotency_key": existing.idempotency_key,
            "replayed": True,
        }

    from_acc = db.get(Account, body.from_account_id)
    to_acc = db.get(Account, body.to_account_id)
    if not from_acc or not to_acc:
        raise HTTPException(404, "Account not found")
    if from_acc.user_id != user.id:
        raise HTTPException(403, "Not your source account")

    # money-safe transaction
    try:
        bal = compute_balance(db, from_acc.id)
        if bal < body.amount:
            raise HTTPException(400, "Insufficient funds")

        t = Transfer(
            user_id=user.id,
            from_account_id=from_acc.id,
            to_account_id=to_acc.id,
            amount=body.amount,
            status="succeeded",
            idempotency_key=idempotency_key,
        )
        db.add(t)
        db.flush()  # get t.id before commit

        db.add(LedgerEntry(account_id=from_acc.id, entry_type="debit", amount=body.amount, ref=f"tr_{t.id}"))
        db.add(LedgerEntry(account_id=to_acc.id, entry_type="credit", amount=body.amount, ref=f"tr_{t.id}"))

        db.commit()
        db.refresh(t)
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(500, "Transfer failed")

    return {
        "id": t.id,
        "status": t.status,
        "amount": str(t.amount),
        "from_account_id": t.from_account_id,
        "to_account_id": t.to_account_id,
        "idempotency_key": t.idempotency_key,
        "replayed": False,
    }