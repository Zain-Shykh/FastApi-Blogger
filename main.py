from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
app = FastAPI()


posts = [
    {
        id: 1,
        "title": "title of post 1",
        "content": "content of post 1",
    },
    {
        id: 2,
        "title": "title of post 2",
        "content": "content of post 2",
    }
]
@app.get("/")
def root():
    return "this is root "

@app.get("/posts")
def get_posts():
    return {"data": posts}

@app.get("/posts/{id}")
def get_post(id: int):
    for post in posts:
        if post["id"] == id:
            return {"post_detail": post}
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
    