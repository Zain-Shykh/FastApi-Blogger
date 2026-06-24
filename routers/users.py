from typing import Annotated
from fastapi import FastAPI, HTTPException, status, Depends, APIRouter, UploadFile, Query, BackgroundTasks
from sqlalchemy import select, func, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import models
from database import get_db
from schemas import PostResponse, UserCreate, UserPublic, UserUpdate, UserPrivate, Token, PaginatedPostsResponse, ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest
from datetime import timedelta, UTC, datetime
from fastapi.security import OAuth2PasswordRequestForm
from auth import hash_password, verify_password, create_access_token, CurrentUser, generate_reset_token, hash_reset_token
from config import settings
from PIL import UnidentifiedImageError
from imageutils import delete_profile_image, process_profile_image, upload_profile_image
from starlette.concurrency import run_in_threadpool
from email_utils import send_password_reset_email

from botocore.exceptions import ClientError

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
    access_token = create_access_token(data={"sub": str(user.id), "is_admin": user.is_admin}, expires_delta=access_token_expires)

    return Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user: CurrentUser):
    return current_user

@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(request_data: ForgotPasswordRequest, background_tasks: BackgroundTasks, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(func.lower(models.User.email) == request_data.email.lower()))
    user = result.scalars().first()

    if user:
        await db.execute(sql_delete(models.PasswordResetToken).where(models.PasswordResetToken.user_id == user.id))
        # Generate a password reset token and save it to the database
        token = generate_reset_token()
        token_hash = hash_reset_token(token)
        expires_at = datetime.now(UTC) + timedelta(minutes=settings.reset_token_expire_minutes)

        reset_token = models.PasswordResetToken(
            token_hash=token_hash,
            user_id=user.id,
            expires_at=expires_at
        )

        db.add(reset_token)
        await db.commit()

        # Send password reset email in the background
        background_tasks.add_task(send_password_reset_email, to_email=user.email, username=user.username, token=token)

    # Always return 202 Accepted to prevent email enumeration
    return {"message": "If an account with that email exists, a password reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(request_data: ResetPasswordRequest, db:Annotated[AsyncSession, Depends(get_db)]):
    # Verify the reset token
    result = await db.execute(select(models.PasswordResetToken).where(models.PasswordResetToken.token_hash == hash_reset_token(request_data.token)))
    reset_token = result.scalars().first()

    if not reset_token :
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    if reset_token.expires_at < datetime.now(UTC):
        await db.delete(reset_token)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    # Find the user associated with the reset token
    result = await db.execute(select(models.User).where(models.User.id == reset_token.user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Update the user's password
    user.password_hash = hash_password(request_data.new_password) # type: ignore
    await db.execute(sql_delete(models.PasswordResetToken).where(models.PasswordResetToken.user_id == user.id))
    await db.commit()

    return {"message": "Password has been reset successfully"}


@router.patch("/me/password", status_code=status.HTTP_200_OK)
async def change_password(password_data: ChangePasswordRequest, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    # Verify the current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    # Update the user's password
    current_user.password_hash = hash_password(password_data.new_password)  # type: ignore
    await db.execute(sql_delete(models.PasswordResetToken).where(models.PasswordResetToken.user_id == current_user.id))
    await db.commit()

    return {"message": "Password has been changed successfully"}

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
        await delete_profile_image(oldfilename)


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
        processed_bytes, new_filename = await run_in_threadpool(process_profile_image, content)

    except UnidentifiedImageError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file. Please Upload (Jpeg/PNG)") from err
    

    try:
        await upload_profile_image(processed_bytes, new_filename)
    except ClientError as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload image. Please try again later.") from err

    old_filename = current_user.image_file

    current_user.image_file = new_filename

    await db.commit()
    await db.refresh(current_user)

    if old_filename:
        await delete_profile_image(old_filename)

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

    await delete_profile_image(old_filename)

    return current_user












