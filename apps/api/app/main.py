from fastapi import FastAPI, Request
from .db import Base, engine
from .routes.auth import router as auth_router
from .routes.accounts import router as accounts_router
from .routes.transfers import router as transfers_router

app = FastAPI(title="VaultPay", version="0.1")

# DEV ONLY: create tables automatically (for portfolio bootstrap).
# For production-like, replace with Alembic migrations.
Base.metadata.create_all(bind=engine)

@app.middleware("http")
async def capture_raw_body(request: Request, call_next):
    request.state.raw_body = await request.body()
    return await call_next(request)

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(transfers_router)