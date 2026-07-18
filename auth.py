from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

import models, schemas
from database import get_db

# --- CONFIGURATION ---
SECRET_KEY = "internloom_super_secret_hackathon_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 1 # Hackathon requirement
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Bcrypt for password hashing (Prevents instant disqualification)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# OAuth2 scheme for extracting token from header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# --- HELPER FUNCTIONS ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- DEPENDENCIES (Middleware for Protected Routes) ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None or payload.get("type") == "refresh":
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_student(current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.RoleEnum.STUDENT:
        raise HTTPException(status_code=403, detail="Not authorized. Student access only.")
    return current_user

def get_current_company(current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.RoleEnum.COMPANY:
        raise HTTPException(status_code=403, detail="Not authorized. Company access only.")
    return current_user

# --- ENDPOINTS ---
@router.post("/register", response_model=schemas.APIResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        role_enum = models.RoleEnum(user.role.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'student' or 'company'.")

    new_user = models.User(
        email=user.email,
        password_hash=get_password_hash(user.password),
        role=role_enum,
        is_verified=False if role_enum == models.RoleEnum.STUDENT else True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if role_enum == models.RoleEnum.STUDENT:
        empty_profile = models.StudentProfile(user_id=new_user.id, name="", college="", branch="", graduation_year=0)
        db.add(empty_profile)
        db.commit()

    return schemas.APIResponse(
        status="success", message=f"{user.role.capitalize()} registered successfully.",
        data={"user_id": new_user.id, "email": new_user.email}
    )

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    return {
        "status": "success",
        "access_token": create_access_token(data={"sub": user.email, "role": user.role.value}),
        "refresh_token": create_refresh_token(data={"sub": user.email, "role": user.role.value}),
        "token_type": "bearer"
    }

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/refresh")
def refresh_access_token(request: RefreshRequest):
    try:
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return {
            "status": "success",
            "access_token": create_access_token(data={"sub": payload.get("sub"), "role": payload.get("role")}),
            "token_type": "bearer"
        }
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")