from typing import Annotated
from fastapi import FastAPI, HTTPException, status, Depends, APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import models
from database import get_db
from schemas import PostCreate, PostResponse,  PostUpdate

router = APIRouter()



@router.get("", response_model=list[PostResponse])
async def get_posts(db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)))
    posts = result.scalars().all()
    return posts

@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post:PostCreate, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).options(selectinload(models.User.posts)).where(models.User.id == post.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user with the provided user_id does not exist")
    new_post = models.Post(
        title = post.title,
        content = post.content,
        user_id = post.user_id
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return new_post


@router.get("/{id}", response_model=PostResponse)
async def get_post(id: int, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == id))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} was not found")
    

@router.put("/{id}", response_model=PostResponse)
async def update_post_full(id: int, newPost:PostCreate, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} was not found")

    if newPost.user_id == post.user_id:
        result = await db.execute(select(models.User).where(models.User.id == post.user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user was not found")
        
        post.title = newPost.title
        post.content = newPost.content

        await db.commit()
        await db.refresh(post, attribute_names=["author"])
        return post
    

@router.patch("/{id}", response_model=PostResponse)
async def update_post_partial(id: int, newPost:PostUpdate, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} was not found")

    newData = newPost.model_dump(exclude_unset=True)
    for field, value in newData.items():
        setattr(post, field, value)
    
    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post
    
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(id:int, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")

    await db.delete(post)
    await db.commit()
        