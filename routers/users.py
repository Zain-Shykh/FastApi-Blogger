from typing import Annotated
from fastapi import FastAPI, HTTPException, status, Depends, APIRouter, UploadFile, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import models
from database import get_db
from schemas import PostResponse, UserCreate, UserPublic, UserUpdate, UserPrivate, Token, PaginatedPostsResponse
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from auth import hash_password, verify_password, create_access_token, CurrentUser
from config import settings
from PIL import UnidentifiedImageError
from imageutils import delete_profile_image, process_profile_image
from starlette.concurrency import run_in_threadpool


router = APIRouter()


@router.post("", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def create_user(user:UserCreate, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select (models.User).where (func.lower(models.User.username) == user.username.lower()),)

    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username already exists")
    
    result = await db.execute(select (models.User).where (func.lower(models.User.email) == user.email.lower()),)

    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists")
    
    new_user = models.User(
        username = user.username,
        email = user.email.lower(),
        password_hash = hash_password(user.password)
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data:Annotated[OAuth2PasswordRequestForm, Depends()], db:Annotated[AsyncSession, Depends(get_db)]):
    # Look up for user by email (case - insensitive)
    # Note: OAuth2PasswordRequestForm has a username field, but we will treat it as email for our authentication
    result = await db.execute(select(models.User).where(func.lower(models.User.email) == form_data.username.lower()))
    user = result.scalars().first()

    # Verify user exists and password is correct
    # Not reveal which one failed for security reasons
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid email or password", headers={"WWW-Authenticate": "Bearer"})
    
    # Create access token with user id as subject
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)

    return Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user: CurrentUser):
    return current_user

@router.patch("/{id}", response_model=UserPrivate)
async def update_user_partial(id: int, newUserData:UserUpdate,current_user:CurrentUser, db:Annotated[AsyncSession, Depends(get_db)]):
    
    if id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="you are not authorized to update this user")
    
    result = await db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with id: {id} was not found")

    if newUserData.username and newUserData.username != user.username:
        result = await db.execute(select(models.User).where(func.lower(models.User.username) == newUserData.username.lower()))
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username already exists")
        
    if newUserData.email and newUserData.email.lower() != user.email.lower():
        result = await db.execute(select(models.User).where(func.lower(models.User.email) == newUserData.email.lower()))
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists")

    newData = newUserData.model_dump(exclude_unset=True)
    for field, value in newData.items():
        if field == "email":
            value = value.lower()
        if field == "image_file":
            continue  # Skip updating image_file directly
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    return user

@router.get("/{user_id}", response_model=UserPublic)
async def get_user(userid:int, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == userid),)

    user = result.scalars().first()

    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user was not found")


@router.delete("/{userid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(id:int, current_user:CurrentUser, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()

    if id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="you are not authorized to delete this user")

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    oldfilename = user.image_file
    
    await db.delete(user)
    await db.commit()

    if oldfilename:
        delete_profile_image(oldfilename)


@router.get("/{user_id}/posts", response_model=PaginatedPostsResponse)
async def get_user_posts(user_id:int, db:Annotated[AsyncSession, Depends(get_db)], skip:Annotated[int, Query(ge=0)] = 0, limit: Annotated[int | None, Query(ge=1, le=100)] = None):
    if limit is None:
        limit = settings.posts_per_page

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not Found.")
    
    count_result = await db.execute(select(func.count()).select_from(models.Post).where(models.Post.user_id == user_id))
    total = count_result.scalar() or 0

    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id == user_id).order_by(models.Post.date_posted.desc()).offset(skip).limit(limit))
    posts = result.scalars().all()
    has_more = skip + len(posts) < total

    return PaginatedPostsResponse(
        posts=[PostResponse.model_validate(post) for post in posts],
        total = total,
        skip = skip,
        limit = limit,
        has_more = has_more,
    )


@router.patch("/{userid}/picture", response_model=UserPrivate)
async def upload_profile_picture(user_id:int, file:UploadFile, current_user:CurrentUser, db:Annotated[AsyncSession, Depends(get_db)]):
    if current_user != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this picture")
    
    content = await file.read()

    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file too large. Maximum size is {settings.max_upload_size_bytes} MB")
    
    try:
        new_filename = await run_in_threadpool(process_profile_image, content)

    except UnidentifiedImageError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file. Please Upload (Jpeg/PNG)") from err
    
    old_filename = current_user.image_file

    current_user.image_file = new_filename

    await db.commit()
    await db.refresh(current_user)

    if old_filename:
        delete_profile_image(old_filename)

    return current_user
    


@router.delete("/{user_id}/picture", response_model=UserPrivate)
async def delete_user_picture(user_id:int, current_user:CurrentUser, db:Annotated[AsyncSession, Depends(get_db)]):
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this User's Picture")
    
    old_filename = current_user.image_file

    if old_filename is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No profile picture to delete.")
    
    current_user.image_file = None

    await db.commit()
    await db.refresh(current_user)

    delete_profile_image(old_filename)

    return current_user












