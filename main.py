from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from schemas import PostCreate, PostResponse
from datetime import datetime
app = FastAPI()


posts = [
    {
        "id": 1,
        "title": "title of post 1",
        "content": "content of post 1",
        "author": "John",
        "date_posted":str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    },
    {
        "id": 2,
        "title": "title of post 2",
        "content": "content of post 2",
        "author": "John",
        "date_posted":str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    }
]
@app.get("/")
def root():
    return "this is root "

@app.get("/posts", response_model=list[PostResponse])
def get_posts():
    return posts

@app.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post:PostCreate):
    print("hello")
    new_id = max(p["id"] for p in posts)+1 if posts else 1
    newpost = {
        "id": new_id,
        "title":post.title,
        "content":post.content,
        "author":post.author,
        "date_posted": str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    }
    posts.append(newpost)
    return newpost


@app.get("/posts/{id}", response_model=PostResponse)
def get_post(id: int):
    for post in posts:
        if post["id"] == id:
            return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} was not found")
    

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
