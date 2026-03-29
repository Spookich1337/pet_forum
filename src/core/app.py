from fastapi import FastAPI, Depends, HTTPException, status
from .database.DBconfig import engine, get_db 
from .database.DBmodels import *
from sqlalchemy.orm import Session
from .schemas.schem import *


app = FastAPI()


Base.metadata.create_all(bind=engine)


@app.get("/post/{id}", response_model=Post)
def get_post(id:int, db:Session = Depends(get_db)):
    exist_post = db.query(Post).filter(Post.id == id).first()
    if not exist_post:
        raise HTTPException(
            detail="Not found post with this ID",
            status_code=status.HTTP_404_NOT_FOUND
        )
    return exist_post


@app.post("/post", response_model=Post)
def post_post(data:PostCreate, db:Session = Depends(get_db)):
    exist_post = db.query(Post).filter(Post.title == data.title).first()
    if exist_post:
        raise HTTPException(
            detail="This post already exist",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    new_post = Post(**data.model_dump())
    db.add(new_post)
    try:
        db.commit()
        db.refresh(new_post)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong: {e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return new_post