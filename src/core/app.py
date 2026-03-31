from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from src.database.DBconfig import engine, get_db 
from src.database.DBmodels import *
from src.schemas.schem import *


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return FileResponse("src/template/index.html")


@app.get("/user/{id}", response_model=UserResponse)
def get_user(id:int, db:Session = Depends(get_db)):
    exist_user = db.query(User).filter(User.id == id).first()
    if not exist_user:
        raise HTTPException(
            detail="Not found user with this ID",
            status_code=status.HTTP_404_NOT_FOUND
        )
    return exist_user


@app.post("/user", response_model=UserResponse)
def post_user(data:UserCreate, db:Session = Depends(get_db)):
    exist_user = db.query(User).filter((User.name == data.name) | (User.email == data.email)).first()
    if exist_user:
        raise HTTPException(
            detail="This user already exist",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    new_user = User(**data.model_dump())
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong: {e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return new_user


@app.put("/user/{id}", response_model=UserResponse)
def put_user(id:int, data:UserUpdate, db:Session = Depends(get_db)):
    exist_user = db.query(User).filter(User.id == id).first()
    if not exist_user:
        raise HTTPException(
            detail="Not found user with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )   
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(exist_user, key, value)
    try:
        db.commit()
        db.refresh(exist_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )    
    return exist_user


@app.delete("/user/{id}")
def delete_user(id:int, db:Session = Depends(get_db)):
    exist_user = db.query(User).filter(User.id == id).first()
    if not exist_user:
        raise HTTPException(
            detail="Not found user with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    db.delete(exist_user)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
    return None   


@app.get("/posts", response_model=PostList)
def get_all_posts(db:Session = Depends(get_db)):
    posts = db.query(Post).all()
    if not posts:
        raise HTTPException(
            detail="Not found any available posts", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    count = db.query(Post).count()
    return {
        "count":count,
        "posts":posts
        }

@app.get("/post/{id}", response_model=PostResponse)
def get_post(id:int, db:Session = Depends(get_db)):
    exist_post = db.query(Post).filter(Post.id == id).first()
    if not exist_post:
        raise HTTPException(
            detail="Not found post with this ID",
            status_code=status.HTTP_404_NOT_FOUND
        )
    return exist_post


@app.post("/post", response_model=PostResponse)
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


@app.put("/post/{id}", response_model=PostResponse)
def put_post(id:int, data:PostUpdate, db:Session = Depends(get_db)):
    exist_post = db.query(Post).filter(Post.id == id).first()
    if not exist_post:
        raise HTTPException(
            detail="Not found post with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )   
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(exist_post, key, value)
    try:
        db.commit()
        db.refresh(exist_post)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )    
    return exist_post


@app.delete("/post/{id}")
def delete_post(id:int, db:Session = Depends(get_db)):
    exist_post = db.query(Post).filter(Post.id == id).first()
    if not exist_post:
        raise HTTPException(
            detail="Not found post with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    db.delete(exist_post)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
    return None