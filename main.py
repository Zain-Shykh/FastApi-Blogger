from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from schemas import PostCreate, PostResponse, UserResponse, UserCreate, PostUpdate, UserUpdate
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import Session
import models
from database import get_db, engine, Base


Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")


@app.get("/")
def root():
    return "this is root "

@app.get("/posts", response_model=list[PostResponse])
def get_posts(db:Annotated[Session,Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts

@app.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post:PostCreate, db:Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user with the provided user_id does not exist")
    new_post = models.Post(
        title = post.title,
        content = post.content,
        user_id = post.user_id
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user:UserCreate, db:Annotated[Session, Depends(get_db)]):
    result = db.execute(select (models.User).where (models.User.username == user.username),)

    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username already exists")
    
    result = db.execute(select (models.User).where (models.User.email == user.email),)

    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists")
    
    new_user = models.User(
        username = user.username,
        email = user.email
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@app.patch("/users/{id}", response_model=UserResponse)
def update_user_partial(id: int, newUserData:UserUpdate, db:Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with id: {id} was not found")

    if newUserData.username and newUserData.username != user.username:
        result = db.execute(select(models.User).where(models.User.username == newUserData.username))
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username already exists")
        
    if newUserData.email and newUserData.email != user.email:
        result = db.execute(select(models.User).where(models.User.email == newUserData.email))
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists")

    newData = newUserData.model_dump(exclude_unset=True)
    for field, value in newData.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(userid:int, db:Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == userid),)

    user = result.scalars().first()

    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user was not found")


@app.delete("/users/{userid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(id:int, db:Annotated[Session, get_db]):
    result = db.execute(select(models.User).where(models.User.id == id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    
    db.delete(user)
    db.commit()

    

@app.get("/users/{userid}/posts", response_model=list[PostResponse])
def get_user_posts(userid:int, db:Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == userid))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    
    result = db.execute(select (models.Post). where(models.Post.user_id == userid))
    posts = result.scalars().all()
    return posts

@app.get("/posts/{id}", response_model=PostResponse)
def get_post(id: int, db:Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == id))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} was not found")
    

@app.put("/posts/{id}", response_model=PostResponse)
def update_post_full(id: int, newPost:PostCreate, db:Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} was not found")

    if newPost.user_id == post.user_id:
        result = db.execute(select(models.User).where(models.User.id == post.user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user was not found")
        
        post.title = newPost.title
        post.content = newPost.content

        db.commit()
        db.refresh(post)
        return post
    

@app.patch("/posts/{id}", response_model=PostResponse)
def update_post_partial(id: int, newPost:PostUpdate, db:Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} was not found")

    newData = newPost.model_dump(exclude_unset=True)
    for field, value in newData.items():
        setattr(post, field, value)
    
    db.commit()
    db.refresh(post)
    return post
    
@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id:int, db:Annotated[Session,get_db]):
    result = db.execute(select(models.Post).where(models.Post.id == id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="post not found")

    db.delete(post)
    db.commit()
        

@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )
