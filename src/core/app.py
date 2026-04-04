from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
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
    exist_user_query = await db.execute(select(User).where(User.id == id).options(selectinload(User.subscriptions), selectinload(User.subscribers)))
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


@app.post("/user/sub/{id_user}/{id_author}", response_model=UserResponse)
async def user_subscribe(id_user:int, id_author:int, db:AsyncSession = Depends(get_db)):
    user_query = await db.execute(select(User).where(User.id == id_user))
    author_query = await db.execute(select(User).where(User.id == id_author))
    exist_user = user_query.scalars().first()
    exist_author = author_query.scalars().first()
    if not exist_user:
        raise HTTPException(
            detail="Not found user with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    if not exist_author:
        raise HTTPException(
            detail="Not found author with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    subscription_check = await db.execute(
        select(user_subscriptions).where(
            and_(
                user_subscriptions.c.subscriber_id == id_user,
                user_subscriptions.c.subscribed_to_id == id_author
            )
        )
    )
    if subscription_check.first():
        raise HTTPException(
            detail="Bad request, user already subscribed to this author",
            status_code=status.HTTP_400_BAD_REQUEST
        )    
    from sqlalchemy import insert
    stmt = insert(user_subscriptions).values(
        subscriber_id=id_user,
        subscribed_to_id=id_author
    )
    try:
        await db.execute(stmt)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return exist_user
           

@app.delete("/user/sub/{id_user}/{id_author}", response_model=UserCreate)
async def delete_subscribe(id_user:int, id_author:int, db:AsyncSession = Depends(get_db)):
    user_query = await db.execute(
        select(User)
        .where(User.id == id_user)
        .options(selectinload(User.subscribers))
    )
    exist_user = user_query.scalars().first()
    author_query = await db.execute(
        select(User)
        .where(User.id == id_author)
        .options(selectinload(User.subscribers))
    )
    exist_author = author_query.scalars().first()
    if not exist_user:
        raise HTTPException(
            detail="Not found user with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    if not exist_author:
        raise HTTPException(
            detail="Not found author with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    if not (exist_user in exist_author.subscribers):
        raise HTTPException(detail="Bad request, user already subscribed to this author",status_code=status.HTTP_400_BAD_REQUEST)
    exist_author.subscribers.remove(exist_user)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return exist_user


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


@app.post("/post/rating/up/{post_id}/{user_id}", response_model=PostResponse)
async def post_rating_up(post_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    post_query = await db.execute(select(Post).where(Post.id == post_id))
    post = post_query.scalars().first()    
    if not post:
        raise HTTPException(
            detail="Not found post with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )   
    rating_up = list(post.rating_up) if post.rating_up else []
    rating_down = list(post.rating_down) if post.rating_down else []
    if user_id in rating_up:
        raise HTTPException(
            detail="Post already rated up", 
            status_code=status.HTTP_400_BAD_REQUEST
        )
    if user_id in rating_down:
        rating_down.remove(user_id)
    rating_up.append(user_id)
    post.rating_up = rating_up
    post.rating_down = rating_down   
    try:
        await db.commit()
        await db.refresh(post)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong: {e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
    return post


@app.post("/post/rating/down/{post_id}/{user_id}", response_model=PostResponse)
async def post_rating_down(post_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    post_query = await db.execute(select(Post).where(Post.id == post_id))
    post = post_query.scalars().first()    
    if not post:
        raise HTTPException(
            detail="Not found post with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )   
    rating_up = list(post.rating_up) if post.rating_up else []
    rating_down = list(post.rating_down) if post.rating_down else []
    if user_id in rating_down:
        raise HTTPException(
            detail="Post already rated down", 
            status_code=status.HTTP_400_BAD_REQUEST
        )
    if user_id in rating_up:
        rating_up.remove(user_id)
    rating_down.append(user_id)    
    post.rating_up = rating_up
    post.rating_down = rating_down   
    try:
        await db.commit()
        await db.refresh(post)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong: {e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
    return post


@app.delete("/post/rating/{post_id}/{user_id}")
async def delete_rating(post_id:int, user_id:int, db:AsyncSession = Depends(get_db)):
    post_query = await db.execute(select(Post).where(Post.id == post_id))
    post = post_query.scalars().first()
    if not post:
        raise HTTPException(
            detail="Not found post with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    rating_up = list(post.rating_up) if post.rating_up else []
    rating_down = list(post.rating_down) if post.rating_down else []
    if user_id not in rating_up and user_id not in rating_down:
        raise HTTPException(
            detail="Bad request, user not rated this post", 
            status_code=status.HTTP_400_BAD_REQUEST
        )
    if user_id in rating_up:
        rating_up.remove(user_id)
    if user_id in rating_down:
        rating_down.remove(user_id)
    post.rating_up = rating_up
    post.rating_down = rating_down
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
    return None