from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import models, schemas, auth
from database import get_db

router = APIRouter(prefix="/api/v1/students", tags=["Students"])

# Pydantic schema for updating profile
class ProfileUpdate(BaseModel):
    name: str
    college: str
    branch: str
    graduation_year: int
    cgpa: Optional[float] = None
    skills: List[str] = []
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    bio: Optional[str] = None
    resume_url: Optional[str] = None

@router.get("/profile", response_model=schemas.APIResponse)
def get_profile(current_user: models.User = Depends(auth.get_current_student), db: Session = Depends(get_db)):
    """Gets the logged-in student's profile and dynamically calculates completeness."""
    profile = db.query(models.StudentProfile).filter(models.StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return schemas.APIResponse(
        status="success", 
        data={"profile": profile, "completeness_score": profile.completeness_score}
    )

@router.put("/profile", response_model=schemas.APIResponse)
def update_profile(update_data: ProfileUpdate, current_user: models.User = Depends(auth.get_current_student), db: Session = Depends(get_db)):
    """Updates the profile. Only accessible by the owner."""
    profile = db.query(models.StudentProfile).filter(models.StudentProfile.user_id == current_user.id).first()
    
    # Update fields dynamically
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(profile, key, value)
        
    db.commit()
    db.refresh(profile)
    
    return schemas.APIResponse(
        status="success", 
        message="Profile updated successfully.",
        meta={"completeness_score": profile.completeness_score}
    )