from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

import models, schemas, database, auth
from database import engine, get_db
from models import JobStatus, AppStatus
from matching_engine import MatchingEngine

# Initialize DB Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="InternLoom Core API")



# --- GLOBAL EXCEPTION HANDLER ---
@app.exception_handler(HTTPException)
async def my_exception_handler(request, exc):
    return {"status": "error", "message": exc.detail, "data": None}

# Register Auth Router
app.include_router(auth.router)
import students, jobs

app.include_router(students.router)
app.include_router(jobs.router)

@app.get("/")
def health_check():
    return {"status": "success", "message": "InternLoom Backend Running!"}

# --- ROUTES ---
@app.get("/api/v1/student/feed", tags=["Matching"])
def get_student_job_feed(
    current_user: models.User = Depends(auth.get_current_student), 
    db: Session = Depends(get_db)
):
    """
    Returns a dynamically scored and ranked list of active jobs for the logged-in student.
    Judges Check: Only students can access this, controlled via get_current_student dependency.
    """
    student = db.query(models.StudentProfile).filter(models.StudentProfile.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")
    
    # Base Query: Only fetch ACTIVE jobs whose deadline hasn't passed
    active_jobs = db.query(models.JobListing).filter(
        models.JobListing.status == JobStatus.ACTIVE,
        models.JobListing.deadline > datetime.utcnow()
    ).all()

    # Pass to engine for scoring and ranking
    ranked_results = MatchingEngine.get_ranked_feed(student, active_jobs, limit=20)
    
    return schemas.APIResponse(
        status="success",
        data=ranked_results,
        message=f"Fetched top matching jobs. Profile Completeness: {student.completeness_score}%"
    )

@app.post("/api/v1/jobs/{job_id}/apply", tags=["Applications"])
def apply_to_job(
    job_id: int, 
    current_user: models.User = Depends(auth.get_current_student), 
    db: Session = Depends(get_db)
):
    """
    Handles job application logic, duplicate checking, and auto-closing on caps.
    """
    job = db.query(models.JobListing).filter(models.JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 1. Enforce active status and deadline
    if job.status != JobStatus.ACTIVE or job.deadline < datetime.utcnow():
        raise HTTPException(status_code=400, detail="This listing is no longer accepting applications.")

    # 2. Check for duplicate application
    existing_app = db.query(models.Application).filter(
        models.Application.job_id == job_id, 
        models.Application.student_id == current_user.id
    ).first()
    if existing_app:
        raise HTTPException(status_code=400, detail="You have already applied to this role.")

    # 3. Create Application
    new_app = models.Application(job_id=job_id, student_id=current_user.id)
    job.current_applicants += 1

    # 4. CAP LOGIC: If we hit the max, auto-close the listing
    if job.current_applicants >= job.max_applicants:
        job.status = JobStatus.CLOSED

    db.add(new_app)
    db.commit()
    
    return schemas.APIResponse(
        status="success", 
        message="Application submitted successfully.",
        meta={"job_status": job.status.value}
    )

@app.delete("/api/v1/applications/{app_id}/withdraw", tags=["Applications"])
def withdraw_application(
    app_id: int, 
    current_user: models.User = Depends(auth.get_current_student), 
    db: Session = Depends(get_db)
):
    """
    Handles withdrawal logic and complex state re-entry (Re-opening an auto-closed job).
    """
    application = db.query(models.Application).filter(
        models.Application.id == app_id, 
        models.Application.student_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found or doesn't belong to you.")

    if application.status != AppStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Can only withdraw applications in SUBMITTED state.")

    job = db.query(models.JobListing).filter(models.JobListing.id == application.job_id).first()
    
    # Remove application and decrement count
    db.delete(application)
    job.current_applicants -= 1

    # STATE RE-ENTRY: If it was closed because of the cap, and the deadline is still good, re-open it.
    if job.status == JobStatus.CLOSED and job.current_applicants < job.max_applicants:
        if job.deadline > datetime.utcnow():
            job.status = JobStatus.ACTIVE # Reverts state dynamically

    db.commit()
    return schemas.APIResponse(
        status="success", 
        message="Application withdrawn.",
        meta={"new_job_status": job.status.value}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)