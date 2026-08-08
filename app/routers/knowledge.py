from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, crud, models
from ..database import get_db
from ..auth import get_current_tenant_flexible

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("", response_model=schemas.KnowledgeOut)
def add_knowledge(
    payload: schemas.KnowledgeCreate,
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible),
):
    return crud.add_knowledge(db, tenant.id, payload.question, payload.answer)


@router.get("", response_model=List[schemas.KnowledgeOut])
def list_knowledge(
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible),
):
    return crud.get_active_knowledge(db, tenant.id)


@router.delete("/{entry_id}")
def delete_knowledge(
    entry_id: str,
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible),
):
    success = crud.delete_knowledge(db, tenant.id, entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return {"status": "deleted", "id": entry_id}
