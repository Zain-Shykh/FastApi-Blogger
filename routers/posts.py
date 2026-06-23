from typing import Annotated
from fastapi import FastAPI, HTTPException, status, Depends, APIRouter, Query, UploadFile, File, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import models
from database import get_db
from schemas import PostCreate, PostResponse, PostUpdate, PaginatedPostsResponse, CommentCreate, CommentResponse
from auth import CurrentUser
from config import settings
from imageutils import delete_post_thumbnail, process_post_thumbnail, upload_post_thumbnail
from starlette.concurrency import run_in_threadpool
from botocore.exceptions import ClientError


router = APIRouter()



@router.get("", response_model=PaginatedPostsResponse)
async def get_posts(db:Annotated[AsyncSession, Depends(get_db)], skip:Annotated[int, Query(ge=0)] = 0, limit: Annotated[int | None, Query(ge=0, le=100)]= None):
    
    if limit is None:
        limit = settings.posts_per_page

    count_result = await db.execute(select(func.count()).select_from(models.Post))
    total = count_result.scalar() or 0
    
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).order_by(models.Post.date_posted.desc()).offset(skip).limit(limit))
    posts = result.scalars().all()

    has_more = skip + len(posts) < total

    return PaginatedPostsResponse(
        posts=[PostResponse.model_validate(post) for post in posts],
        total = total,
        skip = skip,
        limit = limit,
        has_more = has_more,
    )

@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post:PostCreate, current_user:CurrentUser, db:Annotated[AsyncSession, Depends(get_db)]):
    new_post = models.Post(
        title = post.title,
        content = post.content,
        user_id = current_user.id
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
async def update_post_full(id: int, newPost:PostCreate,current_user:CurrentUser, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} was not found")
    
    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="you are not the owner of this post")

    post.title = newPost.title
    post.content = newPost.content

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post
    

@router.patch("/{id}", response_model=PostResponse)
async def update_post_partial(id: int, newPost:PostUpdate, current_user:CurrentUser, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} was not found")

    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="you are not the owner of this post")
    
    newData = newPost.model_dump(exclude_unset=True)
    for field, value in newData.items():
        setattr(post, field, value)
    
    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post
    
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(id:int,current_user:CurrentUser, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")

    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="you are not the owner of this post")

    await db.delete(post)
    await db.commit()


@router.patch("/{id}/image", response_model=PostResponse)
async def upload_post_image(id:int, image_file:UploadFile, current_user:CurrentUser, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")

    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="you are not the owner of this post")

    content = await image_file.read()

    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"image size exceeds the maximum limit of {settings.max_upload_size_bytes} bytes")

    try:
        processed_image, filename = await run_in_threadpool(process_post_thumbnail, content)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid image file")

    try:
        await upload_post_thumbnail(processed_image, filename)
    except ClientError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="failed to upload image to S3") from e

    old_file_name = post.image_file
    post.image_file = filename

    await db.commit()
    await db.refresh(post, attribute_names=["author"])

    if old_file_name:
        await delete_post_thumbnail(old_file_name)
    
    return post


@router.delete("/{id}/image", response_model=PostResponse)
async def delete_post_image(id:int, current_user:CurrentUser, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")

    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="you are not the owner of this post")

    old_file_name = post.image_file
    if old_file_name is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No picture to delete.")

    post.image_file = None

    await db.commit()
    await db.refresh(post, attribute_names=["author"])

    if old_file_name:
        await delete_post_thumbnail(old_file_name)

    return post


@router.post("/{id}/like", status_code=status.HTTP_200_OK)
async def like_post(id:int, current_user:CurrentUser, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")

    like_result = await db.execute(select(models.Like).where(models.Like.post_id == id, models.Like.user_id == current_user.id))
    existing_like = like_result.scalars().first()

    if existing_like:
        await db.delete(existing_like)
        await db.commit()
        return {"message": "post unliked successfully"}

    new_like = models.Like(user_id=current_user.id, post_id=id)
    db.add(new_like)
    await db.commit()
    return {"message": "post liked successfully"}


@router.post("/{id}/comments", response_model=CommentResponse)
async def create_comment(id: int, comment: CommentCreate, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")

    new_comment = models.Comment(content=comment.content, user_id=current_user.id, post_id=id)
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment, attribute_names=["user"])
    return new_comment


@router.delete("/{post_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(post_id: int, comment_id: int, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Comment).where(models.Comment.id == comment_id and models.Comment.post_id == post_id))
    comment = result.scalars().first()

    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="comment not found")

    if comment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="you are not the owner of this comment")

    await db.delete(comment)
    await db.commit()


@router.post("/{post_id}/comments/{comment_id}/replies", response_model=CommentResponse)
async def create_reply(post_id: int, comment_id: int, reply: CommentCreate, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Comment).where(models.Comment.id == comment_id))
    parent_comment = result.scalars().first()

    if not parent_comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="parent comment not found")

    new_reply = models.Comment(content=reply.content, user_id=current_user.id, post_id=post_id, parent_id=comment_id)
    db.add(new_reply)
    await db.commit()
    await db.refresh(new_reply, attribute_names=["user"])
    return new_reply

