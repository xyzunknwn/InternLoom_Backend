from pydantic import BaseModel, EmailStr, validator, Field
from typing import List, Optional, Any
from datetime import datetime
import enum

# --- ENVELOPE FORMAT ---
# All endpoints return this exact structure to satisfy the consistency rule
class APIResponse(BaseModel):
    status: str = "success"
    data: Optional[Any] = None
    message: Optional[str] = None
    meta: Optional[dict] = None # For pagination or matching scores

# --- USER REGISTRATION ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "student"

    @validator("email")
    def validate_college_email(cls, v):
        """Reject personal emails immediately at the API level."""
        forbidden = ["gmail.com", "yahoo.com", "outlook.com"]
        domain = v.split("@")[-1].lower()
        if domain in forbidden:
            raise ValueError(f"Personal emails ({domain}) are not allowed. Use a college email.")
        return v

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    is_verified: bool

    class Config:
        orm_mode = True

# --- JOB LISTINGS ---
class JobResponse(BaseModel):
    id: int
    title: str
    company_id: int
    required_skills: List[str]
    preferred_skills: List[str]
    current_applicants: int
    max_applicants: int
    status: str
    deadline: datetime
    
    class Config:
        orm_mode = True

class MatchedJobResponse(BaseModel):
    job: JobResponse
    match_score: float
    match_reasoning: str # Explains why they matched (bonus transparency)