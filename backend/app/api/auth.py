from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional
from ..models.database import get_db

router = APIRouter()

SECRET_KEY = "super_secret_spotman_key_change_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class CredentialsChange(BaseModel):
    old_password: str
    new_password: str

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception

    async with get_db() as db:
        async with db.execute("SELECT * FROM users WHERE username = ?", (token_data.username,)) as cursor:
            user = await cursor.fetchone()
            if user is None:
                raise credentials_exception
            return user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    async with get_db() as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            count = (await cursor.fetchone())[0]

        if count == 0:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(form_data.password.encode('utf-8'), salt).decode('utf-8')
            await db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (form_data.username, hashed))
            await db.commit()

            async with db.execute("SELECT * FROM users WHERE username = ?", (form_data.username,)) as cursor:
                user = await cursor.fetchone()
        else:
            async with db.execute("SELECT * FROM users WHERE username = ?", (form_data.username,)) as cursor:
                user = await cursor.fetchone()

            if not user or not verify_password(form_data.password, user["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/change-credentials")
async def change_credentials(credentials: CredentialsChange, user: dict = Depends(get_current_user)):
    """Change the current user's password. The old password must match."""
    if not verify_password(credentials.old_password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    salt = bcrypt.gensalt()
    new_hashed = bcrypt.hashpw(credentials.new_password.encode('utf-8'), salt).decode('utf-8')

    async with get_db() as db:
        await db.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (new_hashed, user["username"])
        )
        await db.commit()

    return {"status": "success", "message": "Password updated successfully"}