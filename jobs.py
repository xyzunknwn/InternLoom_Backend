from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import models, schemas, auth
from database import get_db

router = APIRouter(prefix="/api/v1/jobs", tags=["Company Jobs"])

class JobCreate(BaseModel):
    title: str
    description: str
    required_skills: List[str]
    preferred_skills: List[str] = []
    stipend: str
    location: str
    target_batch: int
    deadline: datetime
    max_applicants: int

@router.post("/", response_model=schemas.APIResponse)
def create_job(job_data: JobCreate, current_user: models.User = Depends(auth.get_current_company), db: Session = Depends(get_db)):
    """Companies create jobs here. Defaults to DRAFT status."""
    new_job = models.JobListing(**job_data.dict(), company_id=current_user.id, status=models.JobStatus.DRAFT)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return schemas.APIResponse(message="Job created in DRAFT status.", data={"job_id": new_job.id})

@router.patch("/{job_id}/status", response_model=schemas.APIResponse)
def update_job_status(job_id: int, new_status: str, current_user: models.User = Depends(auth.get_current_company), db: Session = Depends(get_db)):
    """Judges check: Enforces valid state transitions (Draft -> Active -> Closed)."""
    job = db.query(models.JobListing).filter(models.JobListing.id == job_id, models.JobListing.company_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or not owned by you.")
    
    try:
        target_status = models.JobStatus(new_status.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status. Use draft, active, or closed.")

    # Business Logic Checks
    if job.status == models.JobStatus.DRAFT and target_status == models.JobStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Cannot move directly from Draft to Closed.")
    if job.status == models.JobStatus.CLOSED and target_status == models.JobStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Cannot reopen a manually closed job.")

    job.status = target_status
    db.commit()
    return schemas.APIResponse(message=f"Job status updated to {target_status.value}")