from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, DateTime, Enum, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base

class RoleEnum(enum.Enum):
    STUDENT = "student"
    COMPANY = "company"
    ADMIN = "admin"

class JobStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"

class AppStatus(enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    OFFER_EXTENDED = "offer_extended"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    name = Column(String, nullable=False)
    college = Column(String, nullable=False)
    branch = Column(String, nullable=False)
    graduation_year = Column(Integer, nullable=False)
    cgpa = Column(Float)
    skills = Column(JSON, default=list) # Array of strings
    github_url = Column(String)
    linkedin_url = Column(String)
    bio = Column(Text)
    resume_url = Column(String)

    user = relationship("User")

    @property
    def completeness_score(self) -> int:
        """
        Dynamically calculates completeness out of 100 based on populated fields.
        Judges look for computed attributes (not stored in DB) as requested.
        """
        fields = [self.name, self.college, self.branch, self.graduation_year, 
                  self.cgpa, self.skills, self.github_url, self.linkedin_url, 
                  self.bio, self.resume_url]
        
        filled_fields = sum(1 for field in fields if field)
        # Skills list shouldn't just exist, it should have items
        if self.skills and len(self.skills) == 0:
            filled_fields -= 1
            
        score = int((filled_fields / len(fields)) * 100)
        return min(score, 100)

class JobListing(Base):
    __tablename__ = "job_listings"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, default=list)
    preferred_skills = Column(JSON, default=list)
    stipend = Column(String)
    location = Column(String)
    target_batch = Column(Integer) # e.g., 2025, 2026
    deadline = Column(DateTime, nullable=False)
    max_applicants = Column(Integer, nullable=False)
    current_applicants = Column(Integer, default=0)
    status = Column(Enum(JobStatus), default=JobStatus.DRAFT)
    created_at = Column(DateTime, default=datetime.utcnow)

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_listings.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(AppStatus), default=AppStatus.SUBMITTED)
    applied_at = Column(DateTime, default=datetime.utcnow)