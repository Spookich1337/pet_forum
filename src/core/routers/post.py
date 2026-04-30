import random
from fastapi import APIRouter, HTTPException, Depends, status

from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ...schemas.schem import PostCreate, PostResponse, PostUpdate, PostList
from ...database.DBconfig import get_db
from ...database.DBmodels import Post, User
from ...core.util.security import *


router = APIRouter(prefix="/posts", tags=["Posts api"])


@router.get("/recommendations", response_model=PostList)
async def get_post_recom(
    limit:int,    
    sub_limit:int,
    payload:dict = Depends(check_access_token),
    db: AsyncSession = Depends(get_db)
):
    user_query = await db.execute(
        select(User).
        where(User.id == int(payload.get("sub"))).
        options(selectinload(User.subscriptions))
    )

    user = user_query.scalars().first()

    if not user:
        raise HTTPException(
            detail="User not found",
            status_code=status.HTTP_404_NOT_FOUND            
        )
    
    subscribed_ids = [author.id for author in user.subscriptions]   
    final_posts = []

    if subscribed_ids:
        sub_posts_query = await db.execute(
            select(Post)
            .where(Post.author_id.in_(subscribed_ids))
            .order_by(func.random())
            .limit(sub_limit)
        )

        final_posts.extend(sub_posts_query.scalars().all())

    already_chosen_ids = [p.id for p in final_posts]

    rand_posts_query = await db.execute(
        select(Post)
        .where(
            and_(
                Post.id.not_in(already_chosen_ids) if already_chosen_ids else True,
                Post.author_id.not_in(subscribed_ids) if subscribed_ids else True
            )
        )
        .order_by(func.random())
        .limit(limit - len(final_posts))
    )

    final_posts.extend(rand_posts_query.scalars().all())

    random.shuffle(final_posts)

    return {
        "count": len(final_posts),
        "posts": final_posts
    }

@router.get("", response_model=PostList)
async def get_all_posts(
    size:int, 
    page:int,
    db:AsyncSession = Depends(get_db)
):
    posts_query = await db.execute(
        select(Post).
        order_by(Post.id).
        limit(size).
        offset((page-1)*size)
    )

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


@router.get("/{id}", response_model=PostResponse)
async def get_post(
    id:int, 
    db:AsyncSession = Depends(get_db)
):
    exist_post_query = await db.execute(
        select(Post).
        where(Post.id == id)
    )

    exist_post = exist_post_query.scalars().first()

    if not exist_post:
        raise HTTPException(
            detail="Not found post with this ID",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    return exist_post


@router.post("", response_model=PostResponse)
async def post_post(
    data:PostCreate, 
    payload:dict = Depends(check_access_token),
    db:AsyncSession = Depends(get_db)
):
    exist_post_query = await db.execute(
        select(Post).
        where(Post.title == data.title)
    )

    exist_post = exist_post_query.scalars().first()
    
    if exist_post:
        raise HTTPException(
            detail="This post already exist",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    post_data = data.model_dump()
    post_data["author_id"] = int(payload.get("sub"))
    new_post = Post(**post_data)

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


@router.put("", response_model=PostResponse)
async def put_post(
    id:int, 
    data:PostUpdate,
    payload:dict = Depends(check_access_token), 
    db:AsyncSession = Depends(get_db)
):
    exist_post_query = await db.execute(
        select(Post).
        where(Post.id == id)
    )

    exist_post = exist_post_query.scalars().first()

    if not exist_post:
        raise HTTPException(
            detail="Not found post with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )   
    
    if exist_post.author_id != int(payload.get("sub")):
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


@router.delete("")
async def delete_post(
    id:int, 
    payload:dict = Depends(check_access_token),
    db:AsyncSession = Depends(get_db)
):
    exist_post_query = await db.execute(
        select(Post).
        where(Post.id == id)
    )

    exist_post = exist_post_query.scalars().first()

    if not exist_post:
        raise HTTPException(
            detail="Not found post with this ID", 
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if exist_post.author_id != int(payload.get("sub")):
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


@router.post("/rate_up", response_model=PostResponse)
async def post_rating_up(
    post_id: int, 
    payload:dict = Depends(check_access_token),
    db: AsyncSession = Depends(get_db)
):
    post_query = await db.execute(
        select(Post).
        where(Post.id == post_id)
    )

    post = post_query.scalars().first()  

    user_id = int(payload.get("sub"))  

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


@router.post("/rate_down", response_model=PostResponse)
async def post_rating_down(
    post_id: int, 
    payload:dict = Depends(check_access_token),
    db: AsyncSession = Depends(get_db)
):
    post_query = await db.execute(
        select(Post).
        where(Post.id == post_id)
    )

    post = post_query.scalars().first()  

    user_id = int(payload.get("sub"))

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


@router.delete("/delete_rate")
async def delete_rating(
    post_id:int, 
    payload:dict = Depends(check_access_token),
    db:AsyncSession = Depends(get_db)
):
    post_query = await db.execute(
        select(Post).
        where(Post.id == post_id)
    )

    post = post_query.scalars().first()

    user_id = int(payload.get("sub"))

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