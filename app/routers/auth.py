from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud, models
from ..database import get_db
from ..security import hash_password, verify_password, create_access_token
from ..auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=schemas.AuthOut)
def signup(payload: schemas.SignupIn, db: Session = Depends(get_db)):
    if db.query(models.Tenant).filter(models.Tenant.slug == payload.slug).first():
        raise HTTPException(status_code=400, detail="This workspace url is already taken")
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    tenant = crud.create_tenant(db, payload.business_name, payload.slug)
    user = crud.create_user(db, tenant.id, payload.email, hash_password(payload.password))
    token = create_access_token(user.id, tenant.id)
    return schemas.AuthOut(token=token, tenant=tenant, email=user.email)


@router.post("/login", response_model=schemas.AuthOut)
def login(payload: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user.id, user.tenant_id)
    return schemas.AuthOut(token=token, tenant=user.tenant, email=user.email)


@router.get("/me", response_model=schemas.MeOut)
def me(user: models.User = Depends(get_current_user)):
    return schemas.MeOut(tenant=user.tenant, email=user.email)
