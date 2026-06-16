from typing import Annotated
from fastapi import FastAPI, HTTPException, status, Depends, APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import models
from database import get_db
from schemas import PostResponse, UserCreate, UserResponse, UserUpdate

router = APIRouter()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user:UserCreate, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select (models.User).where (models.User.username == user.username),)

    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username already exists")
    
    result = await db.execute(select (models.User).where (models.User.email == user.email),)

    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists")
    
    new_user = models.User(
        username = user.username,
        email = user.email
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user

@router.patch("/{id}", response_model=UserResponse)
async def update_user_partial(id: int, newUserData:UserUpdate, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with id: {id} was not found")

    if newUserData.username and newUserData.username != user.username:
        result = await db.execute(select(models.User).where(models.User.username == newUserData.username))
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username already exists")
        
    if newUserData.email and newUserData.email != user.email:
        result = await db.execute(select(models.User).where(models.User.email == newUserData.email))
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists")

    newData = newUserData.model_dump(exclude_unset=True)
    for field, value in newData.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    return user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(userid:int, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == userid),)

    user = result.scalars().first()

    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user was not found")


@router.delete("/{userid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(id:int, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    
    await db.delete(user)
    await db.commit()


@router.get("/{userid}/posts", response_model=list[PostResponse])
async def get_user_posts(userid:int, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == userid))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    
    result = await db.execute(select (models.Post).options(selectinload(models.Post.author)). where(models.Post.user_id == userid))
    posts = result.scalars().all()
    return posts
