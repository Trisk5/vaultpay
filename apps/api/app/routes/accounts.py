from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case
from ..db import get_db
from ..models import Account, LedgerEntry
from ..security.deps import require_user

router = APIRouter(prefix="/accounts", tags=["accounts"])

class CreateAccountIn(BaseModel):
    currency: str = "GBP"

@router.post("")
def create_account(
    body: CreateAccountIn,
    db: Session = Depends(get_db),
    user=Depends(require_user(["accounts:read"])),
):
    acc = Account(user_id=user.id, currency=body.currency.upper())
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return {"id": acc.id, "currency": acc.currency, "status": acc.status}

@router.get("/{account_id}/balance")
def get_balance(
    account_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_user(["accounts:read"])),
):
    acc = db.get(Account, account_id)
    if not acc or acc.user_id != user.id:
        raise HTTPException(404, "Account not found")

    # balance = sum(credit) - sum(debit)
    q = select(
        func.coalesce(func.sum(
            case(
                (LedgerEntry.entry_type == "credit", LedgerEntry.amount),
                (LedgerEntry.entry_type == "debit", -LedgerEntry.amount),
                else_=0
            )
        ), 0)
    ).where(LedgerEntry.account_id == account_id)

    balance = db.execute(q).scalar_one()
    return {"account_id": account_id, "currency": acc.currency, "balance": str(balance)}