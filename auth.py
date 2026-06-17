from datetime import datetime, timedelta, UTC
import jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from config import settings
from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
import models
from sqlalchemy import select
import hashlib
import secrets


password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")

def hash_password(password:str)->str:
    return password_hash.hash(password)

def verify_password(password:str, hashed_password:str)->bool:
    return password_hash.verify(password, hashed_password)

def generate_reset_token()->str:
    return secrets.token_urlsafe(32)

def hash_reset_token(token:str)->str:
    return hashlib.sha256(token.encode()).hexdigest()

def create_access_token(data:dict, expires_delta:timedelta|None = None)->str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY.get_secret_value(), algorithm=settings.algorithm)

    return encoded_jwt

def verify_access_token(token:str)->str|None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY.get_secret_value(), algorithms=[settings.algorithm], options={"require": ["exp", "sub"]})
    except jwt.InvalidTokenError:
        return None
    else:
        return payload.get("sub")
    

async def get_current_user(token:Annotated[str, Depends(oauth2_scheme)], db:Annotated[AsyncSession, Depends(get_db)])->models.User:
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired token", headers={"WWW-Authenticate":"Bearer"})
    try:
        user_id_int = int(user_id)
    except(TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired token", headers={"WWW-Authenticate":"Bearer"})
    

    result = await db.execute(select(models.User).where(models.User.id == user_id_int))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found", headers={"WWW-Authenticate":"Bearer"})

    return user


CurrentUser = Annotated[models.User, Depends(get_current_user)]











