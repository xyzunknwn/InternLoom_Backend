from fastapi import APIRouter
router = APIRouter(prefix="/api/v1/jobs")

@router.post("/")
def get_jobs():
    return {"status": "success", "message": "Jobs list active"}