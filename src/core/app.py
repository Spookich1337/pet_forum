from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()    
    yield   
    await engine.dispose()


@app.get("/")
async def root():
    return {"test1":"connect"}


@app.get("/user/{id}", response_model=UserResponse)
async def get_user(id:int, db: AsyncSession = Depends(get_db)):
    exist_user_query = await db.execute(select(User).where(User.id == id))
    exist_user = exist_user_query.scalars().first()
    if not exist_user:
        raise HTTPException(
            detail="Not found user with this ID",
            status_code=status.HTTP_404_NOT_FOUND
        )
    return exist_user


@app.post("/user", response_model=UserResponse)
async def post_user(data:UserCreate, db:AsyncSession = Depends(get_db)):
    exist_user_query = await db.execute(select(User).where(User.name == data.name or User.email == data.email))
    exist_user = exist_user_query.scalars().first()
    if exist_user:
        raise HTTPException(
            detail="This user already exist",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    new_user = User(**data.model_dump())
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
    return new_user


@app.put("/user/{id}", response_model=UserResponse)
async def put_user(id:int, data:UserUpdate, db:AsyncSession = Depends(get_db)):
    exist_user_query = await db.execute(select(User).where(User.id == id))
    exist_user = exist_user_query.scalars().first()
    if not exist_user:
        raise HTTPException(
            detail="Not found user with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )   
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(exist_user, key, value)
    try:
        await db.commit()
        await db.refresh(exist_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
    return exist_user


@app.delete("/user/{id}")
async def delete_user(id:int, db:AsyncSession = Depends(get_db)):
    exist_user_query = await db.execute(select(User).where(User.id == id))
    exist_user = exist_user_query.scalars().first()
    if not exist_user:
        raise HTTPException(
            detail="Not found user with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    await db.delete(exist_user)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
    return None   


@app.get("/posts", response_model=PostList)
async def get_all_posts(db:AsyncSession = Depends(get_db)):
    posts_query = await db.execute(select(Post))
    posts = posts_query.scalars().all()
    if not posts:
        raise HTTPException(
            detail="Not found any available posts", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    count = len(posts)
    return {
        "count":count,
        "posts":posts
        }


@app.get("/post/{id}", response_model=PostResponse)
async def get_post(id:int, db:AsyncSession = Depends(get_db)):
    exist_post_query = await db.execute(select(Post).where(Post.id == id))
    exist_post = exist_post_query.scalars().first()
    if not exist_post:
        raise HTTPException(
            detail="Not found post with this ID",
            status_code=status.HTTP_404_NOT_FOUND
        )
    return exist_post


@app.post("/post", response_model=PostResponse)
async def post_post(data:PostCreate, db:AsyncSession = Depends(get_db)):
    exist_post_query = await db.execute(select(Post).where(Post.title == data.title))
    exist_post = exist_post_query.scalars().first()
    if exist_post:
        raise HTTPException(
            detail="This post already exist",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    new_post = Post(**data.model_dump())
    db.add(new_post)
    try:
        await db.commit()
        await db.refresh(new_post)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
    return new_post


@app.put("/post/{id}", response_model=PostResponse)
async def put_post(id:int, data:PostUpdate, db:AsyncSession = Depends(get_db)):
    exist_post_query = await db.execute(select(Post).where(Post.id == id))
    exist_post = exist_post_query.scalars().first()
    if not exist_post:
        raise HTTPException(
            detail="Not found post with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )   
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(exist_post, key, value)
    try:
        await db.commit()
        await db.refresh(exist_post)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )    
    return exist_post


@app.delete("/post/{id}")
async def delete_post(id:int, db:AsyncSession = Depends(get_db)):
    exist_post_query = await db.execute(select(Post).where(Post.id == id))
    exist_post = exist_post_query.scalars().first()
    if not exist_post:
        raise HTTPException(
            detail="Not found post with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    await db.delete(exist_post)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
    return None