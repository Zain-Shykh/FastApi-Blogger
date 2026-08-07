from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from auth import CurrentAdminUser
from schemas import PostResponse, UserPublic  # Ensure these are correctly imported from your schemas file
from imageutils import delete_post_thumbnail

router = APIRouter(prefix="/admin", tags=["Admin Management"])


# ==========================================
# 1. PLATFORM METRICS & ENGAGEMENT STATS
# ==========================================

@router.get("/metrics", status_code=status.HTTP_200_OK)
async def get_platform_metrics(
    current_admin: CurrentAdminUser, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get core platform counts (Users, Admins, Posts, Comments, Likes).
    """
    # Execute count queries concurrently or back-to-back using scalar aggregates
    user_count = (await db.execute(select(func.count(models.User.id)))).scalar() or 0
    admin_count = (await db.execute(select(func.count(models.User.id)).where(models.User.is_admin == True))).scalar() or 0
    post_count = (await db.execute(select(func.count(models.Post.id)))).scalar() or 0
    comment_count = (await db.execute(select(func.count(models.Comment.id)))).scalar() or 0
    like_count = (await db.execute(select(func.count(models.Like.id)))).scalar() or 0

    return {
        "total_users": user_count,
        "total_admins": admin_count,
        "total_posts": post_count,
        "total_comments": comment_count,
        "total_likes": like_count
    }


@router.get("/engagement/top-posts", response_model=list[dict])
async def get_top_posts(
    current_admin: CurrentAdminUser, 
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 5
):
    """
    Get top engaged posts ranked by likes count.
    """
    query = (
        select(
            models.Post.id,
            models.Post.title,
            models.Post.date_posted,
            func.count(models.Like.id).label("likes_count")
        )
        .outerjoin(models.Like, models.Post.id == models.Like.post_id)
        .group_by(models.Post.id)
        .order_by(func.count(models.Like.id).desc())
        .limit(limit)
    )
    
    result = await db.execute(query)
    top_posts = result.all()
    
    return [
        {
            "id": row.id,
            "title": row.title,
            "date_posted": row.date_posted,
            "likes_count": row.likes_count
        } for row in top_posts
    ]


# ==========================================
# 2. USER MODERATION & PRIVILEGES
# ==========================================

@router.patch("/users/{user_id}/role", response_model=UserPublic)
async def toggle_user_admin_privilege(
    user_id: int,
    current_admin: CurrentAdminUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Promote or demote a target platform user.
    An admin cannot revoke their own privilege through this endpoint.
    """
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="You cannot modify your own administrative status."
        )

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Invert the flag state
    user.is_admin = not user.is_admin
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def administrative_ban_user(
    user_id: int,
    current_admin: CurrentAdminUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Administratively ban/wipes a user completely from the platform.
    Cascades will delete all associated posts, tokens, likes, and comments automatically.
    """
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="You cannot ban your own administrative account."
        )

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Wipe records via your model definitions cascade="all, delete-orphan"
    await db.delete(user)
    await db.commit()
    return None


# ==========================================
# 3. CONTENT MODERATION (POSTS & COMMENTS)
# ==========================================

@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def administrative_delete_post(
    post_id: int,
    current_admin: CurrentAdminUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Moderation sweep to delete any post from the platform.
    Ensures S3 thumbnail references are completely removed.
    """
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    old_thumbnail = post.image_file

    await db.delete(post)
    await db.commit()

    # Clear cloud assets asynchronously if they exist
    if old_thumbnail:
        await delete_post_thumbnail(old_thumbnail)

    return None


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def administrative_delete_comment(
    comment_id: int,
    current_admin: CurrentAdminUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Moderation sweep to remove any abusive comment or nested reply tree branch.
    """
    result = await db.execute(select(models.Comment).where(models.Comment.id == comment_id))
    comment = result.scalars().first()

    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    await db.delete(comment)
    await db.commit()
    return None